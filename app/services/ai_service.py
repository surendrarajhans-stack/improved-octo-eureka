from datetime import date, timedelta
from statistics import mean

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.billing import Invoice, Payment
from app.models.clinical import IPDAdmission
from app.models.hospital import Bed
from app.models.pharmacy import DrugInteraction, Medicine, PharmacyDispensingItem


class AIService:
    ICD_MAP = {
        "diabetes": [{"code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "confidence": 0.92}],
        "hypertension": [{"code": "I10", "description": "Essential primary hypertension", "confidence": 0.91}],
        "fever": [{"code": "R50.9", "description": "Fever, unspecified", "confidence": 0.85}],
        "asthma": [{"code": "J45.909", "description": "Unspecified asthma, uncomplicated", "confidence": 0.88}],
        "fracture": [{"code": "T14.2", "description": "Fracture of unspecified body region", "confidence": 0.8}],
    }

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _linear_regression(values: list[float], steps_ahead: int) -> tuple[list[float], float]:
        if not values:
            return [0.0] * steps_ahead, 0.0
        n = len(values)
        xs = list(range(n))
        x_mean = mean(xs)
        y_mean = mean(values)
        denom = sum((x - x_mean) ** 2 for x in xs) or 1
        slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values, strict=False)) / denom
        intercept = y_mean - slope * x_mean
        forecast = [max(0.0, intercept + slope * (n + i)) for i in range(steps_ahead)]
        variance = mean([(y - (intercept + slope * x)) ** 2 for x, y in zip(xs, values, strict=False)]) if n > 1 else 0.0
        return forecast, variance ** 0.5

    def predict_revenue(self, hospital_id: int, days_ahead: int = 7) -> dict:
        start_date = date.today() - timedelta(days=29)
        rows = (
            self.db.query(func.date(Payment.payment_date), func.coalesce(func.sum(Payment.amount), 0.0))
            .join(Invoice, Invoice.id == Payment.invoice_id)
            .filter(Invoice.hospital_id == hospital_id, Payment.payment_date >= start_date)
            .group_by(func.date(Payment.payment_date))
            .all()
        )
        data_map = {str(day): float(total) for day, total in rows}
        values = [data_map.get(str(start_date + timedelta(days=i)), 0.0) for i in range(30)]
        forecast, spread = self._linear_regression(values, days_ahead)
        labels = [str(date.today() + timedelta(days=i + 1)) for i in range(days_ahead)]
        return {
            "historical": [{"date": str(start_date + timedelta(days=i)), "value": values[i]} for i in range(30)],
            "forecast": [{"date": labels[i], "value": round(forecast[i], 2)} for i in range(days_ahead)],
            "confidence_interval": {"low": round(max(sum(forecast) - spread, 0.0), 2), "high": round(sum(forecast) + spread, 2)},
        }

    def predict_patient_load(self, hospital_id: int, date: date) -> dict:
        rows = (
            self.db.query(Appointment.appointment_date, func.count(Appointment.id))
            .filter(Appointment.hospital_id == hospital_id, Appointment.appointment_date >= date - timedelta(days=56))
            .group_by(Appointment.appointment_date)
            .all()
        )
        weekday_values = [count for day, count in rows if day.weekday() == date.weekday()]
        avg = round(mean(weekday_values), 2) if weekday_values else 0
        return {"date": str(date), "predicted_count": avg, "range": [max(avg - 3, 0), avg + 3], "basis_days": len(weekday_values)}

    def predict_bed_occupancy(self, hospital_id: int) -> dict:
        total = self.db.query(func.count(Bed.id)).scalar() or 0
        occupied = (
            self.db.query(func.count(IPDAdmission.id))
            .filter(IPDAdmission.hospital_id == hospital_id, IPDAdmission.status == "ADMITTED")
            .scalar()
            or 0
        )
        rate = round((occupied / total) * 100, 2) if total else 0.0
        return {"occupied": occupied, "total": total, "occupancy_rate": rate, "prediction_next_24h": min(100.0, rate + 5)}

    def predict_medicine_demand(self, hospital_id: int) -> list[dict]:
        rows = (
            self.db.query(Medicine.name, func.coalesce(func.sum(PharmacyDispensingItem.quantity), 0))
            .join(PharmacyDispensingItem, PharmacyDispensingItem.medicine_id == Medicine.id, isouter=True)
            .filter(Medicine.hospital_id == hospital_id)
            .group_by(Medicine.id)
            .order_by(func.coalesce(func.sum(PharmacyDispensingItem.quantity), 0).desc())
            .limit(10)
            .all()
        )
        return [{"medicine": name, "monthly_demand": qty, "recommended_stock": int(qty * 1.5 + 10)} for name, qty in rows]

    def check_drug_interaction(self, medicine_ids: list[int]) -> list[dict]:
        if len(medicine_ids) < 2:
            return []
        interactions = (
            self.db.query(DrugInteraction)
            .filter(
                DrugInteraction.medicine1_id.in_(medicine_ids),
                DrugInteraction.medicine2_id.in_(medicine_ids),
            )
            .all()
        )
        results = []
        for interaction in interactions:
            if interaction.medicine1_id == interaction.medicine2_id:
                continue
            results.append(
                {
                    "medicine1_id": interaction.medicine1_id,
                    "medicine2_id": interaction.medicine2_id,
                    "severity": interaction.severity,
                    "description": interaction.description,
                    "clinical_effect": interaction.clinical_effect,
                }
            )
        return results

    def suggest_icd_codes(self, diagnosis_text: str) -> list[dict]:
        text = diagnosis_text.lower()
        matches = []
        for keyword, codes in self.ICD_MAP.items():
            if keyword in text:
                matches.extend(codes)
        return matches or [{"code": "R69", "description": "Illness, unspecified", "confidence": 0.4}]

    def get_dashboard_insights(self, hospital_id: int) -> list[dict]:
        insights = []
        revenue = self.predict_revenue(hospital_id, 3)
        patient_load = self.predict_patient_load(hospital_id, date.today() + timedelta(days=1))
        bed = self.predict_bed_occupancy(hospital_id)
        meds = self.predict_medicine_demand(hospital_id)
        if revenue["forecast"]:
            insights.append({"title": "Revenue Trend", "message": f"Next 3 days projected revenue is {sum(x['value'] for x in revenue['forecast']):.2f}.", "type": "info"})
        insights.append({"title": "Tomorrow OPD Load", "message": f"Expected appointments: {patient_load['predicted_count']}.", "type": "primary"})
        insights.append({"title": "Bed Occupancy", "message": f"Current bed occupancy is {bed['occupancy_rate']}%.", "type": "warning" if bed['occupancy_rate'] > 80 else "success"})
        if meds:
            insights.append({"title": "High Demand Medicine", "message": f"Keep extra stock of {meds[0]['medicine']}.", "type": "secondary"})
        insights.append({"title": "Follow-up Action", "message": "Review pending lab reports and unfinished consultations before end of day.", "type": "dark"})
        return insights[:7]

    def chat_response(self, message: str, context: dict = None) -> str:
        message_lower = message.lower()
        if "appointment" in message_lower:
            return "To book an appointment, open the Appointments module, choose a patient and doctor, then save the schedule."
        if "patient status" in message_lower or "admission" in message_lower:
            return "You can review patient progress from Patient Detail, OPD, or IPD modules depending on the visit type."
        if "medicine" in message_lower:
            return "Use the Pharmacy module to review stock, expiry alerts, and dispensing records before advising substitutions."
        if "revenue" in message_lower:
            return "Revenue insights are based on recent payments and invoice trends available on the AI dashboard."
        if "lab" in message_lower or "report" in message_lower:
            return "Laboratory and Radiology dashboards show pending worklists, results, and report-ready notifications."
        return "I can help with appointments, patient flow, billing insights, medicine safety, and ICD suggestions."
