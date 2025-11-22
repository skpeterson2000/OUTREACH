"""Comprehensive logging utility for debugging user actions and system behavior."""
import logging
import os
from datetime import datetime
from functools import wraps
from flask import request, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import json

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure main application logger
app_logger = logging.getLogger('outreach_ehr')
app_logger.setLevel(logging.DEBUG)

# File handler for all logs
file_handler = logging.FileHandler('logs/app_debug.log')
file_handler.setLevel(logging.DEBUG)

# Console handler for important logs
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

app_logger.addHandler(file_handler)
app_logger.addHandler(console_handler)

# User action logger (separate file for user actions)
user_action_logger = logging.getLogger('outreach_ehr.user_actions')
user_action_logger.setLevel(logging.INFO)
user_action_handler = logging.FileHandler('logs/user_actions.log')
user_action_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
user_action_logger.addHandler(user_action_handler)


def get_current_user_info():
    """Get current user information from JWT token."""
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            from app.models import User
            user = User.query.get(user_id)
            if user:
                return {
                    'user_id': user.id,
                    'username': user.username,
                    'name': user.full_name,
                    'role': user.role
                }
    except:
        pass
    return {'user_id': None, 'username': 'anonymous', 'name': 'Anonymous', 'role': 'none'}


def log_user_action(action, details=None, level='INFO'):
    """Log a user action with context."""
    user_info = get_current_user_info()
    
    log_entry = {
        'action': action,
        'user': user_info['username'],
        'role': user_info['role'],
        'name': user_info['name'],
        'ip': request.remote_addr if request else 'N/A',
        'endpoint': request.endpoint if request else 'N/A',
        'method': request.method if request else 'N/A',
        'path': request.path if request else 'N/A',
    }
    
    if details:
        log_entry['details'] = details
    
    log_message = json.dumps(log_entry)
    
    if level == 'DEBUG':
        user_action_logger.debug(log_message)
    elif level == 'WARNING':
        user_action_logger.warning(log_message)
    elif level == 'ERROR':
        user_action_logger.error(log_message)
    else:
        user_action_logger.info(log_message)


def log_api_request(f):
    """Decorator to log API requests with user context."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_info = get_current_user_info()
        
        # Log request
        request_data = {}
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                request_data = request.get_json() or {}
                # Sanitize sensitive data
                if 'password' in request_data:
                    request_data['password'] = '***REDACTED***'
            except:
                pass
        
        app_logger.info(
            f"API REQUEST: {request.method} {request.path} | "
            f"User: {user_info['username']} ({user_info['role']}) | "
            f"Data: {json.dumps(request_data) if request_data else 'None'}"
        )
        
        # Execute function
        try:
            result = f(*args, **kwargs)
            
            # Log success
            app_logger.info(
                f"API SUCCESS: {request.method} {request.path} | "
                f"User: {user_info['username']}"
            )
            
            return result
            
        except Exception as e:
            # Log error
            app_logger.error(
                f"API ERROR: {request.method} {request.path} | "
                f"User: {user_info['username']} | "
                f"Error: {str(e)}",
                exc_info=True
            )
            raise
    
    return decorated_function


def log_database_operation(operation, table, record_id=None, details=None):
    """Log database operations."""
    user_info = get_current_user_info()
    
    app_logger.debug(
        f"DB {operation}: {table} | "
        f"ID: {record_id or 'N/A'} | "
        f"User: {user_info['username']} | "
        f"Details: {details or 'None'}"
    )


def log_medication_administration(patient_id, medication_id, action, details=None):
    """Log medication administration actions with full context."""
    user_info = get_current_user_info()
    
    log_user_action(
        action=f"MEDICATION_{action.upper()}",
        details={
            'patient_id': patient_id,
            'medication_id': medication_id,
            'action': action,
            'additional_details': details
        }
    )
    
    app_logger.info(
        f"MEDICATION {action.upper()}: Patient #{patient_id} | "
        f"Medication #{medication_id} | "
        f"User: {user_info['name']} ({user_info['role']}) | "
        f"Details: {json.dumps(details) if details else 'None'}"
    )


def log_adr_alert_action(alert_id, action, details=None):
    """Log ADR alert actions."""
    user_info = get_current_user_info()
    
    log_user_action(
        action=f"ADR_ALERT_{action.upper()}",
        details={
            'alert_id': alert_id,
            'action': action,
            'additional_details': details
        }
    )
    
    app_logger.info(
        f"ADR ALERT {action.upper()}: Alert #{alert_id} | "
        f"User: {user_info['name']} ({user_info['role']}) | "
        f"Details: {json.dumps(details) if details else 'None'}"
    )
