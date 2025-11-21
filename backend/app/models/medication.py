"""Medication models for prescriptions and administration records."""
from datetime import datetime
from app import db


class Medication(db.Model):
    """Medication prescription record."""
    
    __tablename__ = 'medications'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    
    # Medication Details
    medication_name = db.Column(db.String(200), nullable=False)  # Drug name (brand or generic)
    name = db.Column(db.String(200))  # Alias for backward compatibility with existing code
    generic_name = db.Column(db.String(200))
    ndc_code = db.Column(db.String(20))  # National Drug Code
    drug_class = db.Column(db.String(100))  # Antibiotic, Anticoagulant, Antihypertensive, etc.
    
    # Formulary and insurance
    formulary_status = db.Column(db.String(50))  # Preferred, Non-preferred, Prior auth required
    
    # High-risk medication flags
    is_high_risk = db.Column(db.Boolean, default=False)  # Anticoagulants, insulin, opioids, etc.
    requires_monitoring = db.Column(db.Boolean, default=False)  # Labs, vital signs, etc.
    monitoring_parameters = db.Column(db.Text)  # "INR q3days", "BP daily", "Blood glucose AC/HS"
    
    # Dosage
    dose = db.Column(db.String(50), nullable=False)
    dose_unit = db.Column(db.String(20))  # mg, ml, units, etc.
    route = db.Column(db.String(50), nullable=False)  # PO, IV, SQ, IM, etc.
    frequency = db.Column(db.String(100), nullable=False)  # BID, TID, QID, PRN, etc.
    frequency_times_per_day = db.Column(db.Integer)  # Number of times per day
    
    # PRN (As Needed)
    is_prn = db.Column(db.Boolean, default=False)
    prn_indication = db.Column(db.String(200))  # "for pain", "for anxiety", etc.
    prn_reason_required = db.Column(db.Boolean, default=False)  # Must document reason when given
    
    # Schedule
    scheduled_times = db.Column(db.Text)  # JSON array of times
    time_of_day = db.Column(db.String(200))  # Comma-separated times (e.g., "08:00,18:00")
    
    # Instructions
    instructions = db.Column(db.Text)  # General instructions (backward compatibility)
    special_instructions = db.Column(db.Text)
    food_instructions = db.Column(db.String(200))  # "with food", "on empty stomach"
    
    # Prescription Details
    prescribing_physician = db.Column(db.String(200))
    prescriber = db.Column(db.String(200))  # Alias for prescribing_physician
    prescription_date = db.Column(db.Date)
    start_date = db.Column(db.Date, nullable=False)
    is_controlled_substance = db.Column(db.Boolean, default=False)  # DEA scheduled drugs
    end_date = db.Column(db.Date)
    
    # Clinical indication
    indication = db.Column(db.Text)  # What condition this treats
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, discontinued, completed
    discontinued_date = db.Column(db.Date)
    discontinued_reason = db.Column(db.Text)
    
    # Reconciliation tracking
    added_via_reconciliation_id = db.Column(db.Integer, db.ForeignKey('medication_reconciliations.id'))
    last_reconciliation_date = db.Column(db.Date)  # Last time this med was reviewed in reconciliation
    
    # Pharmacy
    pharmacy_name = db.Column(db.String(200))
    pharmacy_phone = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='medications')
    administrations = db.relationship('MedicationAdministration', back_populates='medication',
                                     lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'medication_name': self.medication_name,  # Explicit field name for data interchange
            'generic_name': self.generic_name,
            'dose': self.dose,
            'dose_unit': self.dose_unit,
            'route': self.route,
            'frequency': self.frequency,
            'is_prn': self.is_prn,
            'prn_indication': self.prn_indication,
            'special_instructions': self.special_instructions,
            'indication': self.indication,
            'prescriber': self.prescriber or self.prescribing_physician,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_high_risk': self.is_high_risk,
            'is_controlled_substance': self.is_controlled_substance,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Medication {self.medication_name} {self.dose} {self.route} {self.frequency}>'


class MedicationAdministration(db.Model):
    """Record of medication administration (MAR)."""
    
    __tablename__ = 'medication_administrations'
    
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)  # Denormalized for fast queries
    administered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    nurse_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Alias for administered_by (backward compatibility)
    
    # Administration Details
    scheduled_time = db.Column(db.DateTime)  # When it was scheduled (optional for PRN)
    administration_time = db.Column(db.DateTime, nullable=False)  # When actually given
    actual_time = db.Column(db.DateTime)  # Alias for administration_time
    dose_given = db.Column(db.String(50))
    
    # Administration route (may differ from ordered route)
    route = db.Column(db.String(50))  # Actual route used
    
    # Status
    status = db.Column(db.String(20), nullable=False)  # given, refused, held, omitted
    
    # If not given
    not_given_reason = db.Column(db.String(200))  # patient refused, NPO, unavailable, etc.
    
    # Assessment
    pre_administration_assessment = db.Column(db.Text)  # vital signs, pain level, etc.
    post_administration_assessment = db.Column(db.Text)  # response, side effects
    
    # PRN Effectiveness Tracking (especially important for behavior/pain meds)
    prn_reason = db.Column(db.String(200))  # Why PRN was given
    prn_reason_given = db.Column(db.String(200))  # Alias for prn_reason
    prn_pain_level_before = db.Column(db.Integer)  # Pain level before med (0-10)
    prn_pain_level_after = db.Column(db.Integer)  # Pain level after med (0-10)
    prn_effectiveness_rating = db.Column(db.Integer)  # 1-5 scale: 1=Not effective, 5=Very effective
    prn_effectiveness_notes = db.Column(db.Text)  # "Pain reduced to 3/10 after 30 min"
    prn_reassessment_time = db.Column(db.DateTime)  # When effectiveness was assessed
    
    # Site (for injections)
    administration_site = db.Column(db.String(100))  # left deltoid, right thigh, etc.
    
    # Notes
    notes = db.Column(db.Text)
    
    # Witnesses (for narcotics)
    witness_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    medication = db.relationship('Medication', back_populates='administrations')
    administered_by_user = db.relationship('User', foreign_keys=[administered_by],
                                           back_populates='medication_administrations')
    witness_user = db.relationship('User', foreign_keys=[witness_id])
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'medication_id': self.medication_id,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'administration_time': (self.administration_time or self.actual_time).isoformat() if (self.administration_time or self.actual_time) else None,
            'actual_time': (self.actual_time or self.administration_time).isoformat() if (self.actual_time or self.administration_time) else None,
            'status': self.status,
            'dose_given': self.dose_given,
            'route': self.route,
            'not_given_reason': self.not_given_reason,
            'prn_reason': self.prn_reason or self.prn_reason_given,
            'administration_site': self.administration_site,
            'notes': self.notes,
            'administered_by': self.administered_by,
            'administered_by_name': f"{self.administered_by_user.first_name} {self.administered_by_user.last_name}" if self.administered_by_user else None,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<MedicationAdministration {self.id}: {self.status} at {self.actual_time}>'
