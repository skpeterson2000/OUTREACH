"""Authentication routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime
from app import db
from app.models.user import User
from app.models.audit_log import AuditLog

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    password = data['password']
    
    # Find user
    user = User.query.filter_by(username=username).first()
    
    if not user:
        AuditLog.log_action(
            user=None,
            action='login_failed',
            resource_type='auth',
            description=f'Failed login attempt for username: {username}',
            request=request
        )
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check if account is locked
    if user.account_locked_until and user.account_locked_until > datetime.utcnow():
        return jsonify({'error': 'Account temporarily locked. Please try again later.'}), 403
    
    # Check if account is active
    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403
    
    # Verify password
    if not user.check_password(password):
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            from datetime import timedelta
            user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        db.session.commit()
        
        AuditLog.log_action(
            user=user,
            action='login_failed',
            resource_type='auth',
            description='Invalid password',
            request=request
        )
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.account_locked_until = None
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    # Log successful login
    AuditLog.log_action(
        user=user,
        action='login',
        resource_type='auth',
        description='Successful login',
        request=request
    )
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    
    return jsonify({'access_token': access_token}), 200


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should discard tokens)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user:
        AuditLog.log_action(
            user=user,
            action='logout',
            resource_type='auth',
            description='User logged out',
            request=request
        )
    
    return jsonify({'message': 'Successfully logged out'}), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user info."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Old and new passwords required'}), 400
    
    # Verify old password
    if not user.check_password(old_password):
        return jsonify({'error': 'Invalid old password'}), 401
    
    # Validate new password
    from flask import current_app
    if len(new_password) < current_app.config['PASSWORD_MIN_LENGTH']:
        return jsonify({
            'error': f'Password must be at least {current_app.config["PASSWORD_MIN_LENGTH"]} characters'
        }), 400
    
    # Set new password
    user.set_password(new_password)
    db.session.commit()
    
    AuditLog.log_action(
        user=user,
        action='change_password',
        resource_type='user',
        description='Password changed',
        request=request
    )
    
    return jsonify({'message': 'Password changed successfully'}), 200
