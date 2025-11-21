"""Visit routes - visit documentation and management."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from app import db
from app.models import Visit, Patient, User, Assessment, VitalSigns, AuditLog
from app.utils.permissions import require_role

bp = Blueprint('visits', __name__, url_prefix='/api/visits')


@bp.route('', methods=['GET'])
@jwt_required()
def get_visits():
    """
    Get visits list for facility.
    
    Query params:
    - status: Filter by status (scheduled, in_progress, completed, cancelled)
    - nurse_id: Filter by nurse
    - date_from: Start date for visit range
    - date_to: End date for visit range
    - patient_id: Filter by specific patient
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Parse filters
    status = request.args.get('status')
    nurse_id = request.args.get('nurse_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    patient_id = request.args.get('patient_id')
    
    # Build query - join Patient to filter by facility
    query = Visit.query.join(Patient).filter(Patient.facility_id == user.facility_id)
    
    # Apply filters
    if status:
        query = query.filter(Visit.status == status)
    
    if nurse_id:
        query = query.filter(Visit.nurse_id == int(nurse_id))
    
    if patient_id:
        query = query.filter(Visit.patient_id == int(patient_id))
    
    if date_from:
        start_date = datetime.fromisoformat(date_from)
        query = query.filter(Visit.scheduled_date >= start_date)
    
    if date_to:
        end_date = datetime.fromisoformat(date_to)
        query = query.filter(Visit.scheduled_date <= end_date)
    else:
        # Default: today + 7 days
        query = query.filter(Visit.scheduled_date <= datetime.utcnow() + timedelta(days=7))
    
    visits = query.order_by(Visit.scheduled_date.desc()).all()
    
    result = [v.to_dict() for v in visits]
    
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result),
        'filters': {
            'status': status,
            'nurse_id': nurse_id,
            'date_from': date_from,
            'date_to': date_to
        }
    })


@bp.route('', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def create_visit():
    """
    Start new visit (check-in).
    
    Request body:
    {
        "patient_id": 123,
        "visit_type": "Routine Check",
        "scheduled_date": "2025-11-20T10:00:00",
        "chief_complaint": "Medication review and vital signs"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('patient_id'):
        return jsonify({'error': 'patient_id is required'}), 400
    
    patient = Patient.query.get_or_404(data['patient_id'])
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    if patient.status != 'active':
        return jsonify({'error': 'Patient is not active'}), 400
    
    try:
        # Parse scheduled date
        scheduled_date = None
        if data.get('scheduled_date'):
            scheduled_date = datetime.fromisoformat(data['scheduled_date'])
        else:
            scheduled_date = datetime.utcnow()
        
        # Create visit
        visit = Visit(
            patient_id=data['patient_id'],
            nurse_id=current_user_id,
            visit_type=data.get('visit_type', 'Routine Check'),
            scheduled_date=scheduled_date,
            check_in_time=datetime.utcnow(),
            status='in_progress',
            chief_complaint=data.get('chief_complaint')
        )
        
        db.session.add(visit)
        db.session.flush()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='Visit',
            resource_id=visit.id,
            details=f'Started visit for patient {patient.full_name}: {visit.visit_type}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': visit.to_dict(),
            'message': 'Visit started successfully'
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:visit_id>', methods=['GET'])
@jwt_required()
def get_visit_details(visit_id):
    """Get comprehensive visit information with SOAP notes, assessments, vitals."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get(visit.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get visit details
    result = visit.to_dict()
    
    # Add patient basic info
    result['patient'] = {
        'id': patient.id,
        'full_name': patient.full_name,
        'medical_record_number': patient.medical_record_number,
        'age': patient.age,
        'primary_diagnosis': patient.primary_diagnosis
    }
    
    # Add assessments
    assessments = Assessment.query.filter_by(visit_id=visit_id).all()
    result['assessments'] = [a.to_dict() for a in assessments]
    
    # Add vital signs
    vitals = VitalSigns.query.filter_by(visit_id=visit_id).all()
    result['vital_signs'] = [v.to_dict() for v in vitals]
    
    # Audit log
    AuditLog.log_access(
        user_id=current_user_id,
        action='ACCESS',
        resource_type='Visit',
        resource_id=visit_id,
        details=f'Viewed visit documentation',
        contains_phi=True,
        facility_id=user.facility_id
    )
    
    return jsonify({
        'status': 'success',
        'data': result
    })


@bp.route('/<int:visit_id>', methods=['PUT'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def update_visit(visit_id):
    """
    Update visit documentation (SOAP notes).
    
    Request body:
    {
        "subjective": "Patient reports decreased pain...",
        "objective": "Alert and oriented x3, skin warm and dry...",
        "assessment_summary": "Stable condition, pain controlled...",
        "plan": "Continue current medications, follow up in 2 weeks..."
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get(visit.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Only nurse who created visit or RN can update
    if visit.nurse_id != current_user_id and user.role not in ['RN', 'Admin']:
        return jsonify({'error': 'Only visit nurse or RN can update'}), 403
    
    if visit.status == 'completed':
        return jsonify({'error': 'Cannot update completed visit'}), 400
    
    data = request.get_json()
    
    try:
        # Update SOAP notes
        updatable_fields = [
            'subjective', 'objective', 'assessment_summary', 'plan',
            'chief_complaint', 'visit_type'
        ]
        
        changes = []
        for field in updatable_fields:
            if field in data:
                old_value = getattr(visit, field)
                new_value = data[field]
                if old_value != new_value:
                    setattr(visit, field, new_value)
                    changes.append(field)
        
        if not changes:
            return jsonify({'status': 'success', 'message': 'No changes made'}), 200
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='Visit',
            resource_id=visit_id,
            details=f'Updated visit documentation: {", ".join(changes)}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': visit.to_dict(),
            'message': f'{len(changes)} field(s) updated'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:visit_id>/complete', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def complete_visit(visit_id):
    """
    Complete visit with signature (check-out).
    
    Request body:
    {
        "nurse_signature": "Jane Smith, RN",
        "completion_notes": "Visit completed without issues"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get(visit.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Only nurse who created visit or RN can complete
    if visit.nurse_id != current_user_id and user.role not in ['RN', 'Admin']:
        return jsonify({'error': 'Only visit nurse or RN can complete'}), 403
    
    if visit.status == 'completed':
        return jsonify({'error': 'Visit already completed'}), 400
    
    data = request.get_json() or {}
    
    # Validate SOAP documentation
    if not visit.subjective or not visit.objective or not visit.assessment_summary or not visit.plan:
        return jsonify({
            'error': 'Cannot complete visit without full SOAP documentation',
            'missing_fields': [
                field for field in ['subjective', 'objective', 'assessment_summary', 'plan']
                if not getattr(visit, field)
            ]
        }), 400
    
    try:
        visit.check_out_time = datetime.utcnow()
        visit.status = 'completed'
        visit.nurse_signature = data.get('nurse_signature') or f'{user.first_name} {user.last_name}, {user.role}'
        
        # Calculate visit duration
        if visit.check_in_time:
            duration = (visit.check_out_time - visit.check_in_time).seconds // 60  # minutes
            visit.duration_minutes = duration
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='Visit',
            resource_id=visit_id,
            details=f'Completed visit for {patient.full_name}. Duration: {visit.duration_minutes} minutes',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': visit.to_dict(),
            'message': 'Visit completed successfully',
            'duration_minutes': visit.duration_minutes
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:visit_id>/cancel', methods=['POST'])
@jwt_required()
@require_role(['RN', 'Admin'])
def cancel_visit(visit_id):
    """
    Cancel visit.
    
    Request body:
    {
        "cancellation_reason": "Patient declined visit today"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get(visit.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    if visit.status in ['completed', 'cancelled']:
        return jsonify({'error': f'Cannot cancel {visit.status} visit'}), 400
    
    data = request.get_json() or {}
    
    try:
        visit.status = 'cancelled'
        cancellation_reason = data.get('cancellation_reason', 'Not specified')
        
        # Add to visit_notes
        if visit.visit_notes:
            visit.visit_notes += f"\n\nCANCELLED: {cancellation_reason}"
        else:
            visit.visit_notes = f"CANCELLED: {cancellation_reason}"
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='Visit',
            resource_id=visit_id,
            details=f'Cancelled visit: {cancellation_reason}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': visit.to_dict(),
            'message': 'Visit cancelled'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Patient-specific visit endpoints
@bp.route('/patients/<int:patient_id>/visits', methods=['GET'])
@jwt_required()
def get_patient_visits(patient_id):
    """Get visit history for specific patient."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Parse date range
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    limit = int(request.args.get('limit', 50))
    
    query = Visit.query.filter_by(patient_id=patient_id)
    
    if date_from:
        start_date = datetime.fromisoformat(date_from)
        query = query.filter(Visit.scheduled_date >= start_date)
    
    if date_to:
        end_date = datetime.fromisoformat(date_to)
        query = query.filter(Visit.scheduled_date <= end_date)
    
    visits = query.order_by(Visit.scheduled_date.desc()).limit(limit).all()
    
    result = [v.to_dict() for v in visits]
    
    # Audit log
    AuditLog.log_access(
        user_id=current_user_id,
        action='ACCESS',
        resource_type='VisitHistory',
        resource_id=patient_id,
        details=f'Viewed visit history for patient',
        contains_phi=True,
        facility_id=user.facility_id
    )
    
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result),
        'patient': {
            'id': patient.id,
            'full_name': patient.full_name,
            'medical_record_number': patient.medical_record_number
        }
    })


@bp.route('/patients/<int:patient_id>/visits', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def create_patient_visit(patient_id):
    """
    Alias for creating visit - accepts patient_id in URL instead of body.
    
    Request body:
    {
        "visit_type": "Routine Check",
        "scheduled_date": "2025-11-20T10:00:00",
        "chief_complaint": "Medication review"
    }
    """
    data = request.get_json() or {}
    data['patient_id'] = patient_id
    
    # Forward to main create_visit endpoint
    request._cached_json = (data, data)
    return create_visit()
