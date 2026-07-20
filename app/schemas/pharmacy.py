from pydantic import BaseModel


class MedicineCreate(BaseModel):
    hospital_id: int
    name: str
    generic_name: str | None = None
    category: str | None = None
    form: str | None = None
    manufacturer: str | None = None
    unit: str | None = None
    reorder_level: int = 10
    description: str | None = None


class DispenseItemInput(BaseModel):
    medicine_id: int
    quantity: int
    instructions: str | None = None


class DispenseCreate(BaseModel):
    hospital_id: int
    patient_id: int
    prescription_id: int | None = None
    payment_mode: str = "CASH"
    items: list[DispenseItemInput]
    notes: str | None = None


class DrugInteractionRequest(BaseModel):
    medicine_ids: list[int]
