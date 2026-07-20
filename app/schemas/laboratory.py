from pydantic import BaseModel


class LabOrderCreate(BaseModel):
    hospital_id: int
    patient_id: int
    doctor_id: int | None = None
    sample_type: str | None = None
    priority: str = "ROUTINE"
    test_ids: list[int]
    notes: str | None = None


class LabResultCreate(BaseModel):
    item_id: int
    result_value: str | None = None
    result_text: str | None = None
    is_abnormal: bool = False
    notes: str | None = None


class LabTestResponse(BaseModel):
    id: int
    test_name: str
    test_code: str
    category: str | None = None
    price: int
