"""Pharmacist collaboration routes - clinical messaging and interventions."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from app import db
from app.models import (
    PharmacistCollaboration, PharmacistCollaborationMessage,
    PharmacistIntervention, Patient, User, Medication,
    MedicationReconciliation, AuditLog
)
from app.utils.permissions import require_role

bp = Blueprint('pharmacist', __name__, url_prefix='/api')


@bp.route('/collaborations', methods=['GET'])
@jwt_required()
def get_collaborations():
    """
    Get collaboration threads.
    
    Query params:
    - status: Filter by status (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
    - priority: Filter by priority (ROUTINE, URGENT, STAT)
    - assigned_to_me: Show only threads assigned to current user (for pharmacists)
    - patient_id: Filter by patient
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Parse filters
    status = request.args.get('status')
    priority = request.args.get('priority')
    assigned_to_me = request.args.get('assigned_to_me', 'false').lower() == 'true'
    patient_id = request.args.get('patient_id')
    
    # Build query - filter by facility
    query = PharmacistCollaboration.query.filter_by(facility_id=user.facility_id)
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    else:
        # By default, show active threads
        query = query.filter(
            PharmacistCollaboration.status.in_(['OPEN', 'IN_PROGRESS'])
        )
    
    if priority:
        query = query.filter_by(priority=priority)
    
    if assigned_to_me and user.role == 'Pharmacist':
        query = query.filter_by(assigned_to_pharmacist_id=current_user_id)
    
    if patient_id:
        query = query.filter_by(patient_id=int(patient_id))
    
    # Order by priority and creation time
    priority_order = db.case(
        (PharmacistCollaboration.priority == 'STAT', 1),
        (PharmacistCollaboration.priority == 'URGENT', 2),
        (PharmacistCollaboration.priority == 'ROUTINE', 3),
        else_=4
    )
    
    collaborations = query.order_by(
        priority_order,
        PharmacistCollaboration.updated_at.desc()
    ).all()
    
    # Enrich with patient info
    result = []
    for collab in collaborations:
        collab_dict = collab.to_dict()
        patient = Patient.query.get(collab.patient_id)
        collab_dict['patient_name'] = f"{patient.first_name} {patient.last_name}"
        
        # Add creator info
        creator = User.query.get(collab.created_by_user_id)
        collab_dict['created_by_name'] = creator.full_name if creator else 'Unknown'
        
        # Add pharmacist info if assigned
        if collab.assigned_to_pharmacist_id:
            pharmacist = User.query.get(collab.assigned_to_pharmacist_id)
            collab_dict['assigned_pharmacist_name'] = pharmacist.full_name if pharmacist else 'Unknown'
        
        result.append(collab_dict)
    
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result),
        'filters': {
            'status': status,
            'priority': priority,
            'assigned_to_me': assigned_to_me
        }
    })


@bp.route('/collaborations', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin', 'Pharmacist'])
def create_collaboration():
    """
    Create new collaboration thread.
    
    Request body:
    {
        "patient_id": 1,
        "subject": "Warfarin dose clarification needed",
        "priority": "URGENT",
        "medication_id": 5,
        "initial_message": "Patient's INR is 4.5, current dose 5mg daily. Recommend dose adjustment?"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('patient_id'):
        return jsonify({'error': 'patient_id is required'}), 400
    
    if not data.get('subject'):
        return jsonify({'error': 'subject is required'}), 400
    
    if not data.get('initial_message'):
        return jsonify({'error': 'initial_message is required'}), 400
    
    # Check patient access
    patient = Patient.query.get_or_404(data['patient_id'])
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Validate priority
    valid_priorities = ['ROUTINE', 'URGENT', 'STAT']
    priority = data.get('priority', 'ROUTINE')
    if priority not in valid_priorities:
        return jsonify({'error': f'priority must be one of: {", ".join(valid_priorities)}'}), 400
    
    try:
        # Find available pharmacist (simplified - in production would use assignment logic)
        pharmacist = User.query.filter_by(
            facility_id=user.facility_id,
            role='Pharmacist',
            is_active=True
        ).first()
        
        # Create collaboration thread
        collaboration = PharmacistCollaboration(
            patient_id=data['patient_id'],
            facility_id=patient.facility_id,
            subject=data['subject'],
            priority=priority,
            status='OPEN',
            created_by_user_id=current_user_id,
            assigned_to_pharmacist_id=pharmacist.id if pharmacist else None,
            medication_id=data.get('medication_id'),
            reconciliation_id=data.get('reconciliation_id'),
            participants=[current_user_id] + ([pharmacist.id] if pharmacist else [])
        )
        
        db.session.add(collaboration)
        db.session.flush()
        
        # Create initial message
        message = PharmacistCollaborationMessage(
            collaboration_id=collaboration.id,
            author_user_id=current_user_id,
            message_type='QUESTION',
            message_text=data['initial_message']
        )
        
        db.session.add(message)
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='PharmacistCollaboration',
            resource_id=collaboration.id,
            details=f'Started collaboration: {data["subject"]}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': collaboration.to_dict(include_messages=True),
            'message': 'Collaboration thread created'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/collaborations/<int:collab_id>', methods=['GET'])
@jwt_required()
def get_collaboration_details(collab_id):
    """Get detailed collaboration thread with all messages."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    collaboration = PharmacistCollaboration.query.get_or_404(collab_id)
    
    # Check access
    if collaboration.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Enrich with full details
    result = collaboration.to_dict(include_messages=True)
    
    # Add patient info
    patient = Patient.query.get(collaboration.patient_id)
    result['patient'] = {
        'id': patient.id,
        'name': f"{patient.first_name} {patient.last_name}",
        'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None
    }
    
    # Add medication info if applicable
    if collaboration.medication_id:
        medication = Medication.query.get(collaboration.medication_id)
        result['medication'] = medication.to_dict() if medication else None
    
    # Add reconciliation info if applicable
    if collaboration.reconciliation_id:
        reconciliation = MedicationReconciliation.query.get(collaboration.reconciliation_id)
        result['reconciliation'] = reconciliation.to_dict() if reconciliation else None
    
    # Enrich messages with author names
    for msg in result['messages']:
        author = User.query.get(msg['author_user_id'])
        msg['author_name'] = author.full_name if author else 'Unknown'
        msg['author_role'] = author.role if author else 'Unknown'
    
    # Audit log
    AuditLog.log_access(
        user_id=current_user_id,
        action='ACCESS',
        resource_type='PharmacistCollaboration',
        resource_id=collab_id,
        details=f'Viewed collaboration thread',
        contains_phi=True,
        facility_id=user.facility_id
    )
    
    return jsonify({
        'status': 'success',
        'data': result
    })


@bp.route('/collaborations/<int:collab_id>/messages', methods=['POST'])
@jwt_required()
def add_message_to_collaboration(collab_id):
    """
    Add message to collaboration thread.
    
    Request body:
    {
        "message_type": "RESPONSE",
        "message_text": "Based on INR 4.5, recommend holding tonight's dose and rechecking INR in AM",
        "attachments": []
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    collaboration = PharmacistCollaboration.query.get_or_404(collab_id)
    
    # Check access
    if collaboration.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    if not data.get('message_text'):
        return jsonify({'error': 'message_text is required'}), 400
    
    # Validate message type
    valid_types = ['QUESTION', 'RESPONSE', 'RECOMMENDATION', 'ORDER_CHANGE', 'RESOLUTION', 'NOTE']
    message_type = data.get('message_type', 'NOTE')
    if message_type not in valid_types:
        return jsonify({'error': f'message_type must be one of: {", ".join(valid_types)}'}), 400
    
    try:
        # Create message
        message = PharmacistCollaborationMessage(
            collaboration_id=collab_id,
            author_user_id=current_user_id,
            message_type=message_type,
            message_text=data['message_text'],
            attachments=data.get('attachments', [])
        )
        
        db.session.add(message)
        
        # Update collaboration status and timestamp
        if collaboration.status == 'OPEN':
            collaboration.status = 'IN_PROGRESS'
        
        # Add user to participants if not already there
        if current_user_id not in collaboration.participants:
            collaboration.participants = collaboration.participants + [current_user_id]
        
        collaboration.updated_at = datetime.utcnow()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='PharmacistCollaborationMessage',
            resource_id=message.id,
            details=f'Added message to collaboration {collab_id}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': message.to_dict(),
            'message': 'Message added to thread'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/collaborations/<int:collab_id>/close', methods=['POST'])
@jwt_required()
@require_role(['RN', 'Admin', 'Pharmacist'])
def close_collaboration(collab_id):
    """
    Close collaboration thread with resolution.
    
    Request body:
    {
        "resolution_summary": "Warfarin held for 1 day, INR rechecked and normalized. Resumed at 4mg daily.",
        "status": "RESOLVED"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    collaboration = PharmacistCollaboration.query.get_or_404(collab_id)
    
    # Check access
    if collaboration.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json() or {}
    
    # Validate status
    valid_statuses = ['RESOLVED', 'CLOSED']
    status = data.get('status', 'RESOLVED')
    if status not in valid_statuses:
        return jsonify({'error': f'status must be one of: {", ".join(valid_statuses)}'}), 400
    
    try:
        collaboration.status = status
        collaboration.closed_at = datetime.utcnow()
        collaboration.resolution_summary = data.get('resolution_summary')
        
        # Add closing message if provided
        if data.get('resolution_summary'):
            message = PharmacistCollaborationMessage(
                collaboration_id=collab_id,
                author_user_id=current_user_id,
                message_type='RESOLUTION',
                message_text=data['resolution_summary']
            )
            db.session.add(message)
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='PharmacistCollaboration',
            resource_id=collab_id,
            details=f'Closed collaboration as {status}',
            contains_phi=False,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': collaboration.to_dict(),
            'message': f'Collaboration {status.lower()}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/interventions', methods=['GET'])
@jwt_required()
def get_interventions():
    """
    Get pharmacist interventions.
    
    Query params:
    - patient_id: Filter by patient
    - pharmacist_id: Filter by pharmacist
    - outcome: Filter by outcome (PENDING, ACCEPTED, MODIFIED, DECLINED)
    - unresolved_only: Show only unresolved interventions
    - days: Look back days (default 30)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Parse filters
    patient_id = request.args.get('patient_id')
    pharmacist_id = request.args.get('pharmacist_id')
    outcome = request.args.get('outcome')
    unresolved_only = request.args.get('unresolved_only', 'false').lower() == 'true'
    days = int(request.args.get('days', 30))
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = PharmacistIntervention.query.filter(
        and_(
            PharmacistIntervention.facility_id == user.facility_id,
            PharmacistIntervention.created_at >= cutoff_date
        )
    )
    
    if patient_id:
        query = query.filter_by(patient_id=int(patient_id))
    
    if pharmacist_id:
        query = query.filter_by(pharmacist_id=int(pharmacist_id))
    
    if outcome:
        query = query.filter_by(outcome=outcome)
    
    if unresolved_only:
        query = query.filter_by(outcome='PENDING')
    
    interventions = query.order_by(
        PharmacistIntervention.created_at.desc()
    ).all()
    
    # Enrich with patient info
    result = []
    for intervention in interventions:
        interv_dict = intervention.to_dict()
        patient = Patient.query.get(intervention.patient_id)
        interv_dict['patient_name'] = f"{patient.first_name} {patient.last_name}"
        
        pharmacist = User.query.get(intervention.pharmacist_id)
        interv_dict['pharmacist_name'] = pharmacist.full_name if pharmacist else 'Unknown'
        
        result.append(interv_dict)
    
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result)
    })


@bp.route('/patients/<int:patient_id>/interventions', methods=['GET'])
@jwt_required()
def get_patient_interventions(patient_id):
    """Get all pharmacist interventions for specific patient."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check patient access
    patient = Patient.query.get_or_404(patient_id)
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    days = int(request.args.get('days', 90))
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    interventions = PharmacistIntervention.query.filter(
        and_(
            PharmacistIntervention.patient_id == patient_id,
            PharmacistIntervention.created_at >= cutoff_date
        )
    ).order_by(PharmacistIntervention.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': [interv.to_dict() for interv in interventions],
        'count': len(interventions),
        'patient_id': patient_id
    })


@bp.route('/patients/<int:patient_id>/interventions', methods=['POST'])
@jwt_required()
@require_role(['Pharmacist', 'Admin'])
def create_intervention(patient_id):
    """
    Create pharmacist intervention.
    
    Request body:
    {
        "intervention_type": "DRUG_INTERACTION",
        "severity": "URGENT",
        "medication_id": 5,
        "clinical_concern": "Patient on warfarin and new NSAID order",
        "recommendation": "Discontinue NSAID, consider Tylenol alternative",
        "clinical_rationale": "NSAIDs increase bleeding risk with anticoagulants"
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
    required_fields = ['intervention_type', 'severity', 'clinical_concern', 'recommendation']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate intervention type
    valid_types = [
        'DRUG_INTERACTION', 'DOSE_ADJUSTMENT', 'ALTERNATIVE_RECOMMENDATION',
        'THERAPY_MONITORING', 'ADVERSE_REACTION', 'MEDICATION_ERROR',
        'ALLERGY_CONCERN', 'DUPLICATE_THERAPY', 'RENAL_ADJUSTMENT',
        'THERAPEUTIC_OPTIMIZATION', 'ADR_EVALUATION'
    ]
    if data['intervention_type'] not in valid_types:
        return jsonify({'error': f'intervention_type must be one of: {", ".join(valid_types)}'}), 400
    
    # Validate severity
    valid_severities = ['INFORMATIONAL', 'MONITOR', 'RECOMMEND_CHANGE', 'URGENT', 'MODERATE']
    if data['severity'] not in valid_severities:
        return jsonify({'error': f'severity must be one of: {", ".join(valid_severities)}'}), 400
    
    try:
        intervention = PharmacistIntervention(
            patient_id=patient_id,
            facility_id=patient.facility_id,
            pharmacist_id=current_user_id,
            medication_id=data.get('medication_id'),
            reconciliation_id=data.get('reconciliation_id'),
            intervention_type=data['intervention_type'],
            severity=data['severity'],
            clinical_concern=data['clinical_concern'],
            recommendation=data['recommendation'],
            clinical_rationale=data.get('clinical_rationale'),
            supporting_references=data.get('supporting_references'),
            mtm_billable=data.get('mtm_billable', False),
            time_spent_minutes=data.get('time_spent_minutes')
        )
        
        db.session.add(intervention)
        db.session.flush()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='PharmacistIntervention',
            resource_id=intervention.id,
            details=f'Created {data["intervention_type"]} intervention for patient {patient_id}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': intervention.to_dict(),
            'message': 'Intervention created'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/interventions/<int:intervention_id>/update', methods=['PUT'])
@jwt_required()
@require_role(['Pharmacist', 'Admin', 'RN'])
def update_intervention(intervention_id):
    """
    Update intervention with provider response or outcome.
    
    Request body:
    {
        "provider_notified": true,
        "provider_response": "Agreed, will change to Tylenol",
        "outcome": "ACCEPTED",
        "outcome_notes": "Order changed per pharmacist recommendation",
        "intervention_prevented_error": true
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    intervention = PharmacistIntervention.query.get_or_404(intervention_id)
    
    # Check access
    if intervention.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    try:
        # Update provider notification
        if data.get('provider_notified') is not None:
            intervention.provider_notified = data['provider_notified']
            intervention.provider_notified_at = datetime.utcnow()
            intervention.provider_response = data.get('provider_response')
        
        # Update outcome
        if data.get('outcome'):
            valid_outcomes = ['ACCEPTED', 'MODIFIED', 'DECLINED', 'PENDING']
            if data['outcome'] not in valid_outcomes:
                return jsonify({'error': f'outcome must be one of: {", ".join(valid_outcomes)}'}), 400
            
            intervention.outcome = data['outcome']
            intervention.outcome_notes = data.get('outcome_notes')
            
            if data['outcome'] != 'PENDING':
                intervention.resolved_at = datetime.utcnow()
        
        # Quality metrics
        if data.get('intervention_prevented_error') is not None:
            intervention.intervention_prevented_error = data['intervention_prevented_error']
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='PharmacistIntervention',
            resource_id=intervention_id,
            details=f'Updated intervention outcome: {data.get("outcome", "in progress")}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': intervention.to_dict(),
            'message': 'Intervention updated'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
