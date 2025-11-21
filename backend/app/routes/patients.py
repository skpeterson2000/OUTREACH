"""Patient routes - patient management and records."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import and_, or_
from app import db
from app.models import Patient, User, Visit, Medication, AuditLog
from app.utils.permissions import require_role

bp = Blueprint('patients', __name__, url_prefix='/api/patients')


@bp.route('', methods=['GET'])
@jwt_required()
def get_patients():
    """
    Get patients list for facility.
    
    Query params:
    - status: Filter by status (active, discharged, deceased)
    - search: Search by name or MRN
    - is_hospice: Filter hospice patients
    - high_risk: Filter high-risk patients (fall risk, complex med regimens)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Parse filters
    status = request.args.get('status', 'active')
    search = request.args.get('search')
    is_hospice = request.args.get('is_hospice')
    high_risk = request.args.get('high_risk')
    
    # Build query - filter by facility
    query = Patient.query.filter_by(facility_id=user.facility_id)
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if is_hospice:
        query = query.filter_by(is_hospice=(is_hospice.lower() == 'true'))
    
    if high_risk and high_risk.lower() == 'true':
        query = query.filter_by(fall_risk=True)
    
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            or_(
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.medical_record_number.ilike(search_pattern)
            )
        )
    
    patients = query.order_by(Patient.last_name, Patient.first_name).all()
    
    # Basic patient list (not full details)
    result = [p.to_dict(include_sensitive=False) for p in patients]
    
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result),
        'filters': {
            'status': status,
            'is_hospice': is_hospice,
            'high_risk': high_risk
        }
    })


@bp.route('', methods=['POST'])
@jwt_required()
@require_role(['RN', 'Admin'])
def create_patient():
    """
    Admit new patient.
    
    Request body:
    {
        "medical_record_number": "MRN123456",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1945-03-15",
        "gender": "M",
        "phone_primary": "555-1234",
        "address_line1": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62701",
        "primary_diagnosis": "CHF, DM2",
        "allergies": "Penicillin",
        "code_status": "Full Code",
        "admission_date": "2025-11-20"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['medical_record_number', 'first_name', 'last_name', 'date_of_birth']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check for duplicate MRN
    existing = Patient.query.filter_by(
        medical_record_number=data['medical_record_number']
    ).first()
    
    if existing:
        return jsonify({'error': 'Patient with this MRN already exists'}), 409
    
    try:
        # Parse dates
        dob = datetime.fromisoformat(data['date_of_birth']).date()
        admission_date = None
        if data.get('admission_date'):
            admission_date = datetime.fromisoformat(data['admission_date']).date()
        else:
            admission_date = datetime.utcnow().date()
        
        # Create patient
        patient = Patient(
            facility_id=user.facility_id,
            medical_record_number=data['medical_record_number'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            middle_name=data.get('middle_name'),
            date_of_birth=dob,
            gender=data.get('gender'),
            phone_primary=data.get('phone_primary'),
            phone_secondary=data.get('phone_secondary'),
            email=data.get('email'),
            address_line1=data.get('address_line1'),
            address_line2=data.get('address_line2'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_relationship=data.get('emergency_contact_relationship'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            primary_diagnosis=data.get('primary_diagnosis'),
            secondary_diagnoses=data.get('secondary_diagnoses'),
            allergies=data.get('allergies'),
            code_status=data.get('code_status', 'Full Code'),
            insurance_primary=data.get('insurance_primary'),
            insurance_primary_id=data.get('insurance_primary_id'),
            primary_physician=data.get('primary_physician'),
            physician_phone=data.get('physician_phone'),
            admission_date=admission_date,
            status='active',
            fall_risk=data.get('fall_risk', False),
            language_preference=data.get('language_preference'),
            interpreter_needed=data.get('interpreter_needed', False)
        )
        
        db.session.add(patient)
        db.session.flush()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='Patient',
            resource_id=patient.id,
            details=f'Admitted patient: {patient.full_name} (MRN: {patient.medical_record_number})',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': patient.to_dict(include_sensitive=True),
            'message': 'Patient admitted successfully'
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient_details(patient_id):
    """Get comprehensive patient information."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get full patient details
    result = patient.to_dict(include_sensitive=True)
    
    # Add related counts
    result['active_medications_count'] = Medication.query.filter_by(
        patient_id=patient_id,
        status='active'
    ).count()
    
    result['recent_visits_count'] = Visit.query.filter_by(
        patient_id=patient_id
    ).filter(
        Visit.check_in_time >= datetime.utcnow().replace(day=1)  # This month
    ).count()
    
    # Audit log
    AuditLog.log_access(
        user_id=current_user_id,
        action='ACCESS',
        resource_type='Patient',
        resource_id=patient_id,
        details=f'Viewed patient record',
        contains_phi=True,
        facility_id=user.facility_id
    )
    
    return jsonify({
        'status': 'success',
        'data': result
    })


@bp.route('/<int:patient_id>', methods=['PUT'])
@jwt_required()
@require_role(['RN', 'Admin'])
def update_patient(patient_id):
    """
    Update patient information.
    
    Can update demographics, contact info, medical information.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    try:
        # Update demographics (non-critical fields only)
        updatable_fields = [
            'phone_primary', 'phone_secondary', 'email',
            'address_line1', 'address_line2', 'city', 'state', 'zip_code',
            'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone',
            'primary_diagnosis', 'secondary_diagnoses', 'allergies', 'code_status',
            'insurance_primary', 'insurance_primary_id', 'insurance_secondary', 'insurance_secondary_id',
            'primary_physician', 'physician_phone', 'physician_fax',
            'fall_risk', 'infection_precautions', 'language_preference', 'interpreter_needed',
            'is_hospice', 'hospice_agency', 'hospice_nurse_name', 'hospice_nurse_phone',
            'goals_of_care', 'advance_directive_on_file', 'polst_on_file',
            'do_not_hospitalize', 'comfort_measures_only', 'pain_management_plan'
        ]
        
        changes = []
        for field in updatable_fields:
            if field in data and data[field] is not None:
                old_value = getattr(patient, field)
                new_value = data[field]
                if old_value != new_value:
                    setattr(patient, field, new_value)
                    changes.append(f'{field}: {old_value} → {new_value}')
        
        if not changes:
            return jsonify({'status': 'success', 'message': 'No changes made'}), 200
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='Patient',
            resource_id=patient_id,
            details=f'Updated patient: {", ".join(changes[:5])}' + (' ...' if len(changes) > 5 else ''),
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': patient.to_dict(include_sensitive=True),
            'message': f'{len(changes)} field(s) updated'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:patient_id>/discharge', methods=['POST'])
@jwt_required()
@require_role(['RN', 'Admin'])
def discharge_patient(patient_id):
    """
    Discharge patient.
    
    Request body:
    {
        "discharge_date": "2025-11-20",
        "discharge_disposition": "Home with home health services",
        "discharge_notes": "Patient stable, medications reconciled"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    if patient.status == 'discharged':
        return jsonify({'error': 'Patient already discharged'}), 400
    
    data = request.get_json() or {}
    
    try:
        # Parse discharge date
        if data.get('discharge_date'):
            discharge_date = datetime.fromisoformat(data['discharge_date']).date()
        else:
            discharge_date = datetime.utcnow().date()
        
        patient.discharge_date = discharge_date
        patient.status = 'discharged'
        
        # Discontinue active medications
        active_meds = Medication.query.filter_by(
            patient_id=patient_id,
            status='active'
        ).all()
        
        for med in active_meds:
            med.status = 'discontinued'
            med.discontinued_date = discharge_date
            med.discontinued_reason = 'Patient discharged'
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='Patient',
            resource_id=patient_id,
            details=f'Discharged patient: {patient.full_name}. Disposition: {data.get("discharge_disposition", "Not specified")}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': patient.to_dict(include_sensitive=True),
            'message': 'Patient discharged successfully',
            'medications_discontinued': len(active_meds)
        })
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:patient_id>/summary', methods=['GET'])
@jwt_required()
def get_patient_summary(patient_id):
    """
    Get comprehensive patient summary (for care transitions, reports).
    
    Includes: demographics, active medications, recent vitals, alerts, recent visits.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    from app.models import ADRAlert, VitalSigns
    
    # Get patient details
    summary = patient.to_dict(include_sensitive=True)
    
    # Active medications
    active_meds = Medication.query.filter_by(
        patient_id=patient_id,
        status='active'
    ).all()
    summary['active_medications'] = [m.to_dict() for m in active_meds]
    
    # Active ADR alerts
    active_alerts = ADRAlert.query.filter(
        and_(
            ADRAlert.patient_id == patient_id,
            ADRAlert.status.in_(['NEW', 'ACKNOWLEDGED', 'INVESTIGATING'])
        )
    ).all()
    summary['active_adr_alerts'] = [a.to_dict(include_suggestions=False) for a in active_alerts]
    
    # Recent visits (last 30 days)
    recent_visits = Visit.query.filter(
        and_(
            Visit.patient_id == patient_id,
            Visit.check_in_time >= datetime.utcnow().replace(day=1) - timedelta(days=30)
        )
    ).order_by(Visit.check_in_time.desc()).limit(10).all()
    summary['recent_visits'] = [v.to_dict() for v in recent_visits]
    
    # Most recent vitals
    latest_vitals = VitalSigns.query.filter_by(
        patient_id=patient_id
    ).order_by(VitalSigns.recorded_time.desc()).first()
    
    if latest_vitals:
        summary['latest_vitals'] = latest_vitals.to_dict()
    
    # Audit log
    AuditLog.log_access(
        user_id=current_user_id,
        action='ACCESS',
        resource_type='PatientSummary',
        resource_id=patient_id,
        details=f'Generated patient summary for care transition/report',
        contains_phi=True,
        facility_id=user.facility_id
    )
    
    return jsonify({
        'status': 'success',
        'data': summary,
        'generated_at': datetime.utcnow().isoformat()
    })


from datetime import timedelta
