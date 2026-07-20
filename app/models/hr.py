from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time

from app.database import Base
from app.models.base import TimestampMixin


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_code = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    designation = Column(String(100), nullable=True)
    employment_type = Column(String(50), nullable=True)
    join_date = Column(Date, nullable=True)
    salary = Column(Float, default=0.0)
    bank_account = Column(String(100), nullable=True)
    bank_name = Column(String(100), nullable=True)
    ifsc_code = Column(String(50), nullable=True)
    pan_number = Column(String(20), nullable=True)
    aadhar_number = Column(String(20), nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    photo = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)


class Attendance(TimestampMixin, Base):
    __tablename__ = "attendance"

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)
    total_hours = Column(Float, default=0.0)
    status = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)


class Leave(TimestampMixin, Base):
    __tablename__ = "leaves"

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Float, default=1.0)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="PENDING")
    applied_on = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_on = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class Payroll(TimestampMixin, Base):
    __tablename__ = "payroll"

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, default=0.0)
    allowances = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    gross_salary = Column(Float, default=0.0)
    tax_deducted = Column(Float, default=0.0)
    pf_deducted = Column(Float, default=0.0)
    net_salary = Column(Float, default=0.0)
    status = Column(String(20), default="PENDING")
    processed_on = Column(DateTime, nullable=True)
    paid_on = Column(DateTime, nullable=True)


class Recruitment(TimestampMixin, Base):
    __tablename__ = "recruitments"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    position = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    vacancies = Column(Integer, default=1)
    status = Column(String(20), default="OPEN")
    posted_date = Column(Date, nullable=True)
    closing_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)


class JobApplication(TimestampMixin, Base):
    __tablename__ = "job_applications"

    recruitment_id = Column(Integer, ForeignKey("recruitments.id"), nullable=False)
    applicant_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    resume_path = Column(String(255), nullable=True)
    experience_years = Column(Float, default=0.0)
    status = Column(String(20), default="APPLIED")
    applied_on = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
