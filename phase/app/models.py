from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
import json

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # License (Dr), Company (Insurer), Mobile (Patient)
    password = Column(String) # Simple password for prototype
    role = Column(String) # 'doctor', 'patient', 'insurer'

    # Role specific fields
    full_name = Column(String, nullable=True)
    patient_code = Column(String, unique=True, index=True, nullable=True)

    reports_as_doctor = relationship("Report", foreign_keys="Report.doctor_id", back_populates="doctor")
    reports_as_patient = relationship("Report", foreign_keys="Report.patient_id", back_populates="patient")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    
    clinical_note = Column(Text)
    requested_procedure = Column(String)
    payer = Column(String)
    
    # Engine outputs
    decision_status = Column(String)
    readiness_score = Column(Integer)
    audit_json = Column(Text) # Stored as JSON string
    created_at = Column(String, default=lambda: datetime.datetime.now().isoformat())

    patient = relationship("User", foreign_keys=[patient_id], back_populates="reports_as_patient")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="reports_as_doctor")

    def get_audit(self):
        return json.loads(self.audit_json) if self.audit_json else None
