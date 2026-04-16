from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
import json


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # Doctor: License No. | Insurer: Company Name | Patient: Mobile | Hospital: Reg No. | Pharma: Drug License No.
    username = Column(String, unique=True, index=True)
    password = Column(String)
    # 'doctor', 'patient', 'insurer', 'hospital', 'pharma'
    role = Column(String)

    # Shared fields
    full_name = Column(String, nullable=True)

    # Patient-specific
    patient_code = Column(String, unique=True, index=True, nullable=True)

    # Hospital/Pharma-specific
    organization_name = Column(String, nullable=True)  # Hospital name / Pharmacy name
    address = Column(String, nullable=True)

    # Relationships
    reports_as_doctor = relationship("Report", foreign_keys="Report.doctor_id", back_populates="doctor")
    reports_as_patient = relationship("Report", foreign_keys="Report.patient_id", back_populates="patient")
    medical_history = relationship("PatientMedicalHistory", back_populates="patient", uselist=False)
    hospital_submissions = relationship("HospitalSubmission", foreign_keys="HospitalSubmission.submitted_by_id", back_populates="submitted_by")
    received_summaries = relationship("PatientSummary", foreign_keys="PatientSummary.doctor_id", back_populates="doctor")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))

    clinical_note = Column(Text)
    requested_procedure = Column(String)
    payer = Column(String)
    image_data = Column(Text, nullable=True)

    # Engine outputs
    decision_status = Column(String, default="SUBMITTED")
    readiness_score = Column(Integer)
    audit_json = Column(Text)
    created_at = Column(String, default=lambda: datetime.datetime.now().isoformat())

    patient = relationship("User", foreign_keys=[patient_id], back_populates="reports_as_patient")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="reports_as_doctor")

    def get_audit(self):
        return json.loads(self.audit_json) if self.audit_json else None


class PatientMedicalHistory(Base):
    """Patient fills this once at first login. Hospital can view it via patient code."""
    __tablename__ = "patient_medical_history"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), unique=True)

    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    age = Column(Integer, nullable=True)
    blood_group = Column(String, nullable=True)

    past_medical_history = Column(Text, nullable=True)   # e.g. Diabetes, Hypertension
    genetic_diseases = Column(Text, nullable=True)         # Family genetic conditions
    current_medications = Column(Text, nullable=True)      # Currently taking medicines
    allergies = Column(Text, nullable=True)                # Drug / food allergies
    past_surgeries = Column(Text, nullable=True)           # Previous operations

    created_at = Column(String, default=lambda: datetime.datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.datetime.now().isoformat(),
                        onupdate=lambda: datetime.datetime.now().isoformat())

    patient = relationship("User", back_populates="medical_history")


class HospitalSubmission(Base):
    """Bills and Reports submitted by Hospital Management or Pharma accounts."""
    __tablename__ = "hospital_submissions"
    id = Column(Integer, primary_key=True, index=True)

    # Who submitted it
    submitted_by_id = Column(Integer, ForeignKey("users.id"))
    submitter_role = Column(String)   # 'hospital' | 'pharma'

    # Which patient
    patient_id = Column(Integer, ForeignKey("users.id"))

    # What was submitted
    submission_type = Column(String)  # 'bill' | 'report' | 'blood_report' | 'prescription'
    title = Column(String)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=True)           # For bills
    file_data = Column(Text, nullable=True)          # Base64 for report files/images
    patient_admitted = Column(Boolean, default=False)

    created_at = Column(String, default=lambda: datetime.datetime.now().isoformat())

    submitted_by = relationship("User", foreign_keys=[submitted_by_id], back_populates="hospital_submissions")
    patient = relationship("User", foreign_keys=[patient_id])


class PatientSummary(Base):
    """Medical history summary sent by hospital management to a doctor."""
    __tablename__ = "patient_summaries"
    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("users.id"))
    sent_by_id = Column(Integer, ForeignKey("users.id"))     # Hospital management user
    doctor_id = Column(Integer, ForeignKey("users.id"))      # Target doctor

    summary_text = Column(Text)
    patient_name = Column(String)
    patient_code = Column(String)

    created_at = Column(String, default=lambda: datetime.datetime.now().isoformat())

    patient = relationship("User", foreign_keys=[patient_id])
    sent_by = relationship("User", foreign_keys=[sent_by_id])
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="received_summaries")
