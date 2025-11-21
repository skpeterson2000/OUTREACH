"""Medication reconciliation routes - care transition safety."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from app import db
from app.models import (
    MedicationReconciliation, MedicationDiscrepancy, 
    PharmacistIntervention, Patient, User, Medication,
    AuditLog
)
from app.utils.permissions import require_role

bp = Blueprint('reconciliation', __name__, url_prefix='/api')


@bp.route('/patients/<int:patient_id>/reconciliations', methods=['GET'])
@jwt_required()
def get_patient_reconciliations(patient_id):
    """
    Get medication reconciliation history for patient.
    
    Query params:
    - status: Filter by status
    - type: Filter by reconciliation type
    - days: Look back days (default 90)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check patient access
    patient = Patient.query.get_or_404(patient_id)
    if patient.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Parse filters
    status = request.args.get('status')
    rec_type = request.args.get('type')
    days = int(request.args.get('days', 90))
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = MedicationReconciliation.query.filter(
        and_(
            MedicationReconciliation.patient_id == patient_id,
            MedicationReconciliation.created_at >= cutoff_date
        )
    )
    
    if status:
        query = query.filter_by(status=status)
    
    if rec_type:
        query = query.filter_by(reconciliation_type=rec_type)
    
    reconciliations = query.order_by(
        MedicationReconciliation.created_at.desc()
    ).all()
    
    return jsonify({
        'status': 'success',
        'data': [rec.to_dict() for rec in reconciliations],
        'count': len(reconciliations),
        'patient_id': patient_id
    })


@bp.route('/patients/<int:patient_id>/reconciliations', methods=['POST'])
@jwt_required()
@require_role(['RN', 'Admin', 'Pharmacist'])
def create_reconciliation(patient_id):
    """
    Start new medication reconciliation.
    
    Request body:
    {
        "reconciliation_type": "ADMISSION",
        "transition_from": "St. Mary's Hospital",
        "transition_to": "Sunrise TCU",
        "source_document_type": "Hospital discharge summary",
        "source_document_date": "2025-11-18",
        "source_medications": [
            {
                "name": "Metformin",
                "dose": "500mg",
                "frequency": "BID",
                "route": "PO"
            }
        ],
        "clinical_summary": "Patient admitted post-MI, medication regimen changed"
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
    if not data.get('reconciliation_type'):
        return jsonify({'error': 'reconciliation_type is required'}), 400
    
    valid_types = ['ADMISSION', 'TRANSFER', 'DISCHARGE', 'ROUTINE_REVIEW']
    if data['reconciliation_type'] not in valid_types:
        return jsonify({'error': f'reconciliation_type must be one of: {", ".join(valid_types)}'}), 400
    
    if not data.get('source_medications'):
        return jsonify({'error': 'source_medications is required'}), 400
    
    try:
        # Get current active medications
        current_meds = Medication.query.filter_by(
            patient_id=patient_id,
            status='active'
        ).all()
        
        current_meds_list = [
            {
                'id': med.id,
                'name': med.name,
                'dose': med.dose,
                'frequency': med.frequency,
                'route': med.route,
                'prescribing_physician': med.prescribing_physician
            }
            for med in current_meds
        ]
        
        # Parse source document date
        source_date = None
        if data.get('source_document_date'):
            source_date = datetime.fromisoformat(data['source_document_date']).date()
        
        # Create reconciliation
        reconciliation = MedicationReconciliation(
            patient_id=patient_id,
            facility_id=patient.facility_id,
            reconciliation_type=data['reconciliation_type'],
            transition_from=data.get('transition_from'),
            transition_to=data.get('transition_to'),
            source_document_type=data.get('source_document_type'),
            source_document_date=source_date,
            source_medications=data['source_medications'],
            current_medications=current_meds_list,
            clinical_summary=data.get('clinical_summary'),
            initiated_by_user_id=current_user_id,
            status='IN_REVIEW'
        )
        
        db.session.add(reconciliation)
        db.session.flush()
        
        # Auto-detect discrepancies
        discrepancies = _detect_discrepancies(reconciliation)
        
        # Update reconciliation with discrepancy counts
        reconciliation.discrepancies_count = len(discrepancies)
        reconciliation.high_risk_discrepancies = sum(
            1 for d in discrepancies if d.severity in ['HIGH', 'CRITICAL']
        )
        
        # Flag for pharmacist review if high-risk discrepancies
        if reconciliation.high_risk_discrepancies > 0 or data['reconciliation_type'] == 'ADMISSION':
            reconciliation.requires_pharmacist_review = True
            reconciliation.status = 'PHARMACIST_REVIEW'
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE',
            resource_type='MedicationReconciliation',
            resource_id=reconciliation.id,
            details=f'Started {data["reconciliation_type"]} reconciliation for patient {patient_id}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': reconciliation.to_dict(include_discrepancies=True),
            'message': f'Reconciliation started. {len(discrepancies)} discrepancy(ies) detected.',
            'requires_pharmacist_review': reconciliation.requires_pharmacist_review
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def _detect_discrepancies(reconciliation):
    """
    Auto-detect discrepancies between source and current medication lists.
    
    Returns list of MedicationDiscrepancy objects.
    """
    discrepancies = []
    source_meds = {med['name'].lower(): med for med in reconciliation.source_medications}
    current_meds = {med['name'].lower(): med for med in reconciliation.current_medications}
    
    # Check for discontinued medications (in source but not current)
    for med_name, source_med in source_meds.items():
        if med_name not in current_meds:
            # Check if intentionally discontinued or missing
            discrepancy = MedicationDiscrepancy(
                reconciliation_id=reconciliation.id,
                discrepancy_type='DISCONTINUED',
                severity=_assess_severity(source_med),
                medication_name=source_med['name'],
                source_details=source_med,
                current_details=None,
                clinical_concern=f"{source_med['name']} was prescribed in source document but is not in current medication list",
                potential_impact="Patient may not be receiving necessary medication therapy"
            )
            discrepancies.append(discrepancy)
            db.session.add(discrepancy)
    
    # Check for new medications (in current but not source)
    for med_name, current_med in current_meds.items():
        if med_name not in source_meds:
            discrepancy = MedicationDiscrepancy(
                reconciliation_id=reconciliation.id,
                discrepancy_type='NEW_MED',
                severity='MEDIUM',
                medication_name=current_med['name'],
                medication_id=current_med.get('id'),
                source_details=None,
                current_details=current_med,
                clinical_concern=f"{current_med['name']} is not documented in source medication list",
                potential_impact="Verify if this is a new order or was present but not documented"
            )
            discrepancies.append(discrepancy)
            db.session.add(discrepancy)
    
    # Check for dose/frequency changes (in both lists)
    for med_name in set(source_meds.keys()).intersection(current_meds.keys()):
        source_med = source_meds[med_name]
        current_med = current_meds[med_name]
        
        # Check dose changes
        if source_med.get('dose', '').lower() != current_med.get('dose', '').lower():
            discrepancy = MedicationDiscrepancy(
                reconciliation_id=reconciliation.id,
                discrepancy_type='DOSE_CHANGE',
                severity=_assess_severity(source_med),
                medication_name=source_med['name'],
                medication_id=current_med.get('id'),
                source_details=source_med,
                current_details=current_med,
                clinical_concern=f"Dose changed from {source_med.get('dose')} to {current_med.get('dose')}",
                potential_impact="Verify if dose change is intentional and appropriate"
            )
            discrepancies.append(discrepancy)
            db.session.add(discrepancy)
        
        # Check frequency changes
        if source_med.get('frequency', '').lower() != current_med.get('frequency', '').lower():
            discrepancy = MedicationDiscrepancy(
                reconciliation_id=reconciliation.id,
                discrepancy_type='FREQUENCY_CHANGE',
                severity='MEDIUM',
                medication_name=source_med['name'],
                medication_id=current_med.get('id'),
                source_details=source_med,
                current_details=current_med,
                clinical_concern=f"Frequency changed from {source_med.get('frequency')} to {current_med.get('frequency')}",
                potential_impact="Verify if frequency change is intentional"
            )
            discrepancies.append(discrepancy)
            db.session.add(discrepancy)
        
        # Check route changes
        if source_med.get('route', '').lower() != current_med.get('route', '').lower():
            discrepancy = MedicationDiscrepancy(
                reconciliation_id=reconciliation.id,
                discrepancy_type='ROUTE_CHANGE',
                severity='HIGH',
                medication_name=source_med['name'],
                medication_id=current_med.get('id'),
                source_details=source_med,
                current_details=current_med,
                clinical_concern=f"Route changed from {source_med.get('route')} to {current_med.get('route')}",
                potential_impact="Route changes can significantly affect medication efficacy and safety"
            )
            discrepancies.append(discrepancy)
            db.session.add(discrepancy)
    
    return discrepancies


def _assess_severity(medication):
    """Assess severity of medication discrepancy based on drug class."""
    high_risk_terms = [
        'warfarin', 'insulin', 'heparin', 'methotrexate', 
        'digoxin', 'phenytoin', 'lithium', 'opioid'
    ]
    
    med_name = medication.get('name', '').lower()
    
    for term in high_risk_terms:
        if term in med_name:
            return 'HIGH'
    
    return 'MEDIUM'


@bp.route('/reconciliations/<int:reconciliation_id>', methods=['GET'])
@jwt_required()
def get_reconciliation_details(reconciliation_id):
    """Get detailed reconciliation information including all discrepancies."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    reconciliation = MedicationReconciliation.query.get_or_404(reconciliation_id)
    
    # Check access
    if reconciliation.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Enrich with patient info
    result = reconciliation.to_dict(include_discrepancies=True)
    patient = Patient.query.get(reconciliation.patient_id)
    result['patient'] = {
        'id': patient.id,
        'name': f"{patient.first_name} {patient.last_name}",
        'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None
    }
    
    return jsonify({
        'status': 'success',
        'data': result
    })


@bp.route('/reconciliations/<int:reconciliation_id>/discrepancies', methods=['GET'])
@jwt_required()
def get_reconciliation_discrepancies(reconciliation_id):
    """Get all discrepancies for a reconciliation."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    reconciliation = MedicationReconciliation.query.get_or_404(reconciliation_id)
    
    # Check access
    if reconciliation.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Filter options
    severity = request.args.get('severity')
    unresolved_only = request.args.get('unresolved_only', 'false').lower() == 'true'
    
    query = MedicationDiscrepancy.query.filter_by(
        reconciliation_id=reconciliation_id
    )
    
    if severity:
        query = query.filter_by(severity=severity)
    
    if unresolved_only:
        query = query.filter_by(resolution_action='PENDING')
    
    discrepancies = query.order_by(
        MedicationDiscrepancy.severity.desc(),
        MedicationDiscrepancy.created_at
    ).all()
    
    return jsonify({
        'status': 'success',
        'data': [disc.to_dict() for disc in discrepancies],
        'count': len(discrepancies),
        'reconciliation_id': reconciliation_id
    })


@bp.route('/discrepancies/<int:discrepancy_id>/resolve', methods=['POST'])
@jwt_required()
@require_role(['RN', 'Admin', 'Pharmacist'])
def resolve_discrepancy(discrepancy_id):
    """
    Resolve a medication discrepancy.
    
    Request body:
    {
        "resolution_action": "ACCEPTED",
        "resolution_notes": "Dose increase appropriate due to A1C 8.2"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    discrepancy = MedicationDiscrepancy.query.get_or_404(discrepancy_id)
    reconciliation = MedicationReconciliation.query.get(discrepancy.reconciliation_id)
    
    # Check access
    if reconciliation.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Validate resolution action
    valid_actions = [
        'ACCEPTED', 'MODIFIED', 'DISCONTINUED', 
        'CLARIFICATION_NEEDED', 'PHARMACY_CONSULT', 'PENDING'
    ]
    
    if not data.get('resolution_action') or data['resolution_action'] not in valid_actions:
        return jsonify({
            'error': f'resolution_action must be one of: {", ".join(valid_actions)}'
        }), 400
    
    if not data.get('resolution_notes'):
        return jsonify({'error': 'resolution_notes required'}), 400
    
    try:
        discrepancy.resolution_action = data['resolution_action']
        discrepancy.resolution_notes = data['resolution_notes']
        discrepancy.resolved_by_user_id = current_user_id
        discrepancy.resolved_at = datetime.utcnow()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='MedicationDiscrepancy',
            resource_id=discrepancy.id,
            details=f'Resolved discrepancy as {data["resolution_action"]}: {discrepancy.medication_name}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': discrepancy.to_dict(),
            'message': 'Discrepancy resolved'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/reconciliations/<int:reconciliation_id>/complete', methods=['POST'])
@jwt_required()
@require_role(['RN', 'Admin', 'Pharmacist'])
def complete_reconciliation(reconciliation_id):
    """
    Mark reconciliation as complete.
    
    Request body:
    {
        "reconciliation_notes": "All discrepancies reviewed and resolved",
        "reconciled_medications": [...]  // Final medication list
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    reconciliation = MedicationReconciliation.query.get_or_404(reconciliation_id)
    
    # Check access
    if reconciliation.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if already completed
    if reconciliation.status == 'COMPLETED':
        return jsonify({'error': 'Reconciliation already completed'}), 400
    
    # Check for unresolved high-risk discrepancies
    unresolved_high_risk = MedicationDiscrepancy.query.filter(
        and_(
            MedicationDiscrepancy.reconciliation_id == reconciliation_id,
            MedicationDiscrepancy.severity.in_(['HIGH', 'CRITICAL']),
            MedicationDiscrepancy.resolution_action == 'PENDING'
        )
    ).count()
    
    if unresolved_high_risk > 0:
        return jsonify({
            'error': f'{unresolved_high_risk} high-risk discrepancy(ies) still unresolved',
            'requires_resolution': True
        }), 400
    
    data = request.get_json() or {}
    
    try:
        reconciliation.status = 'COMPLETED'
        reconciliation.completed_at = datetime.utcnow()
        reconciliation.reconciled_by_user_id = current_user_id
        reconciliation.reconciliation_notes = data.get('reconciliation_notes')
        
        # Update reconciled medication list if provided
        if data.get('reconciled_medications'):
            reconciliation.reconciled_medications = data['reconciled_medications']
        else:
            # Use current medications as reconciled list
            reconciliation.reconciled_medications = reconciliation.current_medications
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='MedicationReconciliation',
            resource_id=reconciliation.id,
            details=f'Completed medication reconciliation for patient {reconciliation.patient_id}',
            contains_phi=True,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': reconciliation.to_dict(include_discrepancies=True),
            'message': 'Reconciliation completed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/reconciliations/<int:reconciliation_id>/request-pharmacist', methods=['POST'])
@jwt_required()
@require_role(['RN', 'LPN', 'Admin'])
def request_pharmacist_review(reconciliation_id):
    """
    Request pharmacist review of reconciliation.
    
    Request body:
    {
        "reason": "Multiple high-risk medication changes, need pharmacist input"
    }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    reconciliation = MedicationReconciliation.query.get_or_404(reconciliation_id)
    
    # Check access
    if reconciliation.facility_id != user.facility_id and user.role != 'Admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json() or {}
    
    try:
        reconciliation.requires_pharmacist_review = True
        reconciliation.status = 'PHARMACIST_REVIEW'
        
        # Add note about pharmacist review request
        if data.get('reason'):
            if reconciliation.reconciliation_notes:
                reconciliation.reconciliation_notes += f"\n\n[Pharmacist review requested by {user.full_name}]: {data['reason']}"
            else:
                reconciliation.reconciliation_notes = f"[Pharmacist review requested by {user.full_name}]: {data['reason']}"
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user_id,
            action='UPDATE',
            resource_type='MedicationReconciliation',
            resource_id=reconciliation.id,
            details=f'Requested pharmacist review for reconciliation {reconciliation_id}',
            contains_phi=False,
            facility_id=user.facility_id
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': reconciliation.to_dict(),
            'message': 'Pharmacist review requested'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/reconciliations/pending', methods=['GET'])
@jwt_required()
def get_pending_reconciliations():
    """
    Get pending reconciliations for facility.
    
    Query params:
    - pharmacist_review: Only show those needing pharmacist review
    - overdue: Only show overdue reconciliations
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    pharmacist_review_only = request.args.get('pharmacist_review', 'false').lower() == 'true'
    overdue_only = request.args.get('overdue', 'false').lower() == 'true'
    
    # Build query
    query = MedicationReconciliation.query.filter(
        and_(
            MedicationReconciliation.facility_id == user.facility_id,
            MedicationReconciliation.status.in_(['IN_REVIEW', 'PHARMACIST_REVIEW', 'PENDING'])
        )
    )
    
    if pharmacist_review_only:
        query = query.filter_by(requires_pharmacist_review=True)
    
    reconciliations = query.order_by(
        MedicationReconciliation.created_at.desc()
    ).all()
    
    # Filter overdue if requested
    if overdue_only:
        reconciliations = [rec for rec in reconciliations if rec.is_overdue]
    
    # Enrich with patient info
    result = []
    for rec in reconciliations:
        rec_dict = rec.to_dict()
        patient = Patient.query.get(rec.patient_id)
        rec_dict['patient_name'] = f"{patient.first_name} {patient.last_name}"
        rec_dict['patient_room'] = getattr(patient, 'room_number', None)
        result.append(rec_dict)
    
    return jsonify({
        'status': 'success',
        'data': result,
        'count': len(result),
        'filters': {
            'pharmacist_review': pharmacist_review_only,
            'overdue': overdue_only
        }
    })
