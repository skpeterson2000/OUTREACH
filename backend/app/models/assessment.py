"""Visit and assessment models."""
from datetime import datetime
from app import db


class Visit(db.Model):
    """Patient visit record."""
    
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    nurse_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Visit Details
    visit_type = db.Column(db.String(100))  # skilled nursing, assessment, medication management
    scheduled_date = db.Column(db.DateTime)
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    
    # Visit Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    
    # Documentation
    chief_complaint = db.Column(db.Text)
    subjective = db.Column(db.Text)  # patient's report
    objective = db.Column(db.Text)  # nurse's observations
    assessment_summary = db.Column(db.Text)  # clinical assessment
    plan = db.Column(db.Text)  # plan of care
    
    # Visit Notes
    visit_notes = db.Column(db.Text)
    patient_education_provided = db.Column(db.Text)
    
    # Billing
    billing_code = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer)
    
    # Signatures
    nurse_signature = db.Column(db.String(200))
    signature_date = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='visits')
    nurse = db.relationship('User', back_populates='visits')
    vital_signs = db.relationship('VitalSigns', back_populates='visit', 
                                  lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'nurse_id': self.nurse_id,
            'visit_type': self.visit_type,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'status': self.status,
            'chief_complaint': self.chief_complaint,
            'duration_minutes': self.duration_minutes,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Visit {self.id}: Patient {self.patient_id} on {self.scheduled_date}>'


class Assessment(db.Model):
    """General clinical assessment."""
    
    __tablename__ = 'assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    nurse_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'))
    
    # Assessment Type
    assessment_type = db.Column(db.String(100))  # admission, routine, focused, discharge
    
    # Systems Assessment
    cardiovascular = db.Column(db.Text)
    respiratory = db.Column(db.Text)
    gastrointestinal = db.Column(db.Text)
    genitourinary = db.Column(db.Text)
    musculoskeletal = db.Column(db.Text)
    neurological = db.Column(db.Text)
    integumentary = db.Column(db.Text)
    psychosocial = db.Column(db.Text)
    
    # Functional Status
    mobility = db.Column(db.String(100))
    adls_status = db.Column(db.Text)  # Activities of Daily Living
    
    # Pain Assessment
    pain_present = db.Column(db.Boolean, default=False)
    pain_location = db.Column(db.String(200))
    pain_scale = db.Column(db.Integer)  # 0-10
    pain_character = db.Column(db.String(200))  # sharp, dull, burning, etc.
    
    # Overall Assessment
    general_appearance = db.Column(db.Text)
    clinical_impression = db.Column(db.Text)
    
    # Timestamps
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='assessments')
    nurse = db.relationship('User', back_populates='assessments')
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'nurse_id': self.nurse_id,
            'assessment_type': self.assessment_type,
            'pain_present': self.pain_present,
            'pain_scale': self.pain_scale,
            'cardiovascular': self.cardiovascular,
            'respiratory': self.respiratory,
            'assessment_date': self.assessment_date.isoformat(),
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Assessment {self.id}: {self.assessment_type} for patient {self.patient_id}>'


class VitalSigns(db.Model):
    """Vital signs recording."""
    
    __tablename__ = 'vital_signs'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Vital Signs
    temperature = db.Column(db.Numeric(4, 1))  # Fahrenheit
    temperature_route = db.Column(db.String(20))  # oral, axillary, tympanic, temporal
    pulse = db.Column(db.Integer)  # beats per minute
    pulse_rhythm = db.Column(db.String(50))  # regular, irregular
    respiratory_rate = db.Column(db.Integer)  # breaths per minute
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    bp_position = db.Column(db.String(50))  # sitting, standing, lying
    bp_location = db.Column(db.String(50))  # left arm, right arm
    oxygen_saturation = db.Column(db.Integer)  # percentage
    oxygen_delivery = db.Column(db.String(100))  # room air, nasal cannula, etc.
    oxygen_flow_rate = db.Column(db.Numeric(4, 1))  # liters per minute
    
    # Additional Measurements
    weight_kg = db.Column(db.Numeric(6, 2))
    height_cm = db.Column(db.Numeric(6, 2))
    blood_glucose = db.Column(db.Integer)  # mg/dL
    pain_level = db.Column(db.Integer)  # 0-10 scale
    
    # Notes
    notes = db.Column(db.Text)
    
    # Timestamps
    recorded_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    visit = db.relationship('Visit', back_populates='vital_signs')
    recorder = db.relationship('User')
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'temperature': float(self.temperature) if self.temperature else None,
            'pulse': self.pulse,
            'respiratory_rate': self.respiratory_rate,
            'blood_pressure': f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}" if self.blood_pressure_systolic else None,
            'oxygen_saturation': self.oxygen_saturation,
            'pain_level': self.pain_level,
            'recorded_time': self.recorded_time.isoformat(),
            'recorded_by': self.recorded_by
        }
    
    def __repr__(self):
        return f'<VitalSigns {self.id} for patient {self.patient_id}>'
