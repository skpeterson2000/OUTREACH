"""Care Plan models for nursing interventions, physician orders, and assistance tasks."""
from datetime import datetime, timedelta
from app import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Text


class CarePlan(db.Model):
    """Master care plan for a patient - contains goals and overall plan of care."""
    
    __tablename__ = 'care_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    
    # Plan metadata
    plan_name = db.Column(db.String(200), nullable=False)  # e.g., "Post-Surgical Recovery", "Chronic Disease Management"
    plan_type = db.Column(db.String(50))  # admission, ongoing, discharge, hospice
    
    # Clinical information
    primary_diagnosis = db.Column(db.Text)  # Can override patient diagnosis for specific episode
    care_goals = db.Column(Text)  # JSON array of goals
    
    # Dates
    start_date = db.Column(db.Date, nullable=False)
    target_end_date = db.Column(db.Date)  # Expected discharge/completion
    actual_end_date = db.Column(db.Date)
    last_reviewed_date = db.Column(db.Date)
    next_review_date = db.Column(db.Date)  # Care plans require periodic review
    
    # Status
    status = db.Column(db.String(20), default='active', index=True)  # active, completed, discontinued
    
    # Team
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    primary_nurse_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # RN responsible for plan
    physician_name = db.Column(db.String(200))  # Ordering physician
    physician_phone = db.Column(db.String(20))
    
    # Documentation
    clinical_summary = db.Column(db.Text)  # Current condition, progress notes
    discharge_plan = db.Column(db.Text)  # Discharge planning notes
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref='care_plans')
    nursing_interventions = db.relationship('NursingIntervention', backref='care_plan', lazy='dynamic', cascade='all, delete-orphan')
    physician_orders = db.relationship('PhysicianOrder', backref='care_plan', lazy='dynamic', cascade='all, delete-orphan')
    assistance_tasks = db.relationship('AssistanceTask', backref='care_plan', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'facility_id': self.facility_id,
            'plan_name': self.plan_name,
            'plan_type': self.plan_type,
            'primary_diagnosis': self.primary_diagnosis,
            'care_goals': self.care_goals,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'target_end_date': self.target_end_date.isoformat() if self.target_end_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'last_reviewed_date': self.last_reviewed_date.isoformat() if self.last_reviewed_date else None,
            'next_review_date': self.next_review_date.isoformat() if self.next_review_date else None,
            'status': self.status,
            'primary_nurse_id': self.primary_nurse_id,
            'physician_name': self.physician_name,
            'physician_phone': self.physician_phone,
            'clinical_summary': self.clinical_summary,
            'discharge_plan': self.discharge_plan,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class NursingIntervention(db.Model):
    """Nursing interventions - assessments, treatments, patient education, etc."""
    
    __tablename__ = 'nursing_interventions'
    
    id = db.Column(db.Integer, primary_key=True)
    care_plan_id = db.Column(db.Integer, db.ForeignKey('care_plans.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    
    # Intervention details
    intervention_type = db.Column(db.String(50), nullable=False, index=True)  # assessment, wound_care, education, monitoring, etc.
    intervention_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    rationale = db.Column(db.Text)  # Why this intervention is needed
    
    # Scheduling
    frequency = db.Column(db.String(100))  # "Daily", "BID", "PRN", "Weekly on Monday", etc.
    frequency_times_per_day = db.Column(db.Integer)
    scheduled_times = db.Column(Text)  # JSON array of times ["08:00", "20:00"]
    prn_indication = db.Column(db.Text)  # For PRN interventions, when to perform
    
    # Dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    
    # Assignment
    assigned_role = db.Column(db.String(20))  # Which role should perform (RN, LPN, CNA, etc.)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Specific user assignment
    requires_rn = db.Column(db.Boolean, default=False)  # Must be performed by RN
    can_delegate = db.Column(db.Boolean, default=True)  # Can be delegated to LPN/CNA
    
    # Status
    status = db.Column(db.String(20), default='active', index=True)  # active, completed, discontinued, on_hold
    priority = db.Column(db.String(20), default='routine')  # stat, urgent, routine
    
    # Documentation requirements
    requires_documentation = db.Column(db.Boolean, default=True)
    documentation_template = db.Column(Text)  # JSON template for required fields
    
    # Expected outcomes
    expected_outcome = db.Column(db.Text)
    outcome_measures = db.Column(Text)  # JSON array of measurable outcomes
    
    # Metadata
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    discontinued_at = db.Column(db.DateTime)
    discontinued_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    discontinued_reason = db.Column(db.Text)
    
    # Relationships
    patient = db.relationship('Patient', backref='nursing_interventions')
    completions = db.relationship('InterventionCompletion', backref='intervention', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'care_plan_id': self.care_plan_id,
            'patient_id': self.patient_id,
            'intervention_type': self.intervention_type,
            'intervention_name': self.intervention_name,
            'description': self.description,
            'rationale': self.rationale,
            'frequency': self.frequency,
            'frequency_times_per_day': self.frequency_times_per_day,
            'scheduled_times': self.scheduled_times,
            'prn_indication': self.prn_indication,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'assigned_role': self.assigned_role,
            'assigned_user_id': self.assigned_user_id,
            'requires_rn': self.requires_rn,
            'can_delegate': self.can_delegate,
            'status': self.status,
            'priority': self.priority,
            'requires_documentation': self.requires_documentation,
            'expected_outcome': self.expected_outcome,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PhysicianOrder(db.Model):
    """Physician orders - treatments, tests, consultations, etc."""
    
    __tablename__ = 'physician_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    care_plan_id = db.Column(db.Integer, db.ForeignKey('care_plans.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    
    # Order details
    order_type = db.Column(db.String(50), nullable=False, index=True)  # medication, lab, imaging, consultation, therapy, dme, etc.
    order_category = db.Column(db.String(50))  # For grouping (respiratory, cardiac, wound, etc.)
    order_text = db.Column(db.Text, nullable=False)  # Full order as written by physician
    
    # Ordering provider
    ordering_physician = db.Column(db.String(200), nullable=False)
    physician_npi = db.Column(db.String(20))
    physician_phone = db.Column(db.String(20))
    
    # Dates
    order_date = db.Column(db.DateTime, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # For time-limited orders
    
    # Order details
    frequency = db.Column(db.String(100))  # How often to perform
    duration = db.Column(db.String(100))  # "x 7 days", "until healed", etc.
    prn_indication = db.Column(db.Text)  # For PRN orders
    
    # Status tracking
    status = db.Column(db.String(20), default='active', index=True)  # pending, active, completed, discontinued, expired
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, clarification_needed
    verified_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # RN who verified order
    verified_at = db.Column(db.DateTime)
    
    # Implementation
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Who is responsible
    implementation_notes = db.Column(db.Text)  # How order is being carried out
    
    # Priority
    priority = db.Column(db.String(20), default='routine')  # stat, urgent, routine
    
    # Special instructions
    special_instructions = db.Column(db.Text)
    contraindications = db.Column(db.Text)
    precautions = db.Column(db.Text)
    
    # Discontinuation
    discontinued_at = db.Column(db.DateTime)
    discontinued_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    discontinued_reason = db.Column(db.Text)
    
    # Metadata
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref='physician_orders')
    completions = db.relationship('OrderCompletion', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'care_plan_id': self.care_plan_id,
            'patient_id': self.patient_id,
            'order_type': self.order_type,
            'order_category': self.order_category,
            'order_text': self.order_text,
            'ordering_physician': self.ordering_physician,
            'physician_npi': self.physician_npi,
            'physician_phone': self.physician_phone,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'frequency': self.frequency,
            'duration': self.duration,
            'prn_indication': self.prn_indication,
            'status': self.status,
            'verification_status': self.verification_status,
            'verified_by_user_id': self.verified_by_user_id,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'assigned_to_user_id': self.assigned_to_user_id,
            'priority': self.priority,
            'special_instructions': self.special_instructions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class AssistanceTask(db.Model):
    """Tasks performed by CNAs, HHAs, and other caregivers - ADLs, comfort care, etc."""
    
    __tablename__ = 'assistance_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    care_plan_id = db.Column(db.Integer, db.ForeignKey('care_plans.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    
    # Task details
    task_category = db.Column(db.String(50), nullable=False, index=True)  # adl, meal, hygiene, mobility, comfort, etc.
    task_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Specific ADL details
    adl_type = db.Column(db.String(50))  # bathing, dressing, toileting, feeding, transferring, ambulation
    assistance_level = db.Column(db.String(50))  # independent, supervision, minimal_assist, moderate_assist, maximum_assist, total_care
    
    # Scheduling
    frequency = db.Column(db.String(100), nullable=False)  # Daily, BID, TID, QID, PRN, etc.
    frequency_times_per_day = db.Column(db.Integer)
    scheduled_times = db.Column(Text)  # JSON array ["08:00", "12:00", "18:00"]
    estimated_duration_minutes = db.Column(db.Integer)  # How long task typically takes
    
    # Dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    
    # Assignment
    assigned_role = db.Column(db.String(20), nullable=False)  # CNA, HHA, Family, etc.
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Specific assignment
    requires_two_person_assist = db.Column(db.Boolean, default=False)  # Safety requirement
    
    # Status
    status = db.Column(db.String(20), default='active', index=True)  # active, completed, discontinued
    priority = db.Column(db.String(20), default='routine')
    
    # Safety and equipment
    equipment_needed = db.Column(Text)  # JSON array of equipment (walker, gait belt, shower chair, etc.)
    safety_precautions = db.Column(db.Text)
    fall_risk_precautions = db.Column(db.Boolean, default=False)
    
    # Patient preferences
    patient_preferences = db.Column(db.Text)  # How patient prefers task to be done
    cultural_considerations = db.Column(db.Text)
    
    # Documentation
    requires_documentation = db.Column(db.Boolean, default=True)
    documentation_notes = db.Column(db.Text)  # What to document
    
    # Metadata
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    discontinued_at = db.Column(db.DateTime)
    discontinued_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    discontinued_reason = db.Column(db.Text)
    
    # Relationships
    patient = db.relationship('Patient', backref='assistance_tasks')
    completions = db.relationship('TaskCompletion', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'care_plan_id': self.care_plan_id,
            'patient_id': self.patient_id,
            'task_category': self.task_category,
            'task_name': self.task_name,
            'description': self.description,
            'adl_type': self.adl_type,
            'assistance_level': self.assistance_level,
            'frequency': self.frequency,
            'frequency_times_per_day': self.frequency_times_per_day,
            'scheduled_times': self.scheduled_times,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'assigned_role': self.assigned_role,
            'assigned_user_id': self.assigned_user_id,
            'requires_two_person_assist': self.requires_two_person_assist,
            'status': self.status,
            'priority': self.priority,
            'equipment_needed': self.equipment_needed,
            'safety_precautions': self.safety_precautions,
            'fall_risk_precautions': self.fall_risk_precautions,
            'patient_preferences': self.patient_preferences,
            'requires_documentation': self.requires_documentation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class InterventionCompletion(db.Model):
    """Documentation of completed nursing interventions."""
    
    __tablename__ = 'intervention_completions'
    
    id = db.Column(db.Integer, primary_key=True)
    intervention_id = db.Column(db.Integer, db.ForeignKey('nursing_interventions.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    
    # Completion details
    completed_at = db.Column(db.DateTime, nullable=False)
    completed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Documentation
    status = db.Column(db.String(20), nullable=False)  # completed, partially_completed, not_done, refused
    completion_notes = db.Column(db.Text, nullable=False)
    patient_response = db.Column(db.Text)  # How patient responded to intervention
    outcome_achieved = db.Column(db.Boolean)  # Did we meet expected outcome?
    outcome_notes = db.Column(db.Text)
    
    # If not completed
    reason_not_done = db.Column(db.Text)  # Why intervention wasn't performed
    
    # Time tracking
    duration_minutes = db.Column(db.Integer)  # How long it took
    
    # Follow-up
    requires_follow_up = db.Column(db.Boolean, default=False)
    follow_up_notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient')
    
    def to_dict(self):
        return {
            'id': self.id,
            'intervention_id': self.intervention_id,
            'patient_id': self.patient_id,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by_user_id': self.completed_by_user_id,
            'status': self.status,
            'completion_notes': self.completion_notes,
            'patient_response': self.patient_response,
            'outcome_achieved': self.outcome_achieved,
            'outcome_notes': self.outcome_notes,
            'reason_not_done': self.reason_not_done,
            'duration_minutes': self.duration_minutes,
            'requires_follow_up': self.requires_follow_up,
            'follow_up_notes': self.follow_up_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class OrderCompletion(db.Model):
    """Documentation of physician order completion/implementation."""
    
    __tablename__ = 'order_completions'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('physician_orders.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    
    # Completion details
    completed_at = db.Column(db.DateTime, nullable=False)
    completed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Documentation
    status = db.Column(db.String(20), nullable=False)  # completed, in_progress, cancelled, refused
    completion_notes = db.Column(db.Text, nullable=False)
    results = db.Column(db.Text)  # Results of test, outcome of treatment, etc.
    
    # If not completed
    reason_not_done = db.Column(db.Text)
    
    # Follow-up
    requires_follow_up = db.Column(db.Boolean, default=False)
    follow_up_notes = db.Column(db.Text)
    physician_notified = db.Column(db.Boolean, default=False)
    notification_notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'patient_id': self.patient_id,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by_user_id': self.completed_by_user_id,
            'status': self.status,
            'completion_notes': self.completion_notes,
            'results': self.results,
            'reason_not_done': self.reason_not_done,
            'requires_follow_up': self.requires_follow_up,
            'follow_up_notes': self.follow_up_notes,
            'physician_notified': self.physician_notified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TaskCompletion(db.Model):
    """Documentation of completed assistance tasks (ADLs, etc.)."""
    
    __tablename__ = 'task_completions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('assistance_tasks.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    
    # Completion details
    completed_at = db.Column(db.DateTime, nullable=False)
    completed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assisted_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # If two-person assist
    
    # Documentation
    status = db.Column(db.String(20), nullable=False)  # completed, partially_completed, not_done, refused
    completion_notes = db.Column(db.Text)
    
    # Patient tolerance
    patient_tolerance = db.Column(db.String(50))  # well_tolerated, some_difficulty, poor_tolerance
    patient_participation = db.Column(db.String(50))  # independent, cooperative, resistive, unable
    
    # Safety
    safety_incidents = db.Column(db.Boolean, default=False)
    incident_notes = db.Column(db.Text)
    
    # If not completed
    reason_not_done = db.Column(db.Text)
    
    # Time tracking
    duration_minutes = db.Column(db.Integer)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'patient_id': self.patient_id,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by_user_id': self.completed_by_user_id,
            'assisted_by_user_id': self.assisted_by_user_id,
            'status': self.status,
            'completion_notes': self.completion_notes,
            'patient_tolerance': self.patient_tolerance,
            'patient_participation': self.patient_participation,
            'safety_incidents': self.safety_incidents,
            'incident_notes': self.incident_notes,
            'reason_not_done': self.reason_not_done,
            'duration_minutes': self.duration_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
