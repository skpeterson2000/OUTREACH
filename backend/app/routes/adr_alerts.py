"""ADR (Adverse Drug Reaction) alert routes - surveillance and monitoring."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from app import db
from app.models import (
    ADRAlert, PatientObservation, Patient, User, Medication,
    PharmacistIntervention, AuditLog
)
from app.services.adr_surveillance import ADRSurveillanceService
from app.utils.permissions import require_role

bp = Blueprint('adr_alerts', __name__, url_prefix='/api')


@bp.route('/patients/<int:patient_id>/observations', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'CNA', 'Admin'])
def create_observation(patient_id):
    """
    Document patient observation.
    
    This automatically triggers ADR surveillance.
    
    Request body:
    {
        "observation_type": "SYMPTOM",
        "observation_category": "GI",
        "observation_text": "Patient reports nausea, vomited x2 this shift",
        "standardized_terms": ["nausea", "vomiting"],
        "severity_rating": 6,
        "patient_reported": true,
        "observation_datetime": "2025-11-20T14:00:00Z",
        "related_vital_signs": {
            "blood_pressure": "118/72",
            "heart_rate": 88
        }
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check patient access
    patient = Patient.query.get_or_404(patient_id)
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('observation_type'):
        return jsonify({'error': 'observation_type is required'}), 400
    
    valid_types = [
        'SYMPTOM', 'VITAL_SIGN', 'BEHAVIOR', 
        'PHYSICAL_FINDING', 'LAB_RESULT', 'FUNCTIONAL_CHANGE'
    ]
    if data['observation_type'] not in valid_types:
        return jsonify({'error': f'observation_type must be one of: {", ".join(valid_types)}'}), 400
    
    if not data.get('observation_text'):
        return jsonify({'error': 'observation_text is required'}), 400
    
    try:
        # Get patient's current medications for related_medications field
        active_meds = Medication.query.filter_by(
            patient_id=patient_id,
            status='active'
        ).all()
        
        related_meds = [{'id': med.id, 'name': med.name, 'dose': med.dose} for med in active_meds]
        
        # Parse observation datetime
        obs_datetime = data.get('observation_datetime')
        if obs_datetime:
            obs_datetime = datetime.fromisoformat(obs_datetime.replace('Z', '+00:00'))
        else:
            obs_datetime = datetime.utcnow()
        
        # Create observation
        observation = PatientObservation(
            patient_id=patient_id,
            facility_id=patient.facility_id,
            observed_by_user_id=current_user_id,
            observation_type=data['observation_type'],
            observation_category=data.get('observation_category'),
            observation_text=data['observation_text'],
            standardized_terms=data.get('standardized_terms', []),
            severity_rating=data.get('severity_rating'),
            patient_reported=data.get('patient_reported', False),
            observation_datetime=obs_datetime,
            related_vital_signs=data.get('related_vital_signs'),
            related_medications=related_meds
        )
        
        db.session.add(observation)
        db.session.flush()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='PatientObservation',
            resource_id=observation.id,
            details=f'Observation documented: {data["observation_type"]} - {data["observation_text"][:50]}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        # Trigger ADR surveillance (asynchronously in production)
        alerts = ADRSurveillanceService.analyze_observation(observation.id)
        
        return jsonify({
            'status': 'success',
            'data': observation.to_dict(include_alerts=True),
            'adr_alerts_generated': len(alerts),
            'message': f'Observation documented. {len(alerts)} ADR alert(s) generated.' if alerts else 'Observation documented.'
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/patients/<int:patient_id>/observations', methods=['GET'])
@jwt_required()
def get_patient_observations(patient_id):
    """
    Get patient observations.
    
    Query params:
    - days: Number of days to look back (default 7)
    - type: Filter by observation type
    - with_alerts: Only observations that generated alerts
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check patient access
    patient = Patient.query.get_or_404(patient_id)
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Parse filters
    days = int(request.args.get('days', 7))
    obs_type = request.args.get('type')
    with_alerts = request.args.get('with_alerts', 'false').lower() == 'true'
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = PatientObservation.query.filter(
        and_(
            PatientObservation.patient_id == patient_id,
            PatientObservation.observation_datetime >= cutoff_date
        )
    )
    
    if obs_type:
        query = query.filter_by(observation_type=obs_type)
    
    if with_alerts:
        query = query.filter_by(potential_adr_detected=True)
    
    observations = query.order_by(PatientObservation.observation_datetime.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': [obs.to_dict(include_alerts=with_alerts) for obs in observations],
        'count': len(observations)
    })


@bp.route('/adr-alerts', methods=['GET'])
@jwt_required()
def get_adr_alerts():
    """
    Get ADR alerts for facility.
    
    Query params:
    - status: Filter by status (NEW, ACKNOWLEDGED, INVESTIGATING, etc.)
    - severity: Filter by severity
    - confidence: Minimum confidence level
    - patient_id: Filter by patient
    - days: Look back days (default 7)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Parse filters
    status = request.args.get('status')
    severity = request.args.get('severity')
    confidence = request.args.get('confidence')
    patient_id = request.args.get('patient_id')
    days = int(request.args.get('days', 7))
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query - filter by facility
    query = ADRAlert.query.filter(
        and_(
            ADRAlert.facility_id == user.facility_id,
            ADRAlert.created_at >= cutoff_date
        )
    )
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    else:
        # By default, show active alerts
        query = query.filter(
            ADRAlert.status.in_(['NEW', 'ACKNOWLEDGED', 'INVESTIGATING'])
        )
    
    if severity:
        query = query.filter_by(severity=severity)
    
    if confidence:
        query = query.filter_by(confidence_level=confidence)
    
    if patient_id:
        query = query.filter_by(patient_id=int(patient_id))
    
    # Order by urgency
    urgency_order = db.case(
        (ADRAlert.provider_notification_urgency == 'STAT', 1),
        (ADRAlert.provider_notification_urgency == 'URGENT', 2),
        (ADRAlert.provider_notification_urgency == 'ROUTINE', 3),
        else_=4
    )
    
    alerts = query.order_by(
        urgency_order,
        ADRAlert.created_at.desc()
    ).all()
    
    # Enrich with patient info
    result = []
    for alert in alerts:
        alert_dict = alert.to_dict()
        patient = Patient.query.get(alert.patient_id)
        alert_dict['patient_name'] = f"{patient.first_name} {patient.last_name}"
        alert_dict['patient_room'] = getattr(patient, 'room_number', None)
        result.append(alert_dict)
    
    # Audit log
    AuditLog.log_access(
        user_id=current_user_id,
        action='ACCESS',
        resource_type='ADRAlert',
        resource_id=None,
        details=f'Viewed ADR alerts dashboard',
        contains_phi=False,
        facility_id=user.facility_id
    )
    
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result),
        'filters': {
            'status': status,
            'severity': severity,
            'confidence': confidence,
            'patient_id': patient_id,
            'days': days
        }
    })


@bp.route('/patients/<int:patient_id>/adr-alerts', methods=['GET'])
@jwt_required()
def get_patient_adr_alerts(patient_id):
    """Get ADR alerts for specific patient."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check patient access
    patient = Patient.query.get_or_404(patient_id)
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Parse filters
    status = request.args.get('status')
    days = int(request.args.get('days', 30))
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = ADRAlert.query.filter(
        and_(
            ADRAlert.patient_id == patient_id,
            ADRAlert.created_at >= cutoff_date
        )
    )
    
    if status:
        query = query.filter_by(status=status)
    
    alerts = query.order_by(ADRAlert.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': [alert.to_dict() for alert in alerts],
        'count': len(alerts),
        'patient_id': patient_id
    })


@bp.route('/adr-alerts/<int:alert_id>', methods=['GET'])
@jwt_required()
def get_adr_alert_details(alert_id):
    """Get detailed information about specific ADR alert."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    alert = ADRAlert.query.get_or_404(alert_id)
    
    # Check access
    if alert.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Enrich with related data
    result = alert.to_dict()
    
    # Add patient info
    patient = Patient.query.get(alert.patient_id)
    result['patient'] = {
        'id': patient.id,
        'name': f"{patient.first_name} {patient.last_name}",
        'room': getattr(patient, 'room_number', None),
        'is_hospice': patient.is_hospice
    }
    
    # Add medication info
    medication = Medication.query.get(alert.medication_id)
    result['medication'] = medication.to_dict()
    
    # Add observation info
    observation = PatientObservation.query.get(alert.observation_id)
    result['observation'] = observation.to_dict()
    
    # Add pharmacist intervention if exists
    if alert.pharmacist_intervention_id:
        intervention = PharmacistIntervention.query.get(alert.pharmacist_intervention_id)
        result['pharmacist_intervention'] = intervention.to_dict()
    
    return jsonify({
        'status': 'success',
        'data': result
    })


@bp.route('/adr-alerts/<int:alert_id>/acknowledge', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'TMA', 'Admin'])  # TMA can acknowledge alerts for meds they administer
def acknowledge_alert(alert_id):
    """
    Acknowledge ADR alert (multi-user, shift-based).
    
    Each staff member must independently acknowledge each active alert.
    Acknowledgments expire after 12 hours (shift change).
    
    Request body:
    {
        "action": "ACKNOWLEDGED" or "HOLD_MEDICATION",
        "verified_reaction_awareness": true,
        "verified_monitoring_parameters": true,
        "verified_escalation_criteria": true,
        "notes": "Aware of alert, monitoring patient closely...",
        "monitoring_plan": "Will check BP q4h, observe for confusion",
        
        // If action = "HOLD_MEDICATION":
        "hold_reason": "Patient symptomatic, medication may be contributing",
        "hold_duration": "24 hours or until symptoms resolve",
        "provider_notified": true,
        "provider_notified_at": "2025-11-21T14:30:00",
        "hold_order_obtained": true
    }
    """
    from app.models import ADRAlertAcknowledgment
    from flask import current_app
    import logging
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    current_app.logger.info(f"🔔 ADR ALERT ACKNOWLEDGMENT | Alert #{alert_id} | User: {user.username} ({user.role})")
    
    alert = ADRAlert.query.get_or_404(alert_id)
    current_app.logger.info(f"   Alert: {alert.alert_type} - {alert.severity} | Status: {alert.status} | Patient: {alert.patient_id}")
    
    # Check access
    if alert.facility_id != user.facility_id and user.role != 'Admin':
        current_app.logger.warning(f"   ❌ Access denied - facility mismatch")
        return jsonify({'error': 'Access denied'}), 403
    
    if not alert.is_active:
        current_app.logger.warning(f"   ❌ Cannot acknowledge - alert not active: {alert.status}")
        return jsonify({'error': f'Alert is not active (status: {alert.status})'}), 400
    
    data = request.get_json() or {}
    current_app.logger.info(f"   Acknowledgment action: {data.get('action', 'ACKNOWLEDGED')}")
    
    # Validate required fields
    action = data.get('action', 'ACKNOWLEDGED')
    if action not in ['ACKNOWLEDGED', 'HOLD_MEDICATION']:
        return jsonify({'error': 'Invalid action. Must be ACKNOWLEDGED or HOLD_MEDICATION'}), 400
    
    # Require all three safety verifications
    if not all([
        data.get('verified_reaction_awareness'),
        data.get('verified_monitoring_parameters'),
        data.get('verified_escalation_criteria')
    ]):
        return jsonify({
            'error': 'All safety verifications required',
            'message': 'You must verify reaction awareness, monitoring parameters, and escalation criteria'
        }), 400
    
    # If holding medication, require additional fields
    if action == 'HOLD_MEDICATION':
        if not data.get('hold_reason'):
            return jsonify({'error': 'hold_reason required when holding medication'}), 400
        if not data.get('provider_notified'):
            return jsonify({'error': 'Provider must be notified when holding medication'}), 400
    
    try:
        # Check for existing valid acknowledgment by this user
        existing = ADRAlertAcknowledgment.query.filter_by(
            alert_id=alert_id,
            user_id=current_user_id
        ).order_by(ADRAlertAcknowledgment.acknowledged_at.desc()).first()
        
        if existing and existing.is_valid:
            print(f"   ℹ️ User already has valid acknowledgment (expires: {existing.expires_at})")
            return jsonify({
                'status': 'success',
                'data': existing.to_dict(),
                'message': f'You have already acknowledged this alert (valid until {existing.expires_at.strftime("%H:%M")})',
                'already_acknowledged': True
            })
        
        # Create new acknowledgment
        acknowledgment = ADRAlertAcknowledgment(
            alert_id=alert_id,
            user_id=current_user_id,
            facility_id=user.facility_id,
            action_taken=action,
            acknowledged_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=12),  # Expires after shift
            verified_reaction_awareness=data.get('verified_reaction_awareness', False),
            verified_monitoring_parameters=data.get('verified_monitoring_parameters', False),
            verified_escalation_criteria=data.get('verified_escalation_criteria', False),
            notes=data.get('notes'),
            monitoring_plan=data.get('monitoring_plan')
        )
        
        # If holding medication
        if action == 'HOLD_MEDICATION':
            acknowledgment.hold_reason = data.get('hold_reason')
            acknowledgment.hold_duration = data.get('hold_duration')
            acknowledgment.provider_notified = data.get('provider_notified', False)
            if data.get('provider_notified_at'):
                acknowledgment.provider_notified_at = datetime.fromisoformat(data['provider_notified_at'].replace('Z', '+00:00'))
            acknowledgment.hold_order_obtained = data.get('hold_order_obtained', False)
        
        db.session.add(acknowledgment)
        
        # Update alert status if first acknowledgment
        if alert.status == 'NEW':
            alert.status = 'ACKNOWLEDGED'
            alert.acknowledged_by_user_id = current_user_id
            alert.acknowledged_at = datetime.utcnow()
        
        # Audit log
        AuditLog.log_action(
            user=user,
            action='CREATE',
            resource_type='ADRAlertAcknowledgment',
            resource_id=acknowledgment.id,
            patient_id=alert.patient_id,
            description=f'{action} ADR alert #{alert_id} for patient {alert.patient_id}',
            phi_accessed=True,
            request=request
        )
        
        db.session.commit()
        
        current_app.logger.info(f"   ✅ ACKNOWLEDGMENT CREATED | ID: {acknowledgment.id} | Expires: {acknowledgment.expires_at.strftime('%Y-%m-%d %H:%M')}")
        user_logger = logging.getLogger('user_actions')
        user_logger.info(f"ADR ALERT ACKNOWLEDGED | User: {user.username} | Alert: #{alert_id} | Action: {action} | Patient: {alert.patient_id}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'acknowledgment': acknowledgment.to_dict(),
                'alert': alert.to_dict()
            },
            'message': f'Alert {action.lower().replace("_", " ")} successfully. Valid until shift end.'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"   ❌ ERROR: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/adr-alerts/<int:alert_id>/escalate-pharmacist', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def escalate_to_pharmacist(alert_id):
    """
    Escalate ADR alert to pharmacist for clinical review.
    
    Request body:
    {
        "escalation_notes": "Patient symptoms worsening, requesting pharmacist review"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    alert = ADRAlert.query.get_or_404(alert_id)
    
    # Check access
    if alert.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json() or {}
    
    try:
        # Create pharmacist intervention
        intervention = PharmacistIntervention(
            patient_id=alert.patient_id,
            facility_id=alert.facility_id,
            medication_id=alert.medication_id,
            intervention_type='ADR_EVALUATION',
            severity='URGENT' if alert.provider_notification_urgency == 'STAT' else 'MODERATE',
            clinical_concern=alert.alert_summary,
            recommendation='Evaluate potential adverse drug reaction',
            clinical_rationale=f"ADR alert escalated. Correlation score: {alert.correlation_score}. Matching symptoms: {', '.join(alert.matching_symptoms)}",
            initiated_by_user_id=current_user_id
        )
        
        db.session.add(intervention)
        db.session.flush()
        
        # Link intervention to alert
        alert.pharmacist_consulted = True
        alert.pharmacist_intervention_id = intervention.id
        alert.status = 'INVESTIGATING'
        
        if data.get('escalation_notes'):
            alert.escalation_guidance = data['escalation_notes']
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='PharmacistIntervention',
            resource_id=intervention.id,
            details=f'Escalated ADR alert {alert_id} to pharmacist',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': {
                'alert': alert.to_dict(),
                'intervention': intervention.to_dict()
            },
            'message': 'Alert escalated to pharmacist'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/adr-alerts/<int:alert_id>/notify-provider', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def notify_provider(alert_id):
    """
    Mark that provider has been notified about ADR alert.
    
    Request body:
    {
        "notification_method": "Phone call",
        "provider_name": "Dr. Smith",
        "provider_response": "Will evaluate patient, may discontinue medication"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    alert = ADRAlert.query.get_or_404(alert_id)
    
    # Check access
    if alert.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json() or {}
    
    try:
        alert.provider_notified = True
        alert.provider_notified_at = datetime.utcnow()
        alert.provider_response = data.get('provider_response')
        
        # Update investigation notes
        notification_note = f"\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Provider notified via {data.get('notification_method', 'unspecified')}. "
        if data.get('provider_name'):
            notification_note += f"Provider: {data['provider_name']}. "
        if data.get('provider_response'):
            notification_note += f"Response: {data['provider_response']}"
        
        if alert.investigation_notes:
            alert.investigation_notes += notification_note
        else:
            alert.investigation_notes = notification_note
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='ADRAlert',
            resource_id=alert.id,
            details=f'Notified provider about ADR alert for patient {alert.patient_id}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': alert.to_dict(),
            'message': 'Provider notification documented'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/adr-alerts/check-patient-acknowledgments/<int:patient_id>', methods=['GET'])
@jwt_required()
@require_role(['RN', 'LPN', 'TMA', 'Admin'])
def check_patient_acknowledgments(patient_id):
    """
    Check if current user has acknowledged all active ADR alerts for a patient.
    
    Must be called before administering medications to ensure staff awareness.
    Returns list of unacknowledged alerts (if any) and expired acknowledgments.
    """
    from app.models import ADRAlertAcknowledgment
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Get all active alerts for this patient
    active_alerts = ADRAlert.query.filter_by(
        patient_id=patient_id,
        facility_id=user.facility_id
    ).filter(
        ADRAlert.status.in_(['NEW', 'ACKNOWLEDGED', 'INVESTIGATING'])
    ).all()
    
    if not active_alerts:
        return jsonify({
            'status': 'success',
            'can_administer': True,
            'message': 'No active ADR alerts for this patient',
            'active_alerts': [],
            'unacknowledged_alerts': [],
            'expired_acknowledgments': []
        })
    
    # Check acknowledgments for each alert
    unacknowledged = []
    expired = []
    valid_acks = []
    
    for alert in active_alerts:
        # Get user's most recent acknowledgment
        ack = ADRAlertAcknowledgment.query.filter_by(
            alert_id=alert.id,
            user_id=current_user_id
        ).order_by(ADRAlertAcknowledgment.acknowledged_at.desc()).first()
        
        if not ack:
            unacknowledged.append(alert.to_dict())
        elif ack.is_expired:
            expired.append({
                'alert': alert.to_dict(),
                'expired_acknowledgment': ack.to_dict()
            })
        else:
            valid_acks.append(ack.to_dict())
    
    can_administer = len(unacknowledged) == 0 and len(expired) == 0
    
    return jsonify({
        'status': 'success',
        'can_administer': can_administer,
        'message': 'All alerts acknowledged' if can_administer else 'Some alerts require acknowledgment',
        'active_alerts': [a.to_dict() for a in active_alerts],
        'unacknowledged_alerts': unacknowledged,
        'expired_acknowledgments': expired,
        'valid_acknowledgments': valid_acks
    })


@bp.route('/adr-alerts/<int:alert_id>/resolve', methods=['POST'])
@jwt_required()
@require_role(['RN', 'Admin', 'Pharmacist'])
def resolve_alert(alert_id):
    """
    Resolve ADR alert with outcome.
    
    Request body:
    {
        "status": "CONFIRMED_ADR",
        "outcome_notes": "Vancomycin discontinued, symptoms resolved within 24 hours",
        "action_taken": "Medication discontinued per provider order, switched to alternative antibiotic"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    alert = ADRAlert.query.get_or_404(alert_id)
    
    # Check access
    if alert.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Validate status
    valid_final_statuses = ['CONFIRMED_ADR', 'NOT_ADR', 'DISMISSED']
    if not data.get('status') or data['status'] not in valid_final_statuses:
        return jsonify({
            'error': f'status must be one of: {", ".join(valid_final_statuses)}'
        }), 400
    
    if not data.get('outcome_notes'):
        return jsonify({'error': 'outcome_notes required when resolving alert'}), 400
    
    try:
        alert.status = data['status']
        alert.outcome = data['outcome_notes']
        alert.action_taken = data.get('action_taken')
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by_user_id = current_user_id
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='ADRAlert',
            resource_id=alert.id,
            details=f'Resolved ADR alert as {data["status"]} for patient {alert.patient_id}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': alert.to_dict(),
            'message': f'Alert resolved: {data["status"]}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
