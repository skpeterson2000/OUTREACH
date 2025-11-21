"""Permission decorators for route access control."""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User


def require_role(roles):
    """
    Decorator to restrict route access based on user role.
    
    Args:
        roles: List of allowed roles (e.g., ['RN', 'Admin']) or single role string
    
    Usage:
        @bp.route('/endpoint')
        @jwt_required()
        @require_role(['RN', 'Admin'])
        def my_endpoint():
            ...
    """
    if isinstance(roles, str):
        roles = [roles]
    
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.role not in roles:
                return jsonify({
                    'error': 'Access denied',
                    'message': f'This endpoint requires one of the following roles: {", ".join(roles)}',
                    'your_role': user.role
                }), 403
            
            return fn(*args, **kwargs)
        
        return wrapper
    return decorator
