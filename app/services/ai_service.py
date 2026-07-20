"""Simple rule-based AI service for HMS predictive features."""

DIAGNOSIS_KEYWORD_MAP = {
    "fever": ["Malaria", "Typhoid", "Influenza", "COVID-19", "Dengue"],
    "cough": ["Pneumonia", "Tuberculosis", "Bronchitis", "Asthma", "COVID-19"],
    "chest pain": ["Angina", "Myocardial Infarction", "Pleuritis", "GERD", "Costochondritis"],
    "headache": ["Migraine", "Tension Headache", "Hypertension", "Meningitis", "Cluster Headache"],
    "abdominal pain": ["Appendicitis", "Gastritis", "IBS", "Cholecystitis", "Pancreatitis"],
    "shortness of breath": ["Asthma", "COPD", "Heart Failure", "Pulmonary Embolism", "Anemia"],
    "dizziness": ["Vertigo", "Hypotension", "Anemia", "Arrhythmia", "Dehydration"],
    "nausea": ["Gastroenteritis", "GERD", "Pregnancy", "Migraine", "Food Poisoning"],
    "fatigue": ["Anemia", "Diabetes", "Hypothyroidism", "Depression", "Chronic Fatigue Syndrome"],
    "back pain": ["Muscle Strain", "Herniated Disc", "Sciatica", "Kidney Stone", "Spondylitis"],
    "joint pain": ["Arthritis", "Gout", "Lupus", "Lyme Disease", "Fibromyalgia"],
    "rash": ["Eczema", "Psoriasis", "Allergic Reaction", "Chickenpox", "Measles"],
    "urinary": ["UTI", "Kidney Stone", "Prostatitis", "Overactive Bladder", "Cystitis"],
    "diabetes": ["Type 2 Diabetes", "Type 1 Diabetes", "Pre-diabetes", "Gestational Diabetes"],
    "hypertension": ["Essential Hypertension", "Secondary Hypertension", "White Coat Hypertension"],
}


def predict_readmission_risk(
    patient_age: int, diagnosis: str, previous_admissions: int
) -> dict:
    """Rule-based readmission risk prediction."""
    score = 0

    # Age factor
    if patient_age >= 75:
        score += 30
    elif patient_age >= 65:
        score += 20
    elif patient_age >= 55:
        score += 10
    elif patient_age < 18:
        score += 10

    # Previous admissions factor
    if previous_admissions >= 3:
        score += 35
    elif previous_admissions == 2:
        score += 25
    elif previous_admissions == 1:
        score += 15

    # Diagnosis-based risk
    high_risk_diagnoses = [
        "heart failure",
        "copd",
        "pneumonia",
        "sepsis",
        "stroke",
        "diabetes",
        "renal failure",
        "cancer",
        "myocardial",
    ]
    medium_risk_diagnoses = [
        "hypertension",
        "asthma",
        "anemia",
        "arrhythmia",
        "fracture",
    ]

    diagnosis_lower = diagnosis.lower()
    for dx in high_risk_diagnoses:
        if dx in diagnosis_lower:
            score += 25
            break
    else:
        for dx in medium_risk_diagnoses:
            if dx in diagnosis_lower:
                score += 15
                break

    score = min(score, 100)

    if score >= 60:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "factors": {
            "age_factor": patient_age,
            "previous_admissions": previous_admissions,
            "diagnosis": diagnosis,
        },
        "recommendations": _get_recommendations(risk_level),
    }


def _get_recommendations(risk_level: str) -> list[str]:
    if risk_level == "HIGH":
        return [
            "Schedule follow-up within 7 days",
            "Ensure medication reconciliation",
            "Arrange home health visit",
            "Connect with care coordinator",
            "Patient education on warning signs",
        ]
    elif risk_level == "MEDIUM":
        return [
            "Schedule follow-up within 14 days",
            "Provide detailed discharge instructions",
            "Confirm medication understanding",
        ]
    else:
        return [
            "Schedule routine follow-up",
            "Provide standard discharge instructions",
        ]


def suggest_diagnosis(symptoms: list[str]) -> list[dict]:
    """Keyword-based diagnosis suggestion."""
    diagnoses: dict[str, int] = {}

    for symptom in symptoms:
        symptom_lower = symptom.lower().strip()
        for keyword, dx_list in DIAGNOSIS_KEYWORD_MAP.items():
            if keyword in symptom_lower or symptom_lower in keyword:
                for dx in dx_list:
                    diagnoses[dx] = diagnoses.get(dx, 0) + 1

    # Sort by frequency
    sorted_diagnoses = sorted(diagnoses.items(), key=lambda x: x[1], reverse=True)

    return [
        {"diagnosis": dx, "confidence_score": min(count * 20, 95), "matches": count}
        for dx, count in sorted_diagnoses[:10]
    ]


def forecast_bed_occupancy(historical_data: list[float], forecast_days: int = 7) -> dict:
    """Simple moving average forecast for bed occupancy."""
    if not historical_data:
        return {"forecast": [], "average": 0, "trend": "STABLE"}

    window = min(7, len(historical_data))
    recent = historical_data[-window:]
    moving_avg = sum(recent) / len(recent)

    # Simple trend detection
    if len(historical_data) >= 2:
        trend_value = historical_data[-1] - historical_data[0]
        if trend_value > 5:
            trend = "INCREASING"
        elif trend_value < -5:
            trend = "DECREASING"
        else:
            trend = "STABLE"
    else:
        trend = "STABLE"

    # Generate forecast with slight variation
    forecast = []
    for i in range(forecast_days):
        if trend == "INCREASING":
            projected = moving_avg + (i + 1) * 0.5
        elif trend == "DECREASING":
            projected = moving_avg - (i + 1) * 0.5
        else:
            projected = moving_avg

        forecast.append(
            {
                "day": i + 1,
                "projected_occupancy": round(min(max(projected, 0), 100), 2),
            }
        )

    return {
        "forecast": forecast,
        "moving_average": round(moving_avg, 2),
        "trend": trend,
        "data_points_used": len(historical_data),
    }
