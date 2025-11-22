"""
Medication adverse reaction monitoring and surveillance models.

Actively monitors patient observations, vital signs, lab values, and behavior changes
to detect potential adverse drug reactions and medication-related problems.
"""
from datetime import datetime, timedelta
from app import db
from sqlalchemy.dialects.postgresql import JSON


class MedicationAdverseReaction(db.Model):
    """
    Known adverse reactions and side effects for medications.
    
    Serves as knowledge base for active surveillance. Can be populated from
    drug databases (FDA Adverse Event Reporting System, clinical guidelines).
    """
    __tablename__ = 'medication_adverse_reactions'
    
    # Severity constants
    SEVERITY_MINOR = 'MINOR'  # Inconvenient but not dangerous
    SEVERITY_MODERATE = 'MODERATE'  # Uncomfortable, may require intervention
    SEVERITY_MAJOR = 'MAJOR'  # Serious, requires immediate action
    SEVERITY_LIFE_THREATENING = 'LIFE_THREATENING'  # Critical emergency
    
    SEVERITY_LEVELS = [
        SEVERITY_MINOR,
        SEVERITY_MODERATE,
        SEVERITY_MAJOR,
        SEVERITY_LIFE_THREATENING
    ]
    
    # Likelihood constants
    LIKELIHOOD_VERY_COMMON = 'VERY_COMMON'  # >10% of patients
    LIKELIHOOD_COMMON = 'COMMON'  # 1-10%
    LIKELIHOOD_UNCOMMON = 'UNCOMMON'  # 0.1-1%
    LIKELIHOOD_RARE = 'RARE'  # <0.1%
    
    LIKELIHOOD_LEVELS = [
        LIKELIHOOD_VERY_COMMON,
        LIKELIHOOD_COMMON,
        LIKELIHOOD_UNCOMMON,
        LIKELIHOOD_RARE
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Medication identification (can match multiple ways)
    medication_name = db.Column(db.String(200), nullable=False, index=True)
    generic_name = db.Column(db.String(200), index=True)
    drug_class = db.Column(db.String(100), index=True)  # All drugs in class share this ADR
    
    # Adverse reaction details
    reaction_name = db.Column(db.String(200), nullable=False)
    reaction_description = db.Column(db.Text)
    
    # Clinical characteristics
    severity = db.Column(db.String(30), nullable=False)
    likelihood = db.Column(db.String(30))
    
    # Time to onset
    typical_onset_hours = db.Column(db.Integer)  # How soon after starting med
    typical_onset_days = db.Column(db.Integer)
    
    # Observable symptoms/signs (JSON array for pattern matching)
    observable_symptoms = db.Column(JSON, default=[])  # ["nausea", "vomiting", "diarrhea"]
    vital_sign_changes = db.Column(JSON, default={})  # {"heart_rate": "increased", "bp_systolic": "decreased"}
    lab_abnormalities = db.Column(JSON, default=[])  # ["elevated_creatinine", "hyperkalemia"]
    behavioral_changes = db.Column(JSON, default=[])  # ["confusion", "agitation", "lethargy"]
    
    # Clinical guidance
    monitoring_recommendations = db.Column(db.Text)  # What to watch for
    nursing_interventions = db.Column(JSON, default=[])  # Actions within nursing scope (assess, monitor, notify)
    provider_notification_guidance = db.Column(db.Text)  # What to tell provider, what orders may be needed
    when_to_escalate = db.Column(db.Text)  # When to call provider STAT vs routine notification
    
    # Risk factors
    risk_factors = db.Column(JSON, default=[])  # ["elderly", "renal_impairment", "concurrent_diuretics"]
    
    # References
    reference_source = db.Column(db.String(200))  # "FDA Label", "Clinical guideline", etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MedicationAdverseReaction {self.medication_name}: {self.reaction_name}>'
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'medication_name': self.medication_name,
            'generic_name': self.generic_name,
            'drug_class': self.drug_class,
            'reaction_name': self.reaction_name,
            'reaction_description': self.reaction_description,
            'severity': self.severity,
            'likelihood': self.likelihood,
            'typical_onset_hours': self.typical_onset_hours,
            'typical_onset_days': self.typical_onset_days,
            'observable_symptoms': self.observable_symptoms,
            'vital_sign_changes': self.vital_sign_changes,
            'behavioral_changes': self.behavioral_changes,
            'monitoring_recommendations': self.monitoring_recommendations,
            'suggested_interventions': self.suggested_interventions,
            'when_to_escalate': self.when_to_escalate,
            'risk_factors': self.risk_factors
        }


class PatientObservation(db.Model):
    """
    Staff observations of patient condition, symptoms, behaviors.
    
    Used for adverse reaction surveillance - system correlates observations
    with known ADRs for patient's current medications.
    """
    __tablename__ = 'patient_observations'
    
    # Observation type constants
    TYPE_SYMPTOM = 'SYMPTOM'  # Patient complaint or observed symptom
    TYPE_VITAL_SIGN = 'VITAL_SIGN'  # Abnormal vital sign
    TYPE_BEHAVIOR = 'BEHAVIOR'  # Behavioral change
    TYPE_PHYSICAL_FINDING = 'PHYSICAL_FINDING'  # Physical exam finding
    TYPE_LAB_RESULT = 'LAB_RESULT'  # Abnormal lab value
    TYPE_FUNCTIONAL_CHANGE = 'FUNCTIONAL_CHANGE'  # ADL/mobility change
    
    OBSERVATION_TYPES = [
        TYPE_SYMPTOM,
        TYPE_VITAL_SIGN,
        TYPE_BEHAVIOR,
        TYPE_PHYSICAL_FINDING,
        TYPE_LAB_RESULT,
        TYPE_FUNCTIONAL_CHANGE
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    observed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Observation details
    observation_type = db.Column(db.String(50), nullable=False)
    observation_category = db.Column(db.String(100), index=True)  # "GI", "Cardiac", "Neuro", etc.
    observation_text = db.Column(db.Text, nullable=False)  # Free-text description
    
    # Structured data for pattern matching
    standardized_terms = db.Column(JSON, default=[])  # ["nausea", "vomiting"] - standardized for matching
    severity_rating = db.Column(db.Integer)  # 1-10 scale if applicable
    
    # Context
    patient_reported = db.Column(db.Boolean, default=False)  # vs staff observed
    observation_datetime = db.Column(db.DateTime, nullable=False, index=True)
    
    # Related clinical data
    related_vital_signs = db.Column(JSON)  # Vital signs at time of observation
    related_medications = db.Column(JSON, default=[])  # Current meds at time (for faster querying)
    
    # Surveillance results
    adr_surveillance_performed = db.Column(db.Boolean, default=False)
    potential_adr_detected = db.Column(db.Boolean, default=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = db.relationship('Patient', backref=db.backref('observations', lazy='dynamic'))
    facility = db.relationship('Facility')
    observed_by = db.relationship('User', foreign_keys=[observed_by_user_id])
    adr_alerts = db.relationship('ADRAlert', back_populates='observation', lazy='dynamic')
    
    def __repr__(self):
        return f'<PatientObservation {self.id}: {self.observation_type} for Patient {self.patient_id}>'
    
    def to_dict(self, include_alerts=False):
        """Serialize to dictionary."""
        data = {
            'id': self.id,
            'patient_id': self.patient_id,
            'observation_type': self.observation_type,
            'observation_category': self.observation_category,
            'observation_text': self.observation_text,
            'standardized_terms': self.standardized_terms,
            'severity_rating': self.severity_rating,
            'patient_reported': self.patient_reported,
            'observation_datetime': self.observation_datetime.isoformat(),
            'potential_adr_detected': self.potential_adr_detected,
            'created_at': self.created_at.isoformat()
        }
        
        if include_alerts:
            data['adr_alerts'] = [alert.to_dict() for alert in self.adr_alerts.all()]
        
        return data


class ADRAlert(db.Model):
    """
    Active surveillance alert for potential adverse drug reaction.
    
    Generated when system detects correlation between patient observations
    and known adverse reactions for current medications.
    """
    __tablename__ = 'adr_alerts'
    
    # Alert status constants
    STATUS_NEW = 'NEW'  # Newly generated, not yet reviewed
    STATUS_ACKNOWLEDGED = 'ACKNOWLEDGED'  # Nurse aware, monitoring
    STATUS_INVESTIGATING = 'INVESTIGATING'  # Active investigation
    STATUS_CONFIRMED_ADR = 'CONFIRMED_ADR'  # Determined to be ADR
    STATUS_NOT_ADR = 'NOT_ADR'  # Ruled out as ADR
    STATUS_DISMISSED = 'DISMISSED'  # False positive
    
    STATUS_CHOICES = [
        STATUS_NEW,
        STATUS_ACKNOWLEDGED,
        STATUS_INVESTIGATING,
        STATUS_CONFIRMED_ADR,
        STATUS_NOT_ADR,
        STATUS_DISMISSED
    ]
    
    # Confidence level constants
    CONFIDENCE_LOW = 'LOW'  # Possible but unlikely
    CONFIDENCE_MODERATE = 'MODERATE'  # Reasonable possibility
    CONFIDENCE_HIGH = 'HIGH'  # Strong correlation
    CONFIDENCE_VERY_HIGH = 'VERY_HIGH'  # Multiple indicators align
    
    CONFIDENCE_LEVELS = [
        CONFIDENCE_LOW,
        CONFIDENCE_MODERATE,
        CONFIDENCE_HIGH,
        CONFIDENCE_VERY_HIGH
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    
    # Related records
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False, index=True)
    observation_id = db.Column(db.Integer, db.ForeignKey('patient_observations.id'), nullable=False)
    known_adr_id = db.Column(db.Integer, db.ForeignKey('medication_adverse_reactions.id'), nullable=False)
    
    # Alert details
    suspected_reaction = db.Column(db.String(200), nullable=False)
    alert_summary = db.Column(db.Text, nullable=False)  # Human-readable alert message
    confidence_level = db.Column(db.String(20), nullable=False)
    severity = db.Column(db.String(30), nullable=False)  # From known ADR
    
    # Correlation details
    matching_symptoms = db.Column(JSON, default=[])  # Which symptoms matched
    matching_vital_signs = db.Column(JSON, default=[])  # Which vital sign changes matched
    matching_behaviors = db.Column(JSON, default=[])  # Which behaviors matched
    correlation_score = db.Column(db.Float)  # 0.0-1.0 algorithmic match score
    
    # Time correlation
    medication_start_date = db.Column(db.Date)  # When med was started
    days_since_medication_start = db.Column(db.Integer)  # Onset timing
    expected_onset_match = db.Column(db.Boolean, default=False)  # Does timing fit known ADR onset?
    
    # Risk factors present
    patient_risk_factors = db.Column(JSON, default=[])  # Which risk factors patient has
    
    # Suggested actions (respecting scope of practice)
    nursing_interventions = db.Column(JSON, default=[])  # Actions within nursing scope
    provider_notification_needed = db.Column(db.Boolean, default=True)  # Does provider need to be notified?
    provider_notification_urgency = db.Column(db.String(20))  # 'ROUTINE', 'URGENT', 'STAT'
    provider_notification_guidance = db.Column(db.Text)  # What to tell provider
    suggested_provider_orders = db.Column(JSON, default=[])  # What provider may want to order
    requires_immediate_action = db.Column(db.Boolean, default=False)  # STAT notification needed
    escalation_guidance = db.Column(db.Text)
    
    # Hospice-specific considerations
    is_hospice_patient = db.Column(db.Boolean, default=False)
    hospice_comfort_focus = db.Column(db.Text)  # Comfort-focused interventions for hospice
    
    # Clinical team actions
    status = db.Column(db.String(30), default=STATUS_NEW, nullable=False, index=True)
    acknowledged_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    
    # Investigation outcome
    investigation_notes = db.Column(db.Text)
    action_taken = db.Column(db.Text)
    outcome = db.Column(db.Text)
    
    # Pharmacist involvement
    pharmacist_consulted = db.Column(db.Boolean, default=False)
    pharmacist_intervention_id = db.Column(db.Integer, db.ForeignKey('pharmacist_interventions.id'))
    
    # Provider notification
    provider_notified = db.Column(db.Boolean, default=False)
    provider_notified_at = db.Column(db.DateTime)
    provider_response = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    patient = db.relationship('Patient')
    facility = db.relationship('Facility')
    medication = db.relationship('Medication')
    observation = db.relationship('PatientObservation', back_populates='adr_alerts')
    known_adr = db.relationship('MedicationAdverseReaction')
    acknowledged_by = db.relationship('User', foreign_keys=[acknowledged_by_user_id])
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_user_id])
    pharmacist_intervention = db.relationship('PharmacistIntervention')
    
    def __repr__(self):
        return f'<ADRAlert {self.id}: {self.suspected_reaction} for Patient {self.patient_id}>'
    
    @property
    def is_active(self):
        """Check if alert is still active (not resolved)."""
        return self.status in [self.STATUS_NEW, self.STATUS_ACKNOWLEDGED, self.STATUS_INVESTIGATING]
    
    @property
    def response_time_hours(self):
        """Calculate time from alert creation to acknowledgment."""
        if not self.acknowledged_at:
            return None
        delta = self.acknowledged_at - self.created_at
        return round(delta.total_seconds() / 3600, 1)
    
    @property
    def resolution_time_hours(self):
        """Calculate time from alert creation to resolution."""
        if not self.resolved_at:
            return None
        delta = self.resolved_at - self.created_at
        return round(delta.total_seconds() / 3600, 1)
    
    def to_dict(self, include_suggestions=True):
        """Serialize to dictionary."""
        data = {
            'id': self.id,
            'patient_id': self.patient_id,
            'medication_id': self.medication_id,
            'observation_id': self.observation_id,
            'suspected_reaction': self.suspected_reaction,
            'alert_summary': self.alert_summary,
            'confidence_level': self.confidence_level,
            'severity': self.severity,
            'matching_symptoms': self.matching_symptoms,
            'matching_vital_signs': self.matching_vital_signs,
            'matching_behaviors': self.matching_behaviors,
            'correlation_score': self.correlation_score,
            'days_since_medication_start': self.days_since_medication_start,
            'expected_onset_match': self.expected_onset_match,
            'patient_risk_factors': self.patient_risk_factors,
            'requires_immediate_action': self.requires_immediate_action,
            'status': self.status,
            'is_active': self.is_active,
            'response_time_hours': self.response_time_hours,
            'resolution_time_hours': self.resolution_time_hours,
            'pharmacist_consulted': self.pharmacist_consulted,
            'provider_notified': self.provider_notified,
            'created_at': self.created_at.isoformat(),
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
        
        if include_suggestions:
            data['nursing_interventions'] = self.nursing_interventions
            data['provider_notification_needed'] = self.provider_notification_needed
            data['provider_notification_urgency'] = self.provider_notification_urgency
            data['provider_notification_guidance'] = self.provider_notification_guidance
            data['suggested_provider_orders'] = self.suggested_provider_orders
            data['escalation_guidance'] = self.escalation_guidance
            data['is_hospice_patient'] = self.is_hospice_patient
            data['hospice_comfort_focus'] = self.hospice_comfort_focus
        
        return data


class ADRAlertAcknowledgment(db.Model):
    """
    Individual staff acknowledgments of ADR alerts.
    
    Each staff member who administers medications to a patient must independently
    acknowledge each active ADR alert before giving meds. Acknowledgments expire
    after each shift (12 hours) requiring re-acknowledgment.
    """
    __tablename__ = 'adr_alert_acknowledgments'
    
    # Action constants
    ACTION_ACKNOWLEDGED = 'ACKNOWLEDGED'  # Aware and monitoring
    ACTION_HOLD_MEDICATION = 'HOLD_MEDICATION'  # Holding suspect medication
    
    ACTION_CHOICES = [
        ACTION_ACKNOWLEDGED,
        ACTION_HOLD_MEDICATION
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('adr_alerts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    
    # Acknowledgment details
    action_taken = db.Column(db.String(30), nullable=False)  # ACKNOWLEDGED or HOLD_MEDICATION
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)  # 12 hours from acknowledgment
    
    # Safety verification checkboxes (required)
    verified_reaction_awareness = db.Column(db.Boolean, default=False, nullable=False)
    verified_monitoring_parameters = db.Column(db.Boolean, default=False, nullable=False)
    verified_escalation_criteria = db.Column(db.Boolean, default=False, nullable=False)
    
    # If holding medication
    hold_reason = db.Column(db.Text)  # Required if action = HOLD_MEDICATION
    hold_duration = db.Column(db.String(50))  # "Until symptoms resolve", "24 hours", etc.
    provider_notified = db.Column(db.Boolean, default=False)
    provider_notified_at = db.Column(db.DateTime)
    hold_order_obtained = db.Column(db.Boolean, default=False)  # Provider order to hold
    
    # Staff notes
    notes = db.Column(db.Text)
    monitoring_plan = db.Column(db.Text)  # What staff member plans to monitor
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    alert = db.relationship('ADRAlert', backref=db.backref('acknowledgments', lazy='dynamic'))
    user = db.relationship('User')
    facility = db.relationship('Facility')
    
    def __repr__(self):
        return f'<ADRAlertAcknowledgment Alert#{self.alert_id} by User#{self.user_id}>'
    
    @property
    def is_expired(self):
        """Check if acknowledgment has expired (shift ended)."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if acknowledgment is still valid."""
        return not self.is_expired and all([
            self.verified_reaction_awareness,
            self.verified_monitoring_parameters,
            self.verified_escalation_criteria
        ])
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'action_taken': self.action_taken,
            'acknowledged_at': self.acknowledged_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_expired': self.is_expired,
            'is_valid': self.is_valid,
            'verified_reaction_awareness': self.verified_reaction_awareness,
            'verified_monitoring_parameters': self.verified_monitoring_parameters,
            'verified_escalation_criteria': self.verified_escalation_criteria,
            'hold_reason': self.hold_reason,
            'hold_duration': self.hold_duration,
            'provider_notified': self.provider_notified,
            'provider_notified_at': self.provider_notified_at.isoformat() if self.provider_notified_at else None,
            'hold_order_obtained': self.hold_order_obtained,
            'notes': self.notes,
            'monitoring_plan': self.monitoring_plan,
            'created_at': self.created_at.isoformat()
        }


class ADRSurveillanceLog(db.Model):
    """
    Audit log for ADR surveillance system operations.
    
    Tracks when surveillance runs, what it detected, and system performance metrics.
    """
    __tablename__ = 'adr_surveillance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Surveillance run details
    run_type = db.Column(db.String(50))  # "REAL_TIME", "BATCH", "MANUAL"
    patients_screened = db.Column(db.Integer)
    observations_analyzed = db.Column(db.Integer)
    alerts_generated = db.Column(db.Integer)
    
    # Performance metrics
    execution_time_seconds = db.Column(db.Float)
    
    # Results
    high_severity_alerts = db.Column(db.Integer)
    immediate_action_alerts = db.Column(db.Integer)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ADRSurveillanceLog {self.id}: {self.alerts_generated} alerts from {self.observations_analyzed} observations>'
