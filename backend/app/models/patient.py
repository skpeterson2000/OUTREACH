"""Patient model for demographics and medical information."""
from datetime import datetime
from app import db


class Patient(db.Model):
    """Patient model for home care recipients."""
    
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    
    # Identifiers
    medical_record_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Demographics
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20))
    
    # Contact Information
    phone_primary = db.Column(db.String(20))
    phone_secondary = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Address
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(200))
    emergency_contact_relationship = db.Column(db.String(50))
    emergency_contact_phone = db.Column(db.String(20))
    
    # Medical Information
    primary_diagnosis = db.Column(db.Text)
    secondary_diagnoses = db.Column(db.Text)  # JSON or comma-separated
    allergies = db.Column(db.Text)
    code_status = db.Column(db.String(50))  # Full Code, DNR, DNI, etc.
    
    # Hospice Care (for patients receiving end-of-life care)
    is_hospice = db.Column(db.Boolean, default=False, index=True)
    hospice_agency = db.Column(db.String(200))  # External hospice agency if applicable
    hospice_nurse_name = db.Column(db.String(200))
    hospice_nurse_phone = db.Column(db.String(20))
    hospice_admission_date = db.Column(db.Date)
    hospice_primary_diagnosis = db.Column(db.String(200))  # Terminal diagnosis
    
    # Goals of Care / Advance Directives
    goals_of_care = db.Column(db.Text)  # "Comfort-focused", "Symptom management only"
    advance_directive_on_file = db.Column(db.Boolean, default=False)
    polst_on_file = db.Column(db.Boolean, default=False)  # Physician Orders for Life-Sustaining Treatment
    do_not_hospitalize = db.Column(db.Boolean, default=False)
    
    # Comfort Measures
    comfort_measures_only = db.Column(db.Boolean, default=False)
    pain_management_plan = db.Column(db.Text)
    spiritual_preferences = db.Column(db.Text)
    
    # Insurance
    insurance_primary = db.Column(db.String(100))
    insurance_primary_id = db.Column(db.String(100))
    insurance_secondary = db.Column(db.String(100))
    insurance_secondary_id = db.Column(db.String(100))
    
    # Physician
    primary_physician = db.Column(db.String(200))
    physician_phone = db.Column(db.String(20))
    physician_fax = db.Column(db.String(20))
    
    # Status
    admission_date = db.Column(db.Date)
    discharge_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, discharged, deceased
    
    # Special Considerations
    fall_risk = db.Column(db.Boolean, default=False)
    infection_precautions = db.Column(db.String(200))
    language_preference = db.Column(db.String(50))
    interpreter_needed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    facility = db.relationship('Facility', back_populates='patients')
    visits = db.relationship('Visit', back_populates='patient', lazy='dynamic', 
                            cascade='all, delete-orphan')
    medications = db.relationship('Medication', back_populates='patient', lazy='dynamic',
                                 cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', back_populates='patient', lazy='dynamic',
                                 cascade='all, delete-orphan')
    wounds = db.relationship('WoundAssessment', back_populates='patient', lazy='dynamic',
                            cascade='all, delete-orphan')
    # specialty_assessments = db.relationship('SpecialtyAssessment', back_populates='patient', 
    #                                        lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def age(self):
        """Calculate patient age."""
        today = datetime.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def full_name(self):
        """Get full name."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses."""
        data = {
            'id': self.id,
            'medical_record_number': self.medical_record_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat(),
            'age': self.age,
            'gender': self.gender,
            'status': self.status,
            'fall_risk': self.fall_risk,
            'is_hospice': self.is_hospice,
            'code_status': self.code_status,
            'comfort_measures_only': self.comfort_measures_only,
            'admission_date': self.admission_date.isoformat() if self.admission_date else None,
            'primary_diagnosis': self.primary_diagnosis,
            'secondary_diagnoses': self.secondary_diagnoses,
            'allergies': self.allergies,
            'created_at': self.created_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'phone_primary': self.phone_primary,
                'address_line1': self.address_line1,
                'city': self.city,
                'state': self.state,
                'zip_code': self.zip_code,
                'emergency_contact_name': self.emergency_contact_name,
                'emergency_contact_relationship': self.emergency_contact_relationship,
                'emergency_contact_phone': self.emergency_contact_phone
            })
        
        return data
    
    def __repr__(self):
        return f'<Patient {self.medical_record_number}: {self.full_name}>'
