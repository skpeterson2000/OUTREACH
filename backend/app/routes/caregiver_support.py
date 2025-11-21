"""Caregiver Support API endpoints."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from app import db
from app.models.user import User
from app.models.caregiver_support import (
    CaregiverStressAssessment, CaregiverIntervention,
    CaregiverResource, StaffWellnessDashboard
)
from app.models.audit_log import AuditLog

bp = Blueprint('caregiver_support', __name__, url_prefix='/api/caregiver-support')


@bp.route('/assessments', methods=['POST'])
@jwt_required()
def create_assessment():
    """Create a new caregiver stress assessment."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('assess'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('caregiver_type') or not data.get('assessment_data'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Create assessment
    assessment = CaregiverStressAssessment(
        caregiver_type=data['caregiver_type'],
        patient_id=data.get('patient_id'),
        caregiver_name=data.get('caregiver_name'),
        caregiver_relationship=data.get('caregiver_relationship'),
        staff_id=data.get('staff_id'),
        assessed_by=user_id,
        assessment_data=data['assessment_data'],
        strain_index_score=data.get('strain_index_score'),
        burnout_score=data.get('burnout_score'),
        perceived_stress_score=data.get('perceived_stress_score'),
        risk_level=data.get('risk_level'),
        social_support_adequate=data.get('social_support_adequate'),
        respite_care_available=data.get('respite_care_available'),
        financial_concerns=data.get('financial_concerns'),
        identified_stressors=data.get('identified_stressors', []),
        protective_factors=data.get('protective_factors', []),
        warning_signs=data.get('warning_signs'),
        recommended_interventions=data.get('recommended_interventions', []),
        referrals_made=data.get('referrals_made', []),
        requires_immediate_intervention=data.get('requires_immediate_intervention', False)
    )
    
    # Set follow-up date based on risk
    if assessment.risk_level in ['high', 'critical']:
        from datetime import timedelta
        assessment.follow_up_date = date.today() + timedelta(days=7)
    elif assessment.risk_level == 'moderate':
        from datetime import timedelta
        assessment.follow_up_date = date.today() + timedelta(days=30)
    
    db.session.add(assessment)
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        user=user,
        action='create',
        resource_type='caregiver_assessment',
        resource_id=assessment.id,
        patient_id=assessment.patient_id,
        description=f'Caregiver stress assessment: {assessment.risk_level} risk',
        request=request
    )
    
    return jsonify(assessment.to_dict()), 201


@bp.route('/assessments/<int:assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment(assessment_id):
    """Get specific caregiver assessment."""
    assessment = CaregiverStressAssessment.query.get(assessment_id)
    
    if not assessment:
        return jsonify({'error': 'Assessment not found'}), 404
    
    return jsonify(assessment.to_dict()), 200


@bp.route('/assessments/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient_caregiver_assessments(patient_id):
    """Get all assessments for a patient's family caregiver."""
    assessments = CaregiverStressAssessment.query.filter_by(
        patient_id=patient_id,
        caregiver_type='family_caregiver'
    ).order_by(CaregiverStressAssessment.assessment_date.desc()).all()
    
    return jsonify([a.to_dict() for a in assessments]), 200


@bp.route('/assessments/staff/<int:staff_id>', methods=['GET'])
@jwt_required()
def get_staff_assessments(staff_id):
    """Get all assessments for a staff member."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Staff can view their own, managers/admins can view any
    if current_user_id != staff_id and not current_user.has_permission('supervise'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    assessments = CaregiverStressAssessment.query.filter_by(
        staff_id=staff_id
    ).order_by(CaregiverStressAssessment.assessment_date.desc()).all()
    
    return jsonify([a.to_dict() for a in assessments]), 200


@bp.route('/interventions', methods=['POST'])
@jwt_required()
def create_intervention():
    """Create a caregiver support intervention."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    data = request.get_json()
    
    if not data.get('assessment_id') or not data.get('intervention_type'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    intervention = CaregiverIntervention(
        assessment_id=data['assessment_id'],
        intervention_type=data['intervention_type'],
        intervention_category=data.get('intervention_category'),
        description=data['description'],
        provided_by=user_id,
        initiated_date=date.today(),
        target_completion_date=data.get('target_completion_date'),
        status='active',
        estimated_cost=data.get('estimated_cost')
    )
    
    db.session.add(intervention)
    db.session.commit()
    
    AuditLog.log_action(
        user=user,
        action='create',
        resource_type='caregiver_intervention',
        resource_id=intervention.id,
        description=f'Intervention: {intervention.intervention_type}',
        request=request
    )
    
    return jsonify(intervention.to_dict()), 201


@bp.route('/interventions/<int:intervention_id>', methods=['PUT'])
@jwt_required()
def update_intervention(intervention_id):
    """Update intervention status and outcomes."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    intervention = CaregiverIntervention.query.get(intervention_id)
    
    if not intervention:
        return jsonify({'error': 'Intervention not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'status' in data:
        intervention.status = data['status']
    if 'completed_date' in data:
        intervention.completed_date = data['completed_date']
    if 'caregiver_satisfaction' in data:
        intervention.caregiver_satisfaction = data['caregiver_satisfaction']
    if 'perceived_helpfulness' in data:
        intervention.perceived_helpfulness = data['perceived_helpfulness']
    if 'barriers_encountered' in data:
        intervention.barriers_encountered = data['barriers_encountered']
    if 'outcome_notes' in data:
        intervention.outcome_notes = data['outcome_notes']
    if 'actual_cost' in data:
        intervention.actual_cost = data['actual_cost']
    
    db.session.commit()
    
    return jsonify(intervention.to_dict()), 200


@bp.route('/resources', methods=['GET'])
@jwt_required()
def get_resources():
    """Get caregiver support resources."""
    resource_type = request.args.get('type')
    category = request.args.get('category')
    target_audience = request.args.get('audience')
    
    query = CaregiverResource.query.filter_by(is_active=True)
    
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    if category:
        query = query.filter_by(category=category)
    if target_audience:
        query = query.filter_by(target_audience=target_audience)
    
    # Featured resources first
    resources = query.order_by(
        CaregiverResource.featured.desc(),
        CaregiverResource.average_rating.desc()
    ).all()
    
    return jsonify([r.to_dict() for r in resources]), 200


@bp.route('/resources/<int:resource_id>/access', methods=['POST'])
@jwt_required()
def track_resource_access(resource_id):
    """Track when a resource is accessed (for analytics)."""
    resource = CaregiverResource.query.get(resource_id)
    
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    resource.times_accessed += 1
    db.session.commit()
    
    return jsonify({'message': 'Access tracked'}), 200


@bp.route('/dashboard/team-wellness', methods=['GET'])
@jwt_required()
def team_wellness_dashboard():
    """
    Get organizational wellness metrics.
    Requires supervisor or admin permissions.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('supervise'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    department = request.args.get('department')
    timeframe = int(request.args.get('timeframe_days', 90))
    
    metrics = StaffWellnessDashboard.calculate_team_burnout_risk(
        department=department,
        timeframe_days=timeframe
    )
    
    return jsonify(metrics), 200


@bp.route('/dashboard/turnover-risk', methods=['GET'])
@jwt_required()
def turnover_risk_analysis():
    """
    Identify staff at risk of leaving.
    Requires supervisor or admin permissions.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('supervise'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    high_risk_staff = StaffWellnessDashboard.predict_turnover_risk()
    
    return jsonify({
        'high_risk_count': len(high_risk_staff),
        'high_risk_staff': high_risk_staff
    }), 200


@bp.route('/dashboard/intervention-effectiveness', methods=['GET'])
@jwt_required()
def intervention_effectiveness():
    """
    Analyze effectiveness of interventions.
    Helps optimize support strategies.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('supervise'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    intervention_type = request.args.get('type')
    timeframe = int(request.args.get('timeframe_days', 180))
    
    report = StaffWellnessDashboard.intervention_effectiveness_report(
        intervention_type=intervention_type,
        timeframe_days=timeframe
    )
    
    return jsonify(report), 200


@bp.route('/alerts/high-risk', methods=['GET'])
@jwt_required()
def high_risk_alerts():
    """
    Get list of caregivers requiring immediate intervention.
    Real-time alert system.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.has_permission('supervise'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    # Get recent high-risk assessments without completed interventions
    from datetime import timedelta
    recent_cutoff = datetime.utcnow() - timedelta(days=14)
    
    high_risk = CaregiverStressAssessment.query.filter(
        CaregiverStressAssessment.risk_level.in_(['high', 'critical']),
        CaregiverStressAssessment.assessment_date >= recent_cutoff,
        CaregiverStressAssessment.requires_immediate_intervention == True
    ).order_by(CaregiverStressAssessment.assessment_date.desc()).all()
    
    alerts = []
    for assessment in high_risk:
        # Check if intervention already in progress
        active_interventions = CaregiverIntervention.query.filter_by(
            assessment_id=assessment.id,
            status='active'
        ).count()
        
        if active_interventions == 0:
            alerts.append({
                'assessment_id': assessment.id,
                'caregiver_type': assessment.caregiver_type,
                'risk_level': assessment.risk_level,
                'assessment_date': assessment.assessment_date.isoformat(),
                'identified_stressors': assessment.identified_stressors,
                'recommended_interventions': assessment.recommended_interventions,
                'urgency': 'immediate' if assessment.risk_level == 'critical' else 'high'
            })
    
    return jsonify({
        'alert_count': len(alerts),
        'alerts': alerts
    }), 200
