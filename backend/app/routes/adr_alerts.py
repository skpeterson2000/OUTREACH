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
@require_role(['RN', 'LPN', 'Admin'])
def acknowledge_alert(alert_id):
    """
    Acknowledge ADR alert.
    
    Request body:
    {
        "notes": "Aware of alert, monitoring patient closely. Will notify provider if symptoms worsen."
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    alert = ADRAlert.query.get_or_404(alert_id)
    
    # Check access
    if alert.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    if alert.status not in ['NEW', 'ACKNOWLEDGED']:
        return jsonify({'error': f'Cannot acknowledge alert with status {alert.status}'}), 400
    
    data = request.get_json() or {}
    
    try:
        alert.status = 'ACKNOWLEDGED'
        alert.acknowledged_by_user_id = current_user_id
        alert.acknowledged_at = datetime.utcnow()
        
        if data.get('notes'):
            alert.investigation_notes = data['notes']
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='ADRAlert',
            resource_id=alert.id,
            details=f'Acknowledged ADR alert for patient {alert.patient_id}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': alert.to_dict(),
            'message': 'Alert acknowledged'
        })
        
    except Exception as e:
        db.session.rollback()
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
