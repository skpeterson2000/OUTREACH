"""
Medication reconciliation models for care transitions and pharmacist collaboration.

Supports medication reconciliation at admission, transfer, and discharge with
automated discrepancy detection and pharmacist intervention tracking.
"""
from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON


class MedicationReconciliation(db.Model):
    """
    Medication reconciliation event at care transitions.
    
    Tracks comparison of medication lists when patient moves between care settings
    (hospital → TCU, TCU → home, etc.) to identify and resolve discrepancies.
    """
    __tablename__ = 'medication_reconciliations'
    
    # Reconciliation type constants
    TYPE_ADMISSION = 'ADMISSION'
    TYPE_TRANSFER = 'TRANSFER'
    TYPE_DISCHARGE = 'DISCHARGE'
    TYPE_ROUTINE_REVIEW = 'ROUTINE_REVIEW'
    
    RECONCILIATION_TYPES = [
        TYPE_ADMISSION,
        TYPE_TRANSFER,
        TYPE_DISCHARGE,
        TYPE_ROUTINE_REVIEW
    ]
    
    # Status constants
    STATUS_PENDING = 'PENDING'
    STATUS_IN_REVIEW = 'IN_REVIEW'
    STATUS_PHARMACIST_REVIEW = 'PHARMACIST_REVIEW'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'
    
    STATUS_CHOICES = [
        STATUS_PENDING,
        STATUS_IN_REVIEW,
        STATUS_PHARMACIST_REVIEW,
        STATUS_COMPLETED,
        STATUS_CANCELLED
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    
    # Reconciliation context
    reconciliation_type = db.Column(db.String(50), nullable=False, index=True)
    transition_from = db.Column(db.String(200))  # "St. Mary's Hospital", "Home", etc.
    transition_to = db.Column(db.String(200))  # "Sunrise TCU", "Home with home health", etc.
    
    # Source documentation
    source_document_type = db.Column(db.String(100))  # "Hospital discharge summary", "Previous MAR", "Pharmacy list"
    source_document_date = db.Column(db.Date)
    source_document_url = db.Column(db.String(500))  # Link to uploaded PDF/scan
    
    # Medication lists (stored as JSON arrays)
    source_medications = db.Column(JSON, default=[])  # Medications from source document
    current_medications = db.Column(JSON, default=[])  # Current active medications before reconciliation
    reconciled_medications = db.Column(JSON, default=[])  # Final reconciled medication list
    
    # Discrepancy summary
    discrepancies_count = db.Column(db.Integer, default=0)
    high_risk_discrepancies = db.Column(db.Integer, default=0)  # Count of critical issues
    
    # Review tracking
    initiated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reconciled_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_by_pharmacist_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Status and completion
    status = db.Column(db.String(50), default=STATUS_PENDING, nullable=False, index=True)
    requires_pharmacist_review = db.Column(db.Boolean, default=False)  # Auto-flagged for high-risk cases
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    review_started_at = db.Column(db.DateTime)
    pharmacist_review_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Clinical notes
    clinical_summary = db.Column(db.Text)  # Why medications changed
    reconciliation_notes = db.Column(db.Text)  # Provider notes during reconciliation
    
    # Relationships
    patient = db.relationship('Patient', backref=db.backref('medication_reconciliations', lazy='dynamic'))
    facility = db.relationship('Facility')
    initiated_by = db.relationship('User', foreign_keys=[initiated_by_user_id])
    reconciled_by = db.relationship('User', foreign_keys=[reconciled_by_user_id])
    reviewed_by_pharmacist = db.relationship('User', foreign_keys=[reviewed_by_pharmacist_id])
    discrepancies = db.relationship('MedicationDiscrepancy', back_populates='reconciliation',
                                   lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MedicationReconciliation {self.reconciliation_type} for Patient {self.patient_id}>'
    
    @property
    def is_overdue(self):
        """Check if reconciliation is overdue (>24 hours for admission, >72 hours for routine)."""
        if self.status in [self.STATUS_COMPLETED, self.STATUS_CANCELLED]:
            return False
        
        from datetime import timedelta
        threshold = timedelta(hours=24 if self.reconciliation_type == self.TYPE_ADMISSION else 72)
        return (datetime.utcnow() - self.created_at) > threshold
    
    def to_dict(self, include_discrepancies=False):
        """Serialize to dictionary."""
        data = {
            'id': self.id,
            'patient_id': self.patient_id,
            'facility_id': self.facility_id,
            'reconciliation_type': self.reconciliation_type,
            'transition_from': self.transition_from,
            'transition_to': self.transition_to,
            'source_document_type': self.source_document_type,
            'source_document_date': self.source_document_date.isoformat() if self.source_document_date else None,
            'discrepancies_count': self.discrepancies_count,
            'high_risk_discrepancies': self.high_risk_discrepancies,
            'status': self.status,
            'requires_pharmacist_review': self.requires_pharmacist_review,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'source_medications': self.source_medications,
            'current_medications': self.current_medications,
            'reconciled_medications': self.reconciled_medications
        }
        
        if include_discrepancies:
            data['discrepancies'] = [d.to_dict() for d in self.discrepancies.all()]
        
        return data


class MedicationDiscrepancy(db.Model):
    """
    Individual medication discrepancy found during reconciliation.
    
    Represents a specific difference between source and current medication lists
    that requires clinical review and resolution.
    """
    __tablename__ = 'medication_discrepancies'
    
    # Discrepancy type constants
    TYPE_NEW_MED = 'NEW_MED'  # Medication added that wasn't in source
    TYPE_DISCONTINUED = 'DISCONTINUED'  # Medication in source but not current
    TYPE_DOSE_CHANGE = 'DOSE_CHANGE'  # Dose differs from source
    TYPE_FREQUENCY_CHANGE = 'FREQUENCY_CHANGE'  # Frequency differs
    TYPE_ROUTE_CHANGE = 'ROUTE_CHANGE'  # Route of administration changed
    TYPE_DUPLICATE_THERAPY = 'DUPLICATE_THERAPY'  # Same drug class prescribed twice
    TYPE_MISSING_MED = 'MISSING_MED'  # Expected medication not present
    TYPE_CONFLICTING_ORDERS = 'CONFLICTING_ORDERS'  # Contradictory orders present
    
    DISCREPANCY_TYPES = [
        TYPE_NEW_MED,
        TYPE_DISCONTINUED,
        TYPE_DOSE_CHANGE,
        TYPE_FREQUENCY_CHANGE,
        TYPE_ROUTE_CHANGE,
        TYPE_DUPLICATE_THERAPY,
        TYPE_MISSING_MED,
        TYPE_CONFLICTING_ORDERS
    ]
    
    # Severity constants
    SEVERITY_LOW = 'LOW'  # Informational, unlikely to cause harm
    SEVERITY_MEDIUM = 'MEDIUM'  # Could cause harm if not addressed
    SEVERITY_HIGH = 'HIGH'  # Likely to cause significant harm
    SEVERITY_CRITICAL = 'CRITICAL'  # Immediate risk to patient safety
    
    SEVERITY_LEVELS = [
        SEVERITY_LOW,
        SEVERITY_MEDIUM,
        SEVERITY_HIGH,
        SEVERITY_CRITICAL
    ]
    
    # Resolution action constants
    ACTION_ACCEPTED = 'ACCEPTED'  # Discrepancy is intentional and correct
    ACTION_MODIFIED = 'MODIFIED'  # Order modified to resolve discrepancy
    ACTION_DISCONTINUED = 'DISCONTINUED'  # Medication discontinued
    ACTION_CLARIFICATION_NEEDED = 'CLARIFICATION_NEEDED'  # Requires provider input
    ACTION_PHARMACY_CONSULT = 'PHARMACY_CONSULT'  # Referred to pharmacist
    ACTION_PENDING = 'PENDING'  # Not yet resolved
    
    RESOLUTION_ACTIONS = [
        ACTION_ACCEPTED,
        ACTION_MODIFIED,
        ACTION_DISCONTINUED,
        ACTION_CLARIFICATION_NEEDED,
        ACTION_PHARMACY_CONSULT,
        ACTION_PENDING
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    reconciliation_id = db.Column(db.Integer, db.ForeignKey('medication_reconciliations.id'), 
                                  nullable=False, index=True)
    
    # Discrepancy details
    discrepancy_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False, index=True)
    
    # Medication information
    medication_name = db.Column(db.String(200), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'))  # If linked to existing med
    
    # Source vs current comparison
    source_details = db.Column(JSON)  # What the source document stated
    current_details = db.Column(JSON)  # What the current MAR shows
    
    # Clinical context
    clinical_concern = db.Column(db.Text)  # Auto-generated or pharmacist-added concern description
    potential_impact = db.Column(db.Text)  # Why this matters clinically
    
    # Resolution
    resolution_action = db.Column(db.String(50), default=ACTION_PENDING)
    resolution_notes = db.Column(db.Text)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    
    # Flagging
    requires_pharmacist_input = db.Column(db.Boolean, default=False)
    requires_provider_clarification = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reconciliation = db.relationship('MedicationReconciliation', back_populates='discrepancies')
    medication = db.relationship('Medication')
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_user_id])
    
    def __repr__(self):
        return f'<MedicationDiscrepancy {self.discrepancy_type}: {self.medication_name}>'
    
    @property
    def is_resolved(self):
        """Check if discrepancy has been resolved."""
        return self.resolution_action != self.ACTION_PENDING
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'reconciliation_id': self.reconciliation_id,
            'discrepancy_type': self.discrepancy_type,
            'severity': self.severity,
            'medication_name': self.medication_name,
            'medication_id': self.medication_id,
            'source_details': self.source_details,
            'current_details': self.current_details,
            'clinical_concern': self.clinical_concern,
            'potential_impact': self.potential_impact,
            'resolution_action': self.resolution_action,
            'resolution_notes': self.resolution_notes,
            'is_resolved': self.is_resolved,
            'requires_pharmacist_input': self.requires_pharmacist_input,
            'requires_provider_clarification': self.requires_provider_clarification,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class PharmacistIntervention(db.Model):
    """
    Pharmacist clinical intervention record.
    
    Documents pharmacist recommendations, clinical concerns, and outcomes.
    Supports MTM (Medication Therapy Management) billing documentation.
    """
    __tablename__ = 'pharmacist_interventions'
    
    # Intervention type constants
    TYPE_DRUG_INTERACTION = 'DRUG_INTERACTION'
    TYPE_DOSE_ADJUSTMENT = 'DOSE_ADJUSTMENT'
    TYPE_ALTERNATIVE_RECOMMENDATION = 'ALTERNATIVE_RECOMMENDATION'
    TYPE_THERAPY_MONITORING = 'THERAPY_MONITORING'
    TYPE_ADVERSE_REACTION = 'ADVERSE_REACTION'
    TYPE_MEDICATION_ERROR = 'MEDICATION_ERROR'
    TYPE_ALLERGY_CONCERN = 'ALLERGY_CONCERN'
    TYPE_DUPLICATE_THERAPY = 'DUPLICATE_THERAPY'
    TYPE_RENAL_ADJUSTMENT = 'RENAL_ADJUSTMENT'
    TYPE_THERAPEUTIC_OPTIMIZATION = 'THERAPEUTIC_OPTIMIZATION'
    
    INTERVENTION_TYPES = [
        TYPE_DRUG_INTERACTION,
        TYPE_DOSE_ADJUSTMENT,
        TYPE_ALTERNATIVE_RECOMMENDATION,
        TYPE_THERAPY_MONITORING,
        TYPE_ADVERSE_REACTION,
        TYPE_MEDICATION_ERROR,
        TYPE_ALLERGY_CONCERN,
        TYPE_DUPLICATE_THERAPY,
        TYPE_RENAL_ADJUSTMENT,
        TYPE_THERAPEUTIC_OPTIMIZATION
    ]
    
    # Severity constants
    SEVERITY_INFORMATIONAL = 'INFORMATIONAL'
    SEVERITY_MONITOR = 'MONITOR'
    SEVERITY_RECOMMEND_CHANGE = 'RECOMMEND_CHANGE'
    SEVERITY_URGENT = 'URGENT'
    
    SEVERITY_LEVELS = [
        SEVERITY_INFORMATIONAL,
        SEVERITY_MONITOR,
        SEVERITY_RECOMMEND_CHANGE,
        SEVERITY_URGENT
    ]
    
    # Outcome constants
    OUTCOME_ACCEPTED = 'ACCEPTED'
    OUTCOME_MODIFIED = 'MODIFIED'
    OUTCOME_DECLINED = 'DECLINED'
    OUTCOME_PENDING = 'PENDING'
    
    OUTCOME_CHOICES = [
        OUTCOME_ACCEPTED,
        OUTCOME_MODIFIED,
        OUTCOME_DECLINED,
        OUTCOME_PENDING
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    pharmacist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Related medication (if applicable)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'))
    
    # Related reconciliation (if intervention came from reconciliation review)
    reconciliation_id = db.Column(db.Integer, db.ForeignKey('medication_reconciliations.id'))
    
    # Intervention details
    intervention_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(30), nullable=False)
    
    # Clinical documentation
    clinical_concern = db.Column(db.Text, nullable=False)  # What the pharmacist identified
    recommendation = db.Column(db.Text, nullable=False)  # What the pharmacist recommends
    clinical_rationale = db.Column(db.Text)  # Why this recommendation is made
    supporting_references = db.Column(db.Text)  # Citations, guidelines, etc.
    
    # Provider interaction
    provider_notified = db.Column(db.Boolean, default=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Which provider was contacted
    provider_notification_method = db.Column(db.String(50))  # "In-system message", "Phone", "In-person"
    provider_response = db.Column(db.Text)
    
    # Outcome
    outcome = db.Column(db.String(30), default=OUTCOME_PENDING)
    outcome_notes = db.Column(db.Text)
    intervention_prevented_error = db.Column(db.Boolean, default=False)  # Quality metric
    
    # MTM billing support
    mtm_billable = db.Column(db.Boolean, default=False)
    time_spent_minutes = db.Column(db.Integer)  # For billing documentation
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    provider_notified_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    
    # Relationships
    patient = db.relationship('Patient', backref=db.backref('pharmacist_interventions', lazy='dynamic'))
    facility = db.relationship('Facility')
    pharmacist = db.relationship('User', foreign_keys=[pharmacist_id])
    provider = db.relationship('User', foreign_keys=[provider_id])
    medication = db.relationship('Medication')
    reconciliation = db.relationship('MedicationReconciliation')
    
    def __repr__(self):
        return f'<PharmacistIntervention {self.intervention_type} for Patient {self.patient_id}>'
    
    @property
    def is_resolved(self):
        """Check if intervention has been resolved."""
        return self.outcome != self.OUTCOME_PENDING
    
    @property
    def response_time_hours(self):
        """Calculate time from creation to resolution."""
        if not self.resolved_at:
            return None
        delta = self.resolved_at - self.created_at
        return round(delta.total_seconds() / 3600, 1)
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'facility_id': self.facility_id,
            'pharmacist_id': self.pharmacist_id,
            'medication_id': self.medication_id,
            'reconciliation_id': self.reconciliation_id,
            'intervention_type': self.intervention_type,
            'severity': self.severity,
            'clinical_concern': self.clinical_concern,
            'recommendation': self.recommendation,
            'clinical_rationale': self.clinical_rationale,
            'provider_notified': self.provider_notified,
            'provider_response': self.provider_response,
            'outcome': self.outcome,
            'outcome_notes': self.outcome_notes,
            'intervention_prevented_error': self.intervention_prevented_error,
            'is_resolved': self.is_resolved,
            'response_time_hours': self.response_time_hours,
            'mtm_billable': self.mtm_billable,
            'time_spent_minutes': self.time_spent_minutes,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class PharmacistCollaboration(db.Model):
    """
    Collaboration thread between care team members about medication issues.
    
    Supports asynchronous communication to eliminate phone tag between
    nurses, pharmacists, and providers.
    """
    __tablename__ = 'pharmacist_collaborations'
    
    # Priority constants
    PRIORITY_ROUTINE = 'ROUTINE'
    PRIORITY_URGENT = 'URGENT'
    PRIORITY_STAT = 'STAT'
    
    PRIORITY_LEVELS = [
        PRIORITY_ROUTINE,
        PRIORITY_URGENT,
        PRIORITY_STAT
    ]
    
    # Status constants
    STATUS_OPEN = 'OPEN'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CLOSED = 'CLOSED'
    
    STATUS_CHOICES = [
        STATUS_OPEN,
        STATUS_IN_PROGRESS,
        STATUS_RESOLVED,
        STATUS_CLOSED
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    
    # Thread details
    subject = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20), default=PRIORITY_ROUTINE, nullable=False)
    status = db.Column(db.String(20), default=STATUS_OPEN, nullable=False, index=True)
    
    # Participants (stored as JSON array of user IDs)
    participants = db.Column(JSON, default=[])
    
    # Assignment
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_pharmacist_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Related records
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'))
    reconciliation_id = db.Column(db.Integer, db.ForeignKey('medication_reconciliations.id'))
    intervention_id = db.Column(db.Integer, db.ForeignKey('pharmacist_interventions.id'))
    
    # Resolution
    resolution_summary = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    
    # Relationships
    patient = db.relationship('Patient')
    facility = db.relationship('Facility')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    assigned_to_pharmacist = db.relationship('User', foreign_keys=[assigned_to_pharmacist_id])
    medication = db.relationship('Medication')
    reconciliation = db.relationship('MedicationReconciliation')
    intervention = db.relationship('PharmacistIntervention')
    messages = db.relationship('PharmacistCollaborationMessage', back_populates='collaboration',
                              lazy='dynamic', cascade='all, delete-orphan', 
                              order_by='PharmacistCollaborationMessage.created_at')
    
    def __repr__(self):
        return f'<PharmacistCollaboration {self.id}: {self.subject}>'
    
    @property
    def message_count(self):
        """Count messages in thread."""
        return self.messages.count()
    
    @property
    def resolution_time_hours(self):
        """Calculate time from creation to closure."""
        if not self.closed_at:
            return None
        delta = self.closed_at - self.created_at
        return round(delta.total_seconds() / 3600, 1)
    
    def to_dict(self, include_messages=False):
        """Serialize to dictionary."""
        data = {
            'id': self.id,
            'patient_id': self.patient_id,
            'facility_id': self.facility_id,
            'subject': self.subject,
            'priority': self.priority,
            'status': self.status,
            'participants': self.participants,
            'created_by_user_id': self.created_by_user_id,
            'assigned_to_pharmacist_id': self.assigned_to_pharmacist_id,
            'medication_id': self.medication_id,
            'message_count': self.message_count,
            'resolution_summary': self.resolution_summary,
            'resolution_time_hours': self.resolution_time_hours,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }
        
        if include_messages:
            data['messages'] = [m.to_dict() for m in self.messages.all()]
        
        return data


class PharmacistCollaborationMessage(db.Model):
    """
    Individual message in a collaboration thread.
    """
    __tablename__ = 'pharmacist_collaboration_messages'
    
    # Message type constants
    TYPE_QUESTION = 'QUESTION'
    TYPE_RESPONSE = 'RESPONSE'
    TYPE_RECOMMENDATION = 'RECOMMENDATION'
    TYPE_ORDER_CHANGE = 'ORDER_CHANGE'
    TYPE_RESOLUTION = 'RESOLUTION'
    TYPE_NOTE = 'NOTE'
    
    MESSAGE_TYPES = [
        TYPE_QUESTION,
        TYPE_RESPONSE,
        TYPE_RECOMMENDATION,
        TYPE_ORDER_CHANGE,
        TYPE_RESOLUTION,
        TYPE_NOTE
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    collaboration_id = db.Column(db.Integer, db.ForeignKey('pharmacist_collaborations.id'),
                                nullable=False, index=True)
    author_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Message content
    message_type = db.Column(db.String(30), default=TYPE_NOTE)
    message_text = db.Column(db.Text, nullable=False)
    
    # Attachments (links to uploaded documents, lab results, etc.)
    attachments = db.Column(JSON, default=[])
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    collaboration = db.relationship('PharmacistCollaboration', back_populates='messages')
    author = db.relationship('User', foreign_keys=[author_user_id])
    
    def __repr__(self):
        return f'<PharmacistCollaborationMessage {self.id} in Thread {self.collaboration_id}>'
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'collaboration_id': self.collaboration_id,
            'author_user_id': self.author_user_id,
            'message_type': self.message_type,
            'message_text': self.message_text,
            'attachments': self.attachments,
            'created_at': self.created_at.isoformat()
        }
