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


def init_app(app):
    """Register blueprint with app."""
    app.register_blueprint(bp)
