"""Care Plan API routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app import db
from app.models import (
    CarePlan, NursingIntervention, PhysicianOrder, AssistanceTask,
    InterventionCompletion, OrderCompletion, TaskCompletion,
    Patient, User
)
from app.utils.logging import app_logger

bp = Blueprint('care_plans', __name__, url_prefix='/api/care-plans')


@bp.route('', methods=['GET'])
@jwt_required()
def get_care_plans():
    """Get care plans with optional filtering."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        patient_id = request.args.get('patient_id', type=int)
        status = request.args.get('status')
        
        query = CarePlan.query.filter_by(facility_id=user.facility_id)
        
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        
        if status:
            query = query.filter_by(status=status)
        
        care_plans = query.order_by(CarePlan.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [cp.to_dict() for cp in care_plans]
        }), 200
        
    except Exception as e:
        app_logger.error(f"Error getting care plans: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to get care plans'}), 500


@bp.route('/<int:care_plan_id>', methods=['GET'])
@jwt_required()
def get_care_plan(care_plan_id):
    """Get a single care plan with related items."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        care_plan = CarePlan.query.filter_by(
            id=care_plan_id,
            facility_id=user.facility_id
        ).first()
        
        if not care_plan:
            return jsonify({'status': 'error', 'message': 'Care plan not found'}), 404
        
        # Get related items
        interventions = NursingIntervention.query.filter_by(care_plan_id=care_plan_id).all()
        orders = PhysicianOrder.query.filter_by(care_plan_id=care_plan_id).all()
        tasks = AssistanceTask.query.filter_by(care_plan_id=care_plan_id).all()
        
        return jsonify({
            'status': 'success',
            'data': {
                'care_plan': care_plan.to_dict(),
                'interventions': [i.to_dict() for i in interventions],
                'orders': [o.to_dict() for o in orders],
                'tasks': [t.to_dict() for t in tasks]
            }
        }), 200
        
    except Exception as e:
        app_logger.error(f"Error getting care plan {care_plan_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to get care plan'}), 500


@bp.route('', methods=['POST'])
@jwt_required()
def create_care_plan():
    """Create a new care plan."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        # Check permission
        if user.role not in ['RN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'Only RNs and Admins can create care plans'}), 403
        
        data = request.json
        
        # Validate patient exists and is in same facility
        patient = Patient.query.filter_by(
            id=data['patient_id'],
            facility_id=user.facility_id
        ).first()
        
        if not patient:
            return jsonify({'status': 'error', 'message': 'Patient not found'}), 404
        
        # Create care plan
        care_plan = CarePlan(
            patient_id=data['patient_id'],
            facility_id=user.facility_id,
            plan_name=data['plan_name'],
            plan_type=data.get('plan_type'),
            primary_diagnosis=data.get('primary_diagnosis'),
            care_goals=data.get('care_goals'),
            start_date=datetime.fromisoformat(data['start_date']).date(),
            target_end_date=datetime.fromisoformat(data['target_end_date']).date() if data.get('target_end_date') else None,
            primary_nurse_id=data.get('primary_nurse_id', user.id),
            physician_name=data.get('physician_name'),
            physician_phone=data.get('physician_phone'),
            clinical_summary=data.get('clinical_summary'),
            created_by_user_id=user.id,
            status='active',
            next_review_date=(datetime.utcnow() + timedelta(days=30)).date()
        )
        
        db.session.add(care_plan)
        db.session.commit()
        
        app_logger.info(f"Care plan {care_plan.id} created by user {user.id} for patient {patient.id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Care plan created',
            'data': care_plan.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error creating care plan: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to create care plan'}), 500


@bp.route('/<int:care_plan_id>', methods=['PUT'])
@jwt_required()
def update_care_plan(care_plan_id):
    """Update a care plan."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        if user.role not in ['RN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'Only RNs and Admins can update care plans'}), 403
        
        care_plan = CarePlan.query.filter_by(
            id=care_plan_id,
            facility_id=user.facility_id
        ).first()
        
        if not care_plan:
            return jsonify({'status': 'error', 'message': 'Care plan not found'}), 404
        
        data = request.json
        
        # Update allowed fields
        if 'plan_name' in data:
            care_plan.plan_name = data['plan_name']
        if 'plan_type' in data:
            care_plan.plan_type = data['plan_type']
        if 'care_goals' in data:
            care_plan.care_goals = data['care_goals']
        if 'clinical_summary' in data:
            care_plan.clinical_summary = data['clinical_summary']
        if 'discharge_plan' in data:
            care_plan.discharge_plan = data['discharge_plan']
        if 'status' in data:
            care_plan.status = data['status']
            if data['status'] == 'completed':
                care_plan.actual_end_date = datetime.utcnow().date()
        
        care_plan.updated_at = datetime.utcnow()
        db.session.commit()
        
        app_logger.info(f"Care plan {care_plan_id} updated by user {user.id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Care plan updated',
            'data': care_plan.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error updating care plan {care_plan_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to update care plan'}), 500


# Nursing Interventions
@bp.route('/<int:care_plan_id>/interventions', methods=['POST'])
@jwt_required()
def create_intervention(care_plan_id):
    """Add a nursing intervention to a care plan."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        if user.role not in ['RN', 'LPN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'Only nurses can create interventions'}), 403
        
        care_plan = CarePlan.query.filter_by(
            id=care_plan_id,
            facility_id=user.facility_id
        ).first()
        
        if not care_plan:
            return jsonify({'status': 'error', 'message': 'Care plan not found'}), 404
        
        data = request.json
        
        intervention = NursingIntervention(
            care_plan_id=care_plan_id,
            patient_id=care_plan.patient_id,
            intervention_type=data['intervention_type'],
            intervention_name=data['intervention_name'],
            description=data['description'],
            rationale=data.get('rationale'),
            frequency=data.get('frequency'),
            frequency_times_per_day=data.get('frequency_times_per_day'),
            scheduled_times=data.get('scheduled_times'),
            prn_indication=data.get('prn_indication'),
            start_date=datetime.fromisoformat(data['start_date']).date(),
            end_date=datetime.fromisoformat(data['end_date']).date() if data.get('end_date') else None,
            assigned_role=data.get('assigned_role'),
            assigned_user_id=data.get('assigned_user_id'),
            requires_rn=data.get('requires_rn', False),
            priority=data.get('priority', 'routine'),
            expected_outcome=data.get('expected_outcome'),
            created_by_user_id=user.id
        )
        
        db.session.add(intervention)
        db.session.commit()
        
        app_logger.info(f"Intervention {intervention.id} created for care plan {care_plan_id} by user {user.id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Intervention created',
            'data': intervention.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error creating intervention: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to create intervention'}), 500


@bp.route('/interventions/<int:intervention_id>', methods=['PUT'])
@jwt_required()
def update_intervention(intervention_id):
    """Update a nursing intervention."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        if user.role not in ['RN', 'LPN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'Only nurses can update interventions'}), 403
        
        intervention = NursingIntervention.query.get(intervention_id)
        if not intervention:
            return jsonify({'status': 'error', 'message': 'Intervention not found'}), 404
        
        data = request.json
        
        if 'status' in data:
            intervention.status = data['status']
            if data['status'] == 'discontinued':
                intervention.discontinued_at = datetime.utcnow()
                intervention.discontinued_by_user_id = user.id
                intervention.discontinued_reason = data.get('discontinued_reason')
        
        if 'frequency' in data:
            intervention.frequency = data['frequency']
        if 'assigned_user_id' in data:
            intervention.assigned_user_id = data['assigned_user_id']
        
        intervention.updated_at = datetime.utcnow()
        db.session.commit()
        
        app_logger.info(f"Intervention {intervention_id} updated by user {user.id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Intervention updated',
            'data': intervention.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error updating intervention: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to update intervention'}), 500


@bp.route('/interventions/<int:intervention_id>/complete', methods=['POST'])
@jwt_required()
def complete_intervention(intervention_id):
    """Document completion of a nursing intervention."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        intervention = NursingIntervention.query.get(intervention_id)
        if not intervention:
            return jsonify({'status': 'error', 'message': 'Intervention not found'}), 404
        
        # Check permissions
        if intervention.requires_rn and user.role not in ['RN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'This intervention requires an RN'}), 403
        
        if user.role not in ['RN', 'LPN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'Only licensed nurses can complete interventions'}), 403
        
        data = request.json
        
        completion = InterventionCompletion(
            intervention_id=intervention_id,
            patient_id=intervention.patient_id,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else datetime.utcnow(),
            completed_by_user_id=user.id,
            status=data['status'],
            completion_notes=data['completion_notes'],
            patient_response=data.get('patient_response'),
            outcome_achieved=data.get('outcome_achieved'),
            outcome_notes=data.get('outcome_notes'),
            reason_not_done=data.get('reason_not_done'),
            duration_minutes=data.get('duration_minutes'),
            requires_follow_up=data.get('requires_follow_up', False),
            follow_up_notes=data.get('follow_up_notes')
        )
        
        db.session.add(completion)
        db.session.commit()
        
        app_logger.info(f"Intervention {intervention_id} completed by user {user.id}: {data['status']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Intervention completion documented',
            'data': completion.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error completing intervention: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to document completion'}), 500


# Physician Orders
@bp.route('/<int:care_plan_id>/orders', methods=['POST'])
@jwt_required()
def create_order(care_plan_id):
    """Add a physician order to a care plan."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        if user.role not in ['RN', 'LPN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'Only nurses can enter physician orders'}), 403
        
        care_plan = CarePlan.query.filter_by(
            id=care_plan_id,
            facility_id=user.facility_id
        ).first()
        
        if not care_plan:
            return jsonify({'status': 'error', 'message': 'Care plan not found'}), 404
        
        data = request.json
        
        order = PhysicianOrder(
            care_plan_id=care_plan_id,
            patient_id=care_plan.patient_id,
            order_type=data['order_type'],
            order_category=data.get('order_category'),
            order_text=data['order_text'],
            ordering_physician=data['ordering_physician'],
            physician_npi=data.get('physician_npi'),
            physician_phone=data.get('physician_phone'),
            order_date=datetime.fromisoformat(data['order_date']),
            start_date=datetime.fromisoformat(data['start_date']).date(),
            end_date=datetime.fromisoformat(data['end_date']).date() if data.get('end_date') else None,
            frequency=data.get('frequency'),
            duration=data.get('duration'),
            prn_indication=data.get('prn_indication'),
            priority=data.get('priority', 'routine'),
            special_instructions=data.get('special_instructions'),
            created_by_user_id=user.id
        )
        
        db.session.add(order)
        db.session.commit()
        
        app_logger.info(f"Physician order {order.id} created for care plan {care_plan_id} by user {user.id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Physician order created',
            'data': order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error creating physician order: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to create order'}), 500


@bp.route('/orders/<int:order_id>/verify', methods=['POST'])
@jwt_required()
def verify_order(order_id):
    """Verify a physician order."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        if user.role not in ['RN', 'LPN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'Only licensed nurses can verify orders'}), 403
        
        order = PhysicianOrder.query.get(order_id)
        if not order:
            return jsonify({'status': 'error', 'message': 'Order not found'}), 404
        
        data = request.json
        
        order.verification_status = data.get('verification_status', 'verified')
        order.verified_by_user_id = user.id
        order.verified_at = datetime.utcnow()
        
        if order.verification_status == 'verified':
            order.status = 'active'
        
        db.session.commit()
        
        app_logger.info(f"Order {order_id} verified by user {user.id}: {order.verification_status}")
        
        return jsonify({
            'status': 'success',
            'message': 'Order verified',
            'data': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error verifying order: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to verify order'}), 500


@bp.route('/orders/<int:order_id>/complete', methods=['POST'])
@jwt_required()
def complete_order(order_id):
    """Document completion of a physician order."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        order = PhysicianOrder.query.get(order_id)
        if not order:
            return jsonify({'status': 'error', 'message': 'Order not found'}), 404
        
        data = request.json
        
        completion = OrderCompletion(
            order_id=order_id,
            patient_id=order.patient_id,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else datetime.utcnow(),
            completed_by_user_id=user.id,
            status=data['status'],
            completion_notes=data['completion_notes'],
            results=data.get('results'),
            reason_not_done=data.get('reason_not_done'),
            requires_follow_up=data.get('requires_follow_up', False),
            follow_up_notes=data.get('follow_up_notes'),
            physician_notified=data.get('physician_notified', False),
            notification_notes=data.get('notification_notes')
        )
        
        db.session.add(completion)
        db.session.commit()
        
        app_logger.info(f"Order {order_id} completed by user {user.id}: {data['status']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Order completion documented',
            'data': completion.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error completing order: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to document completion'}), 500


# Assistance Tasks
@bp.route('/<int:care_plan_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(care_plan_id):
    """Add an assistance task to a care plan."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        if user.role not in ['RN', 'LPN', 'Admin']:
            return jsonify({'status': 'error', 'message': 'Only nurses can create tasks'}), 403
        
        care_plan = CarePlan.query.filter_by(
            id=care_plan_id,
            facility_id=user.facility_id
        ).first()
        
        if not care_plan:
            return jsonify({'status': 'error', 'message': 'Care plan not found'}), 404
        
        data = request.json
        
        task = AssistanceTask(
            care_plan_id=care_plan_id,
            patient_id=care_plan.patient_id,
            task_category=data['task_category'],
            task_name=data['task_name'],
            description=data['description'],
            adl_type=data.get('adl_type'),
            assistance_level=data.get('assistance_level'),
            frequency=data['frequency'],
            frequency_times_per_day=data.get('frequency_times_per_day'),
            scheduled_times=data.get('scheduled_times'),
            estimated_duration_minutes=data.get('estimated_duration_minutes'),
            start_date=datetime.fromisoformat(data['start_date']).date(),
            end_date=datetime.fromisoformat(data['end_date']).date() if data.get('end_date') else None,
            assigned_role=data['assigned_role'],
            assigned_user_id=data.get('assigned_user_id'),
            requires_two_person_assist=data.get('requires_two_person_assist', False),
            priority=data.get('priority', 'routine'),
            equipment_needed=data.get('equipment_needed'),
            safety_precautions=data.get('safety_precautions'),
            fall_risk_precautions=data.get('fall_risk_precautions', False),
            patient_preferences=data.get('patient_preferences'),
            created_by_user_id=user.id
        )
        
        db.session.add(task)
        db.session.commit()
        
        app_logger.info(f"Task {task.id} created for care plan {care_plan_id} by user {user.id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Task created',
            'data': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error creating task: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to create task'}), 500


@bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@jwt_required()
def complete_task(task_id):
    """Document completion of an assistance task."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    try:
        task = AssistanceTask.query.get(task_id)
        if not task:
            return jsonify({'status': 'error', 'message': 'Task not found'}), 404
        
        # Check if user's role matches task assignment
        if task.assigned_role and user.role != task.assigned_role and user.role not in ['RN', 'Admin']:
            return jsonify({'status': 'error', 'message': f'This task is assigned to {task.assigned_role}'}), 403
        
        data = request.json
        
        completion = TaskCompletion(
            task_id=task_id,
            patient_id=task.patient_id,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else datetime.utcnow(),
            completed_by_user_id=user.id,
            assisted_by_user_id=data.get('assisted_by_user_id'),
            status=data['status'],
            completion_notes=data.get('completion_notes'),
            patient_tolerance=data.get('patient_tolerance'),
            patient_participation=data.get('patient_participation'),
            safety_incidents=data.get('safety_incidents', False),
            incident_notes=data.get('incident_notes'),
            reason_not_done=data.get('reason_not_done'),
            duration_minutes=data.get('duration_minutes')
        )
        
        db.session.add(completion)
        db.session.commit()
        
        app_logger.info(f"Task {task_id} completed by user {user.id}: {data['status']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Task completion documented',
            'data': completion.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Error completing task: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to document completion'}), 500


# Get completions
@bp.route('/interventions/<int:intervention_id>/completions', methods=['GET'])
@jwt_required()
def get_intervention_completions(intervention_id):
    """Get completion history for an intervention."""
    try:
        completions = InterventionCompletion.query.filter_by(
            intervention_id=intervention_id
        ).order_by(InterventionCompletion.completed_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [c.to_dict() for c in completions]
        }), 200
        
    except Exception as e:
        app_logger.error(f"Error getting intervention completions: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to get completions'}), 500


@bp.route('/tasks/<int:task_id>/completions', methods=['GET'])
@jwt_required()
def get_task_completions(task_id):
    """Get completion history for a task."""
    try:
        completions = TaskCompletion.query.filter_by(
            task_id=task_id
        ).order_by(TaskCompletion.completed_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [c.to_dict() for c in completions]
        }), 200
        
    except Exception as e:
        app_logger.error(f"Error getting task completions: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to get completions'}), 500


def init_app(app):
    """Register blueprint with app."""
    app.register_blueprint(bp)
