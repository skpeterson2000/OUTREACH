"""Medication routes - MAR and medication administration."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from app import db
from app.models import (
    Medication, MedicationAdministration, Patient, User,
    AuditLog
)
from app.utils.permissions import require_role
from app.utils.logging import (
    log_api_request, log_user_action, log_medication_administration,
    app_logger
)

bp = Blueprint('medications', __name__, url_prefix='/api')


@bp.route('/patients/<int:patient_id>/medications', methods=['GET'])
@jwt_required()
def get_patient_medications(patient_id):
    """
    Get list of patient's medications.
    
    Query params:
    - status: Filter by status (active, discontinued, completed)
    - include_history: Include discontinued meds (true/false)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check patient access
    patient = Patient.query.get_or_404(patient_id)
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Build query
    query = Medication.query.filter_by(patient_id=patient_id)
    
    # Filter by status
    status = request.args.get('status')
    include_history = request.args.get('include_history', 'false').lower() == 'true'
    
    if status:
        query = query.filter_by(status=status)
    elif not include_history:
        query = query.filter_by(status='active')
    
    medications = query.order_by(Medication.medication_name).all()
    
    # Enrich with next due time and last administration
    result = []
    for med in medications:
        med_dict = med.to_dict()
        
        # Get last administration
        last_admin = MedicationAdministration.query.filter_by(
            medication_id=med.id
        ).order_by(MedicationAdministration.administration_time.desc()).first()
        
        if last_admin:
            actual_time = last_admin.actual_time or last_admin.administration_time
            med_dict['last_administration'] = {
                'actual_time': actual_time.isoformat() if actual_time else None,
                'status': last_admin.status,
                'administered_by': last_admin.administered_by
            }
        
        # Calculate next due time (simplified - would need more complex scheduling logic)
        if med.status == 'active' and not med.is_prn:
            # This is simplified - real implementation would parse scheduled_times
            med_dict['next_due'] = 'See schedule'
        
        result.append(med_dict)
    
    # Audit log
    AuditLog.log_access(
        user_id=current_user_id,
        action='ACCESS',
        resource_type='Medication',
        resource_id=None,
        details=f'Viewed medication list for patient {patient_id}',
        contains_phi=True,
        facility_id=user.facility_id
    )
    
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result)
    })


@bp.route('/patients/<int:patient_id>/mar/due', methods=['GET'])
@jwt_required()
def get_due_medications(patient_id):
    """
    Get medications due now or in specified timeframe.
    
    Query params:
    - window_hours: Look ahead window (default 2 hours)
    - include_prn: Include PRN meds (default true)
    - shift: Filter by shift (day/evening/night)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check patient access
    patient = Patient.query.get_or_404(patient_id)
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Parse parameters
    window_hours = int(request.args.get('window_hours', 2))
    include_prn = request.args.get('include_prn', 'true').lower() == 'true'
    
    now = datetime.utcnow()
    window_end = now + timedelta(hours=window_hours)
    
    # Get active medications
    active_meds = Medication.query.filter_by(
        patient_id=patient_id,
        status='active'
    ).all()
    
    due_medications = []
    
    for med in active_meds:
        # Include PRN meds if requested
        if med.is_prn and include_prn:
            med_dict = med.to_dict()
            med_dict['is_due'] = 'PRN'
            med_dict['scheduled_time'] = None
            due_medications.append(med_dict)
            continue
        
        # Skip PRN if not included
        if med.is_prn:
            continue
        
        # For scheduled meds, would parse scheduled_times JSON
        # Simplified: check if any recent administration
        last_admin = MedicationAdministration.query.filter(
            and_(
                MedicationAdministration.medication_id == med.id,
                MedicationAdministration.status == 'given'
            )
        ).order_by(MedicationAdministration.actual_time.desc()).first()
        
        # Simplified logic: if no admin in last 4 hours, consider due
        if not last_admin or (now - last_admin.actual_time).total_seconds() > 14400:
            med_dict = med.to_dict()
            med_dict['is_due'] = 'scheduled'
            med_dict['scheduled_time'] = now.isoformat()
            due_medications.append(med_dict)
    
    return jsonify({
        'status': 'success',
        'data': due_medications,
        'count': len(due_medications),
        'as_of': now.isoformat()
    })


@bp.route('/mar/overdue', methods=['GET'])
@jwt_required()
def get_overdue_medications():
    """
    Get all overdue medication administrations across all patients.
    
    Query params:
    - grace_period_minutes: Grace period after scheduled time (default 60)
    - patient_id: Filter by specific patient
    - facility_id: Filter by facility (admin only)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Parse parameters
    grace_period_minutes = int(request.args.get('grace_period_minutes', 60))
    patient_id = request.args.get('patient_id', type=int)
    
    now = datetime.utcnow()
    cutoff_time = now - timedelta(minutes=grace_period_minutes)
    
    # Build query for overdue administrations
    query = db.session.query(
        MedicationAdministration,
        Medication,
        Patient
    ).join(
        Medication, MedicationAdministration.medication_id == Medication.id
    ).join(
        Patient, MedicationAdministration.patient_id == Patient.id
    ).filter(
        MedicationAdministration.status == 'scheduled',
        MedicationAdministration.scheduled_time <= cutoff_time,
        Medication.status == 'active'
    )
    
    # Filter by facility access
    if user.role != 'Admin':
        query = query.filter(Patient.facility_id == user.facility_id)
    
    # Optional patient filter
    if patient_id:
        query = query.filter(MedicationAdministration.patient_id == patient_id)
    
    # Order by how overdue (most overdue first)
    query = query.order_by(MedicationAdministration.scheduled_time.asc())
    
    results = query.all()
    
    # Format results
    overdue_list = []
    for admin, med, patient in results:
        minutes_overdue = int((now - admin.scheduled_time).total_seconds() / 60)
        
        overdue_list.append({
            'administration_id': admin.id,
            'medication_id': med.id,
            'medication_name': med.medication_name,
            'dose': med.dose,
            'route': med.route,
            'patient_id': patient.id,
            'patient_name': f"{patient.first_name} {patient.last_name}",
            'patient_room': patient.room_number if hasattr(patient, 'room_number') else None,
            'scheduled_time': admin.scheduled_time.isoformat(),
            'minutes_overdue': minutes_overdue,
            'is_high_risk': med.is_high_risk,
            'is_controlled_substance': med.is_controlled_substance if hasattr(med, 'is_controlled_substance') else False,
        })
    
    return jsonify({
        'status': 'success',
        'data': overdue_list,
        'count': len(overdue_list),
        'grace_period_minutes': grace_period_minutes,
        'as_of': now.isoformat()
    })


@bp.route('/medications/<int:medication_id>/adr-alerts', methods=['GET'])
@jwt_required()
def get_medication_adr_alerts(medication_id):
    """
    Get active ADR alerts for a specific medication.
    
    Shows any active adverse reaction surveillance alerts that staff should
    be aware of before administering this medication.
    """
    from app.models import ADRAlert
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    medication = Medication.query.get_or_404(medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get active alerts for this medication
    alerts = ADRAlert.query.filter_by(
        medication_id=medication_id,
        facility_id=user.facility_id
    ).filter(
        ADRAlert.status.in_(['NEW', 'ACKNOWLEDGED', 'INVESTIGATING'])
    ).order_by(ADRAlert.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'medication_id': medication_id,
        'medication_name': medication.medication_name,
        'patient_id': patient.id,
        'patient_name': f"{patient.first_name} {patient.last_name}",
        'active_alerts': [alert.to_dict() for alert in alerts],
        'alert_count': len(alerts)
    })


@bp.route('/medications/<int:medication_id>/administer', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'TMA', 'Admin'])  # TMA can also administer
@log_api_request
def administer_medication(medication_id):
    """
    Document medication administration.
    
    SAFETY: Checks for ADR alerts before allowing administration.
    
    Request body:
    {
        "scheduled_time": "2025-11-20T14:00:00Z",
        "actual_time": "2025-11-20T14:05:00Z",
        "status": "given",
        "dose_given": "500mg",
        "not_given_reason": null,
        "pre_administration_assessment": "BP 128/82, P 76",
        "administration_site": "PO",
        "prn_reason_given": "Patient c/o pain 7/10",
        "notes": "Patient tolerated well",
        "witness_id": null,
        "adr_alerts_acknowledged": true  // Required if active alerts exist
    }
    """
    from app.models import ADRAlert, ADRAlertAcknowledgment
    from flask import current_app
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    current_app.logger.info(f"🏥 MEDICATION ADMINISTRATION INITIATED | User: {user.username} ({user.role}) | Medication ID: {medication_id}")
    
    # Get medication and verify access
    medication = Medication.query.get_or_404(medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    current_app.logger.info(f"   📋 Patient: {patient.first_name} {patient.last_name} (ID: {patient.id}) | Medication: {medication.medication_name}")
    
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    current_app.logger.info(f"   📝 Administration request: status={data.get('status')}, dose={data.get('dose_given')}")
    
    # ⚠️ SAFETY CHECK: Verify ADR alert acknowledgments
    if data.get('status') == 'given':  # Only check if actually administering
        current_app.logger.info(f"   🔒 SAFETY CHECK: Verifying ADR alert acknowledgments for patient {patient.id}")
        
        # Check for active ADR alerts for this patient
        active_alerts = ADRAlert.query.filter_by(
            patient_id=patient.id,
            facility_id=user.facility_id
        ).filter(
            ADRAlert.status.in_(['NEW', 'ACKNOWLEDGED', 'INVESTIGATING'])
        ).all()
        
        current_app.logger.info(f"   📊 Found {len(active_alerts)} active ADR alerts")
        
        if active_alerts:
            # Check if user has valid acknowledgments for ALL active alerts
            unacknowledged = []
            expired = []
            held_meds = []
            
            for alert in active_alerts:
                # Get user's most recent acknowledgment for this alert
                ack = ADRAlertAcknowledgment.query.filter_by(
                    alert_id=alert.id,
                    user_id=current_user_id
                ).order_by(ADRAlertAcknowledgment.acknowledged_at.desc()).first()
                
                if not ack:
                    unacknowledged.append(alert.to_dict())
                elif ack.is_expired:
                    expired.append(alert.to_dict())
                elif ack.action_taken == 'HOLD_MEDICATION' and alert.medication_id == medication_id:
                    held_meds.append({
                        'alert': alert.to_dict(),
                        'hold_info': {
                            'reason': ack.hold_reason,
                            'duration': ack.hold_duration,
                            'provider_notified': ack.provider_notified
                        }
                    })
            
            # If there are medications on hold, block administration
            if held_meds:
                current_app.logger.warning(f"   ⛔ BLOCKED: Medication on hold - {len(held_meds)} hold(s)")
                return jsonify({
                    'error': 'MEDICATION_ON_HOLD',
                    'message': 'This medication is on hold due to ADR alert',
                    'held_medications': held_meds,
                    'action_required': 'Contact provider before administering. Medication hold must be lifted.'
                }), 403
            
            # If there are unacknowledged or expired alerts, block administration
            if unacknowledged or expired:
                current_app.logger.warning(f"   ⛔ BLOCKED: Unacknowledged ({len(unacknowledged)}) or expired ({len(expired)}) alerts")
                return jsonify({
                    'error': 'ADR_ALERTS_NOT_ACKNOWLEDGED',
                    'message': 'You must acknowledge all active ADR alerts before administering medications to this patient',
                    'unacknowledged_alerts': unacknowledged,
                    'expired_acknowledgments': expired,
                    'total_active_alerts': len(active_alerts),
                    'action_required': 'Review and acknowledge each ADR alert before proceeding'
                }), 403
            
            current_app.logger.info(f"   ✅ SAFETY CHECK PASSED: All alerts acknowledged")
    
    # Validate required fields
    if not data.get('scheduled_time'):
        return jsonify({'error': 'scheduled_time is required'}), 400
    
    if not data.get('actual_time'):
        return jsonify({'error': 'actual_time is required'}), 400
    
    if not data.get('status'):
        return jsonify({'error': 'status is required (given/refused/held/omitted)'}), 400
    
    # Validate status
    valid_statuses = ['given', 'refused', 'held', 'omitted']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'status must be one of: {", ".join(valid_statuses)}'}), 400
    
    # If not given, require reason
    if data['status'] != 'given' and not data.get('not_given_reason'):
        return jsonify({'error': 'not_given_reason required when status is not "given"'}), 400
    
    # If PRN, require reason given
    if medication.is_prn and data['status'] == 'given' and not data.get('prn_reason_given'):
        return jsonify({'error': 'prn_reason_given required for PRN medications'}), 400
    
    try:
        # Create administration record
        administration = MedicationAdministration(
            medication_id=medication_id,
            administered_by=current_user_id,
            scheduled_time=datetime.fromisoformat(data['scheduled_time'].replace('Z', '+00:00')),
            actual_time=datetime.fromisoformat(data['actual_time'].replace('Z', '+00:00')),
            status=data['status'],
            dose_given=data.get('dose_given', medication.dose),
            not_given_reason=data.get('not_given_reason'),
            pre_administration_assessment=data.get('pre_administration_assessment'),
            post_administration_assessment=data.get('post_administration_assessment'),
            prn_reason_given=data.get('prn_reason_given'),
            administration_site=data.get('administration_site'),
            notes=data.get('notes'),
            witness_id=data.get('witness_id')
        )
        
        db.session.add(administration)
        db.session.flush()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='MedicationAdministration',
            resource_id=administration.id,
            details=f'Administered {medication.name} to patient {patient.id}: {data["status"]}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        current_app.logger.info(f"   ✅ MEDICATION ADMINISTRATION RECORDED | ID: {administration.id} | Status: {data['status']}")
        user_logger = logging.getLogger('user_actions')
        user_logger.info(f"MEDICATION ADMINISTERED | User: {user.username} | Patient: {patient.first_name} {patient.last_name} | Med: {medication.medication_name} | Status: {data['status']}")
        
        return jsonify({
            'status': 'success',
            'data': administration.to_dict(),
            'message': f'Medication administration recorded: {data["status"]}'
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        current_app.logger.error(f"   ❌ ERROR: Invalid datetime - {str(e)}")
        return jsonify({'error': f'Invalid datetime format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"   ❌ ERROR: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/medication-administrations/<int:admin_id>/reassess-prn', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def reassess_prn_effectiveness(admin_id):
    """
    Document PRN medication effectiveness.
    
    Request body:
    {
        "prn_effectiveness_rating": 4,
        "prn_effectiveness_notes": "Pain reduced to 3/10 after 30 minutes",
        "prn_reassessment_time": "2025-11-20T14:35:00Z"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    administration = MedicationAdministration.query.get_or_404(admin_id)
    medication = Medication.query.get(administration.medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Verify this is a PRN medication
    if not medication.is_prn:
        return jsonify({'error': 'This endpoint is only for PRN medications'}), 400
    
    # Verify medication was given
    if administration.status != 'given':
        return jsonify({'error': 'Cannot reassess effectiveness for medication that was not given'}), 400
    
    data = request.get_json()
    
    # Validate rating
    rating = data.get('prn_effectiveness_rating')
    if rating is None:
        return jsonify({'error': 'prn_effectiveness_rating is required (1-5 scale)'}), 400
    
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'prn_effectiveness_rating must be 1-5'}), 400
    
    try:
        # Update administration record
        administration.prn_effectiveness_rating = rating
        administration.prn_effectiveness_notes = data.get('prn_effectiveness_notes')
        
        if data.get('prn_reassessment_time'):
            administration.prn_reassessment_time = datetime.fromisoformat(
                data['prn_reassessment_time'].replace('Z', '+00:00')
            )
        else:
            administration.prn_reassessment_time = datetime.utcnow()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='MedicationAdministration',
            resource_id=administration.id,
            details=f'PRN effectiveness rated {rating}/5 for {medication.name}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': administration.to_dict(),
            'message': 'PRN effectiveness documented'
        })
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid datetime format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/patients/<int:patient_id>/mar', methods=['GET'])
@jwt_required()
def get_patient_mar(patient_id):
    """
    Get Medication Administration Record (MAR) for patient.
    
    Query params:
    - start_date: Start date (default: today)
    - end_date: End date (default: today)
    - shift: Filter by shift (day/evening/night)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check patient access
    patient = Patient.query.get_or_404(patient_id)
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Parse date range
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str:
        # Handle date-only strings by adding time component
        if 'T' not in start_date_str:
            start_date = datetime.fromisoformat(start_date_str + 'T00:00:00')
        else:
            start_date = datetime.fromisoformat(start_date_str)
    else:
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if end_date_str:
        # Handle date-only strings by adding time component
        if 'T' not in end_date_str:
            end_date = datetime.fromisoformat(end_date_str + 'T23:59:59')
        else:
            end_date = datetime.fromisoformat(end_date_str)
    else:
        end_date = datetime.utcnow().replace(hour=23, minute=59, second=59)
    
    # Get medications and administrations
    medications = Medication.query.filter_by(
        patient_id=patient_id,
        status='active'
    ).all()
    
    mar_data = []
    
    for med in medications:
        med_dict = med.to_dict()
        
        # Get administrations in date range
        administrations = MedicationAdministration.query.filter(
            and_(
                MedicationAdministration.medication_id == med.id,
                MedicationAdministration.scheduled_time >= start_date,
                MedicationAdministration.scheduled_time <= end_date
            )
        ).order_by(MedicationAdministration.scheduled_time).all()
        
        med_dict['administrations'] = [admin.to_dict() for admin in administrations]
        med_dict['total_administrations'] = len(administrations)
        med_dict['given_count'] = sum(1 for a in administrations if a.status == 'given')
        med_dict['missed_count'] = sum(1 for a in administrations if a.status in ['refused', 'held', 'omitted'])
        
        mar_data.append(med_dict)
    
    # Audit log
    AuditLog.log_access(
        user_id=current_user_id,
        action='ACCESS',
        resource_type='MAR',
        resource_id=patient_id,
        details=f'Viewed MAR for patient {patient_id}',
        contains_phi=True,
        facility_id=user.facility_id
    )
    
    return jsonify({
        'status': 'success',
        'data': mar_data,
        'patient_id': patient_id,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })


@bp.route('/medication-administrations/<int:admin_id>', methods=['GET'])
@jwt_required()
def get_administration_details(admin_id):
    """Get details of a specific medication administration."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    administration = MedicationAdministration.query.get_or_404(admin_id)
    medication = Medication.query.get(administration.medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Enrich with related data
    result = administration.to_dict()
    result['medication'] = medication.to_dict()
    result['patient_id'] = patient.id
    
    return jsonify({
        'status': 'success',
        'data': result
    })


@bp.route('/medications/<int:medication_id>', methods=['PATCH'])
@jwt_required()
@require_role(['RN', 'LPN', 'Pharmacist', 'Admin'])
def update_medication(medication_id):
    """
    Update medication details (schedule, dose, status, etc.).
    Nurses can update schedule and hold medications.
    Only pharmacists/prescribers can change dose/route.
    
    Request body:
    {
        "status": "held",  // active, held, discontinued
        "hold_reason": "Patient NPO for procedure",
        "time_of_day": "08:00,20:00",
        "frequency_times_per_day": 2,
        "special_instructions": "Give with food"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    medication = Medication.query.get_or_404(medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    changes = []
    
    # Status changes (RN can hold/activate)
    if 'status' in data:
        old_status = medication.status
        new_status = data['status']
        
        # Validate status transitions
        valid_statuses = ['active', 'held', 'discontinued', 'completed']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # RN/LPN can hold or reactivate, but not discontinue (requires MD order)
        if new_status == 'discontinued' and user.role not in ['Pharmacist', 'Admin']:
            return jsonify({'error': 'Only pharmacists or admins can discontinue medications'}), 403
        
        if new_status == 'held' and not data.get('hold_reason'):
            return jsonify({'error': 'hold_reason required when holding medication'}), 400
        
        medication.status = new_status
        changes.append(f'Status changed from {old_status} to {new_status}')
        
        if new_status == 'discontinued':
            medication.discontinued_date = datetime.utcnow().date()
            medication.discontinued_reason = data.get('discontinued_reason', data.get('hold_reason'))
    
    # Schedule changes (RN can modify)
    if 'time_of_day' in data:
        old_times = medication.time_of_day
        medication.time_of_day = data['time_of_day']
        changes.append(f'Schedule changed from {old_times} to {data["time_of_day"]}')
    
    if 'frequency_times_per_day' in data:
        medication.frequency_times_per_day = data['frequency_times_per_day']
        changes.append(f'Frequency times per day updated to {data["frequency_times_per_day"]}')
    
    # Special instructions (RN can add)
    if 'special_instructions' in data:
        medication.special_instructions = data['special_instructions']
        changes.append('Special instructions updated')
    
    # Dose/route changes (only Pharmacist/Admin)
    if 'dose' in data or 'route' in data:
        if user.role not in ['Pharmacist', 'Admin']:
            return jsonify({'error': 'Only pharmacists or admins can change dose or route'}), 403
        
        if 'dose' in data:
            old_dose = medication.dose
            medication.dose = data['dose']
            changes.append(f'Dose changed from {old_dose} to {data["dose"]}')
        
        if 'route' in data:
            old_route = medication.route
            medication.route = data['route']
            changes.append(f'Route changed from {old_route} to {data["route"]}')
    
    try:
        medication.updated_at = datetime.utcnow()
        
        # Audit log
        AuditLog.log_action(
            user=user,
            action='UPDATE',
            resource_type='Medication',
            resource_id=medication_id,
            description=f'Updated medication {medication.medication_name} for patient {patient.id}: {"; ".join(changes)}',
            phi_accessed=True
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': medication.to_dict(),
            'changes': changes,
            'message': 'Medication updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/medications/<int:medication_id>/hold', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def hold_medication(medication_id):
    """
    Quick endpoint to place medication on hold.
    
    Request body:
    {
        "reason": "Patient NPO for surgery",
        "expected_resume_date": "2025-11-21"  // optional
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    medication = Medication.query.get_or_404(medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    if not data.get('reason'):
        return jsonify({'error': 'Reason for hold is required'}), 400
    
    old_status = medication.status
    medication.status = 'held'
    medication.special_instructions = f"HELD: {data['reason']}"
    if medication.special_instructions and not medication.special_instructions.startswith('HELD:'):
        medication.special_instructions = f"HELD: {data['reason']}\n{medication.special_instructions}"
    
    medication.updated_at = datetime.utcnow()
    
    # Audit log
    AuditLog.log_action(
        user=user,
        action='UPDATE',
        resource_type='Medication',
        resource_id=medication_id,
        description=f'Placed {medication.medication_name} on hold for patient {patient.id}. Reason: {data["reason"]}',
        phi_accessed=True
    )
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': medication.to_dict(),
        'message': f'Medication placed on hold: {data["reason"]}'
    })


@bp.route('/medications/<int:medication_id>/resume', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def resume_medication(medication_id):
    """
    Resume a held medication.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    medication = Medication.query.get_or_404(medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    # Check access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    if medication.status != 'held':
        return jsonify({'error': 'Medication is not currently on hold'}), 400
    
    medication.status = 'active'
    # Remove HELD prefix from instructions
    if medication.special_instructions and medication.special_instructions.startswith('HELD:'):
        lines = medication.special_instructions.split('\n')
        medication.special_instructions = '\n'.join(lines[1:]) if len(lines) > 1 else None
    
    medication.updated_at = datetime.utcnow()
    
    # Audit log
    AuditLog.log_action(
        user=user,
        action='UPDATE',
        resource_type='Medication',
        resource_id=medication_id,
        description=f'Resumed {medication.medication_name} for patient {patient.id}',
        phi_accessed=True
    )
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': medication.to_dict(),
        'message': 'Medication resumed'
    })


@bp.route('/patients/<int:patient_id>/medications', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Pharmacist', 'Admin'])
def create_medication(patient_id):
    """
    Add a new medication to patient's MAR (per physician order).
    RNs/LPNs can add medications to implement physician orders.
    
    Request body:
    {
        "medication_name": "Aspirin",
        "generic_name": "Acetylsalicylic acid",
        "dose": "81mg",
        "route": "PO",
        "frequency": "Daily",
        "frequency_times_per_day": 1,
        "time_of_day": "08:00",
        "is_prn": false,
        "prn_indication": null,
        "prescribing_physician": "Dr. Smith",
        "indication": "Cardiovascular prophylaxis",
        "special_instructions": "Give with food",
        "start_date": "2025-11-20",
        "end_date": null,
        "is_high_risk": false,
        "requires_monitoring": false
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Check facility access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required = ['medication_name', 'dose', 'route', 'frequency', 'prescribing_physician']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Create medication
    medication = Medication(
        patient_id=patient_id,
        medication_name=data['medication_name'],
        generic_name=data.get('generic_name'),
        dose=data['dose'],
        route=data['route'],
        frequency=data['frequency'],
        frequency_times_per_day=data.get('frequency_times_per_day'),
        time_of_day=data.get('time_of_day'),
        is_prn=data.get('is_prn', False),
        prn_indication=data.get('prn_indication'),
        prescribing_physician=data['prescribing_physician'],
        indication=data.get('indication'),
        special_instructions=data.get('special_instructions'),
        start_date=datetime.fromisoformat(data['start_date']).date() if data.get('start_date') else datetime.utcnow().date(),
        end_date=datetime.fromisoformat(data['end_date']).date() if data.get('end_date') else None,
        status='active',
        is_high_risk=data.get('is_high_risk', False),
        requires_monitoring=data.get('requires_monitoring', False)
    )
    
    db.session.add(medication)
    
    # Audit log
    AuditLog.log_action(
        user=user,
        action='CREATE',
        resource_type='Medication',
        resource_id=None,
        description=f'Added {medication.medication_name} {medication.dose} {medication.route} for patient {patient.medical_record_number}',
        phi_accessed=True
    )
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': medication.to_dict(),
        'message': 'Medication added successfully'
    }), 201


@bp.route('/medications/<int:medication_id>', methods=['PUT'])
@jwt_required()
@require_role(['RN', 'LPN', 'Pharmacist', 'Admin'])
def update_medication_full(medication_id):
    """
    Full update of medication details (per physician order modification).
    RNs/LPNs can modify medications per new physician orders.
    
    Request body: Same as create_medication
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    medication = Medication.query.get_or_404(medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    # Check facility access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    changes = []
    
    # Update fields if provided
    updatable_fields = {
        'medication_name': str,
        'generic_name': str,
        'dose': str,
        'route': str,
        'frequency': str,
        'frequency_times_per_day': int,
        'time_of_day': str,
        'is_prn': bool,
        'prn_indication': str,
        'prescribing_physician': str,
        'indication': str,
        'special_instructions': str,
        'is_high_risk': bool,
        'requires_monitoring': bool
    }
    
    for field, field_type in updatable_fields.items():
        if field in data:
            old_value = getattr(medication, field)
            new_value = data[field]
            if old_value != new_value:
                setattr(medication, field, new_value)
                changes.append(f'{field}: {old_value} → {new_value}')
    
    # Handle dates
    if 'start_date' in data:
        new_date = datetime.fromisoformat(data['start_date']).date()
        if medication.start_date != new_date:
            changes.append(f'start_date: {medication.start_date} → {new_date}')
            medication.start_date = new_date
    
    if 'end_date' in data:
        new_date = datetime.fromisoformat(data['end_date']).date() if data['end_date'] else None
        if medication.end_date != new_date:
            changes.append(f'end_date: {medication.end_date} → {new_date}')
            medication.end_date = new_date
    
    medication.updated_at = datetime.utcnow()
    
    # Audit log
    AuditLog.log_action(
        user=user,
        action='UPDATE',
        resource_type='Medication',
        resource_id=medication_id,
        description=f'Modified {medication.medication_name} for patient {patient.medical_record_number}: {"; ".join(changes)}',
        phi_accessed=True
    )
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': medication.to_dict(),
        'message': 'Medication updated successfully',
        'changes': changes
    })


@bp.route('/medications/<int:medication_id>/discontinue', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Pharmacist', 'Admin'])
def discontinue_medication(medication_id):
    """
    Discontinue a medication (per physician order).
    This marks the medication as discontinued but DOES NOT delete it from the record.
    All historical data is preserved per legal requirements.
    
    Request body:
    {
        "reason": "Per MD order - condition resolved",
        "discontinue_date": "2025-11-20"  // optional, defaults to today
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    medication = Medication.query.get_or_404(medication_id)
    patient = Patient.query.get(medication.patient_id)
    
    # Check facility access
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    if medication.status == 'discontinued':
        return jsonify({'error': 'Medication is already discontinued'}), 400
    
    data = request.get_json() or {}
    reason = data.get('reason', 'Discontinued per order')
    
    # Mark as discontinued
    medication.status = 'discontinued'
    medication.end_date = datetime.fromisoformat(data['discontinue_date']).date() if data.get('discontinue_date') else datetime.utcnow().date()
    
    # Add discontinuation note to instructions
    if medication.special_instructions:
        medication.special_instructions += f'\n\nDISCONTINUED {medication.end_date}: {reason}'
    else:
        medication.special_instructions = f'DISCONTINUED {medication.end_date}: {reason}'
    
    medication.updated_at = datetime.utcnow()
    
    # Audit log
    AuditLog.log_action(
        user=user,
        action='UPDATE',
        resource_type='Medication',
        resource_id=medication_id,
        description=f'Discontinued {medication.medication_name} for patient {patient.medical_record_number}: {reason}',
        phi_accessed=True
    )
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': medication.to_dict(),
        'message': 'Medication discontinued successfully'
    })
