"""User management routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.audit_log import AuditLog

bp = Blueprint('users', __name__, url_prefix='/api/users')


def require_permission(permission):
    """Decorator to check user permissions."""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or not user.has_permission(permission):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@bp.route('', methods=['GET'])
@require_permission('all')
def get_users():
    """Get all users (admin only)."""
    users = User.query.filter_by(is_active=True).all()
    return jsonify([user.to_dict() for user in users]), 200


@bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get specific user."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Users can view their own profile, admins can view any
    if current_user_id != user_id and not current_user.has_permission('all'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@bp.route('', methods=['POST'])
@require_permission('all')
def create_user():
    """Create new user (admin only)."""
    data = request.get_json()
    
    # Validate required fields
    required = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if username or email exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Create user
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=data['role'],
        license_number=data.get('license_number'),
        license_state=data.get('license_state'),
        employee_id=data.get('employee_id'),
        department=data.get('department')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    AuditLog.log_action(
        user=current_user,
        action='create',
        resource_type='user',
        resource_id=user.id,
        description=f'Created user: {user.username}',
        request=request
    )
    
    return jsonify(user.to_dict()), 201


@bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Users can update their own profile, admins can update any
    if current_user_id != user_id and not current_user.has_permission('all'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    old_values = user.to_dict()
    
    # Update allowed fields
    updatable = ['first_name', 'last_name', 'email', 'phone', 
                 'license_number', 'license_state', 'department']
    
    # Only admins can update role and active status
    if current_user.has_permission('all'):
        updatable.extend(['role', 'is_active'])
    
    for field in updatable:
        if field in data:
            setattr(user, field, data[field])
    
    db.session.commit()
    
    AuditLog.log_action(
        user=current_user,
        action='update',
        resource_type='user',
        resource_id=user.id,
        description=f'Updated user: {user.username}',
        old_values=old_values,
        new_values=user.to_dict(),
        request=request
    )
    
    return jsonify(user.to_dict()), 200


@bp.route('/<int:user_id>', methods=['DELETE'])
@require_permission('all')
def deactivate_user(user_id):
    """Deactivate user (soft delete)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_active = False
    db.session.commit()
    
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    AuditLog.log_action(
        user=current_user,
        action='deactivate',
        resource_type='user',
        resource_id=user.id,
        description=f'Deactivated user: {user.username}',
        request=request
    )
    
    return jsonify({'message': 'User deactivated successfully'}), 200
