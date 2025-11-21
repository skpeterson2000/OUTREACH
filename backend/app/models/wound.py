"""Wound assessment model for wound care documentation."""
from datetime import datetime
from app import db


class WoundAssessment(db.Model):
    """Comprehensive wound assessment and tracking."""
    
    __tablename__ = 'wound_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    assessed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'))
    
    # Wound Identification
    wound_id = db.Column(db.String(50))  # Internal tracking ID for this specific wound
    location = db.Column(db.String(200), nullable=False)  # anatomical location
    location_description = db.Column(db.Text)  # detailed description
    
    # Wound Type
    wound_type = db.Column(db.String(100))  # pressure injury, surgical, venous ulcer, etc.
    etiology = db.Column(db.String(200))  # cause of wound
    
    # Staging (Pressure Injuries)
    stage = db.Column(db.String(50))  # Stage 1, 2, 3, 4, Unstageable, DTPI
    
    # Measurements
    length_cm = db.Column(db.Numeric(5, 2))  # longest dimension
    width_cm = db.Column(db.Numeric(5, 2))  # widest dimension perpendicular to length
    depth_cm = db.Column(db.Numeric(5, 2))  # deepest point
    undermining_cm = db.Column(db.Numeric(5, 2))
    undermining_location = db.Column(db.String(100))  # clock position
    tunneling_cm = db.Column(db.Numeric(5, 2))
    tunneling_location = db.Column(db.String(100))  # clock position
    
    # Wound Bed
    wound_bed_description = db.Column(db.Text)
    tissue_type_percentages = db.Column(db.Text)  # JSON: {granulation: 60, slough: 30, etc.}
    necrotic_tissue = db.Column(db.Boolean, default=False)
    
    # Exudate
    exudate_amount = db.Column(db.String(50))  # none, scant, moderate, copious
    exudate_type = db.Column(db.String(50))  # serous, serosanguinous, sanguineous, purulent
    exudate_odor = db.Column(db.String(50))  # none, foul, etc.
    
    # Wound Edges
    edge_description = db.Column(db.String(200))  # attached, unattached, rolled, etc.
    epithelialization = db.Column(db.Boolean, default=False)
    
    # Periwound Skin
    periwound_condition = db.Column(db.String(200))  # intact, macerated, erythematous, etc.
    periwound_edema = db.Column(db.Boolean, default=False)
    periwound_induration = db.Column(db.Boolean, default=False)
    
    # Pain
    pain_level = db.Column(db.Integer)  # 0-10 scale
    pain_description = db.Column(db.Text)
    
    # Signs of Infection
    signs_of_infection = db.Column(db.Text)  # increased drainage, odor, fever, etc.
    
    # Treatment
    cleansing_solution = db.Column(db.String(200))
    dressing_type = db.Column(db.String(200))
    secondary_dressing = db.Column(db.String(200))
    frequency_of_change = db.Column(db.String(100))
    
    # Topical Treatments
    topical_medications = db.Column(db.Text)  # antimicrobials, growth factors, etc.
    
    # Offloading/Pressure Relief
    pressure_relief_devices = db.Column(db.Text)
    
    # Healing Progress
    healing_status = db.Column(db.String(50))  # healing, stable, deteriorating
    compared_to_previous = db.Column(db.Text)  # comparison notes
    
    # Photography
    photo_taken = db.Column(db.Boolean, default=False)
    photo_path = db.Column(db.String(500))
    
    # Assessment Notes
    notes = db.Column(db.Text)
    plan_of_care = db.Column(db.Text)
    
    # Next Assessment
    next_assessment_date = db.Column(db.Date)
    
    # Timestamps
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='wounds')
    nurse = db.relationship('User')
    visit = db.relationship('Visit')
    
    def calculate_area(self):
        """Calculate wound area in cm²."""
        if self.length_cm and self.width_cm:
            return float(self.length_cm * self.width_cm)
        return None
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'wound_id': self.wound_id,
            'location': self.location,
            'wound_type': self.wound_type,
            'stage': self.stage,
            'length_cm': float(self.length_cm) if self.length_cm else None,
            'width_cm': float(self.width_cm) if self.width_cm else None,
            'depth_cm': float(self.depth_cm) if self.depth_cm else None,
            'area_cm2': self.calculate_area(),
            'exudate_amount': self.exudate_amount,
            'exudate_type': self.exudate_type,
            'healing_status': self.healing_status,
            'pain_level': self.pain_level,
            'dressing_type': self.dressing_type,
            'assessment_date': self.assessment_date.isoformat(),
            'assessed_by': self.assessed_by,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<WoundAssessment {self.id}: {self.location} on {self.assessment_date}>'
