"""Patient safety alert system for all staff (including unlicensed).

This module provides privacy-preserving safety alerts that notify ALL staff members
about patient safety concerns without exposing medication details or PHI unnecessarily.
Designed to empower CNAs, HHAs, and other unlicensed staff to be extra vigilant
about fall risks, orthostatic hypotension, and other observable safety issues.
"""
from datetime import datetime, timedelta
from app import db
from sqlalchemy import JSON


class PatientSafetyAlert(db.Model):
    """General patient safety alerts visible to all staff.
    
    These alerts are intentionally vague about medical details but specific about
    what to watch for and when to escalate. They're designed to:
    1. Protect patient privacy (no medication names unless necessary)
    2. Empower unlicensed staff to be vigilant
    3. Provide clear guidance on what to do
    4. Integrate seamlessly with daily care activities
    """
    
    __tablename__ = 'patient_safety_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    
    # Alert Classification
    alert_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: 'FALL_RISK', 'ORTHOSTATIC_HYPOTENSION', 'DIZZINESS_RISK', 
    #        'BLEEDING_RISK', 'CARDIAC_CONCERN', 'NEURO_CONCERN', 'GI_CONCERN'
    
    severity = db.Column(db.String(20), default='MODERATE')  # LOW, MODERATE, HIGH, CRITICAL
    
    # Privacy-Preserving Details
    alert_title = db.Column(db.String(200), nullable=False)  # e.g., "Extra Fall Risk - Use Assist"
    what_to_watch = db.Column(db.Text, nullable=False)  # Observable symptoms/behaviors
    when_to_notify = db.Column(db.Text, nullable=False)  # Escalation criteria
    safety_precautions = db.Column(JSON)  # List of specific actions to take
    
    # Vital Signs Triggers
    trigger_on_low_bp = db.Column(db.Boolean, default=False)  # Alert if systolic < threshold
    bp_systolic_threshold = db.Column(db.Integer)  # e.g., 100
    trigger_on_low_hr = db.Column(db.Boolean, default=False)  # Alert if HR < threshold
    hr_threshold = db.Column(db.Integer)  # e.g., 60
    trigger_on_high_hr = db.Column(db.Boolean, default=False)  # Alert if HR > threshold
    hr_high_threshold = db.Column(db.Integer)  # e.g., 100
    
    # Positional Assessment Required
    requires_orthostatic_vitals = db.Column(db.Boolean, default=False)
    # If True, prompt for sitting AND standing BP/HR when collecting vitals
    
    # Source Tracking (for licensed staff context)
    source_type = db.Column(db.String(50))  # 'ADR_ALERT', 'MEDICATION', 'DIAGNOSIS', 'MANUAL'
    source_id = db.Column(db.Integer)  # ID of source (e.g., adr_alert_id, medication_id)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Lifecycle
    active = db.Column(db.Boolean, default=True, index=True)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    resolved_at = db.Column(db.DateTime)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolution_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient')
    facility = db.relationship('Facility')
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_user_id])
    
    @property
    def is_expired(self):
        """Check if alert has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self):
        """Check if alert is currently active."""
        return self.active and not self.is_expired and not self.resolved_at
    
    def to_dict(self, include_source=False):
        """Convert to dictionary for API responses.
        
        Args:
            include_source: If True, include source details (for licensed staff only)
        """
        data = {
            'id': self.id,
            'patient_id': self.patient_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'alert_title': self.alert_title,
            'what_to_watch': self.what_to_watch,
            'when_to_notify': self.when_to_notify,
            'safety_precautions': self.safety_precautions or [],
            'trigger_on_low_bp': self.trigger_on_low_bp,
            'bp_systolic_threshold': self.bp_systolic_threshold,
            'trigger_on_low_hr': self.trigger_on_low_hr,
            'hr_threshold': self.hr_threshold,
            'trigger_on_high_hr': self.trigger_on_high_hr,
            'hr_high_threshold': self.hr_high_threshold,
            'requires_orthostatic_vitals': self.requires_orthostatic_vitals,
            'active': self.active,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
        }
        
        if include_source:
            data['source_type'] = self.source_type
            data['source_id'] = self.source_id
            data['resolved_at'] = self.resolved_at.isoformat() if self.resolved_at else None
            data['resolution_notes'] = self.resolution_notes
        
        return data
    
    def __repr__(self):
        return f'<PatientSafetyAlert {self.id}: {self.alert_type} - {self.patient_id}>'


class StaffSafetyAlertAcknowledgment(db.Model):
    """Track which staff members have seen safety alerts.
    
    Unlike ADR acknowledgments (which verify medical understanding),
    these acknowledgments just confirm the staff member has been notified
    and knows what to watch for.
    """
    
    __tablename__ = 'staff_safety_alert_acknowledgments'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('patient_safety_alerts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    
    # Acknowledgment
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_via = db.Column(db.String(50))  # 'LOGIN_PROMPT', 'VITAL_SIGNS', 'PATIENT_ASSIGNMENT'
    
    # Optional notes
    notes = db.Column(db.Text)
    
    # Relationships
    alert = db.relationship('PatientSafetyAlert')
    user = db.relationship('User')
    facility = db.relationship('Facility')
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'acknowledged_at': self.acknowledged_at.isoformat(),
            'acknowledged_via': self.acknowledged_via,
            'notes': self.notes,
        }
    
    def __repr__(self):
        return f'<StaffSafetyAlertAck {self.id}: Alert {self.alert_id} by User {self.user_id}>'


def create_safety_alert_from_adr(adr_alert, created_by_user_id):
    """Create a privacy-preserving safety alert from an ADR alert.
    
    This function translates detailed ADR alerts (with medication names, etc.)
    into general safety alerts appropriate for unlicensed staff.
    
    Args:
        adr_alert: ADRAlert object
        created_by_user_id: User ID creating the safety alert (usually RN)
    
    Returns:
        PatientSafetyAlert object
    """
    from app.models import Medication
    
    # Get medication to determine alert type
    medication = Medication.query.get(adr_alert.medication_id)
    med_name_lower = medication.medication_name.lower() if medication else ''
    
    # Initialize variables
    trigger_on_low_bp = False
    trigger_on_low_hr = False
    trigger_on_high_hr = False
    bp_systolic_threshold = None
    hr_threshold = None
    hr_high_threshold = None
    requires_orthostatic = False
    
    # Determine alert type and content based on ADR type
    if 'digoxin' in adr_alert.suspected_reaction.lower() or 'digoxin' in med_name_lower:
        alert_type = 'CARDIAC_CONCERN'
        alert_title = 'Monitor for Dizziness and Heart Rhythm'
        what_to_watch = (
            '• Complaints of dizziness or lightheadedness\n'
            '• Visual changes (seeing halos, colors looking different)\n'
            '• Nausea, vomiting, or loss of appetite\n'
            '• Confusion or unusual tiredness\n'
            '• Slow or irregular pulse (you may notice this during care)'
        )
        when_to_notify = (
            'NOTIFY RN IMMEDIATELY if client:\n'
            '• Complains of seeing yellow-green halos around lights\n'
            '• Is very dizzy or unsteady when standing\n'
            '• Has persistent nausea/vomiting\n'
            '• Seems confused or much more tired than usual\n'
            '• Pulse feels very slow or irregular'
        )
        safety_precautions = [
            'Use assist for all transfers',
            'Do not leave client unattended when standing',
            'Report any dizziness immediately',
            'Check on client frequently',
        ]
        trigger_on_low_hr = True
        hr_threshold = 60
        requires_orthostatic = True
        
    elif any(term in adr_alert.suspected_reaction.lower() for term in ['anticoagulant', 'bleeding', 'warfarin', 'heparin']):
        alert_type = 'BLEEDING_RISK'
        alert_title = 'Monitor for Bleeding or Bruising'
        what_to_watch = (
            '• New or worsening bruises\n'
            '• Any bleeding that won\'t stop (gums, nose, cuts)\n'
            '• Blood in urine or stool (dark, tarry stool)\n'
            '• Coughing up blood\n'
            '• Severe headache or dizziness'
        )
        when_to_notify = (
            'NOTIFY RN IMMEDIATELY if client has:\n'
            '• Any active bleeding\n'
            '• Large or spreading bruises\n'
            '• Blood in urine or dark/tarry stools\n'
            '• Severe headache\n'
            '• Fall or injury (even if seems minor)'
        )
        safety_precautions = [
            'Use soft toothbrush',
            'Avoid rough handling during transfers',
            'Report all falls immediately',
            'Check for bruising during care',
        ]
        trigger_on_low_bp = True
        bp_systolic_threshold = 90
        hr_threshold = None
        requires_orthostatic = False
        
    elif any(term in adr_alert.suspected_reaction.lower() for term in ['hypotension', 'blood pressure', 'bp']):
        alert_type = 'ORTHOSTATIC_HYPOTENSION'
        alert_title = 'High Risk for Dizziness When Standing'
        what_to_watch = (
            '• Dizziness or lightheadedness, especially when standing\n'
            '• Unsteady gait\n'
            '• Complaints of feeling faint\n'
            '• Appears pale or sweaty\n'
            '• Weakness in legs'
        )
        when_to_notify = (
            'NOTIFY RN IMMEDIATELY if client:\n'
            '• Becomes dizzy and unsteady when you help them stand\n'
            '• Nearly faints or needs to sit back down quickly\n'
            '• Has any fall or near-fall\n'
            '• Complains of persistent dizziness'
        )
        safety_precautions = [
            'ALWAYS use two-person assist for transfers',
            'Have client sit on edge of bed for 30 seconds before standing',
            'Ask "Are you dizzy?" before each transfer',
            'Move slowly - no rushing',
            'Keep call bell within reach at all times',
        ]
        trigger_on_low_bp = True
        bp_systolic_threshold = 100
        requires_orthostatic = True
        hr_threshold = None
        
    else:
        # Generic alert for other ADRs
        alert_type = 'FALL_RISK'
        alert_title = 'Monitor for Changes in Condition'
        what_to_watch = (
            '• Any changes in behavior or mood\n'
            '• New complaints of not feeling well\n'
            '• Dizziness or unsteadiness\n'
            '• Confusion or drowsiness\n'
            '• Any new symptoms'
        )
        when_to_notify = (
            'NOTIFY RN if client:\n'
            '• Has any concerning symptoms\n'
            '• Seems "not themselves"\n'
            '• Refuses care or seems upset\n'
            '• Has any fall or near-fall'
        )
        safety_precautions = [
            'Use assist for transfers',
            'Monitor closely during care',
            'Report changes promptly',
        ]
        trigger_on_low_bp = False
        bp_systolic_threshold = None
        hr_threshold = None
        requires_orthostatic = False
    
    # Create the safety alert
    safety_alert = PatientSafetyAlert(
        patient_id=adr_alert.patient_id,
        facility_id=adr_alert.facility_id,
        alert_type=alert_type,
        severity=adr_alert.severity,
        alert_title=alert_title,
        what_to_watch=what_to_watch,
        when_to_notify=when_to_notify,
        safety_precautions=safety_precautions,
        trigger_on_low_bp=trigger_on_low_bp,
        bp_systolic_threshold=bp_systolic_threshold,
        trigger_on_low_hr=trigger_on_low_hr,
        hr_threshold=hr_threshold,
        requires_orthostatic_vitals=requires_orthostatic,
        source_type='ADR_ALERT',
        source_id=adr_alert.id,
        created_by_user_id=created_by_user_id,
        active=True,
    )
    
    return safety_alert
