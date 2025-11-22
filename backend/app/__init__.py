"""Flask application factory."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()


def setup_logging(app):
    """Setup comprehensive logging that persists across sessions."""
    # Create logs directory in project root (not backend subdirectory)
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure Flask's logger
    app.logger.setLevel(logging.DEBUG)
    
    # Remove default handlers
    app.logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    app.logger.addHandler(console_handler)
    
    # File handler - main application log (10MB max, keep 5 backups)
    app_log_file = os.path.join(log_dir, 'application.log')
    file_handler = RotatingFileHandler(
        app_log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    app.logger.addHandler(file_handler)
    
    # User actions log (separate file for user activity tracking)
    user_log_file = os.path.join(log_dir, 'user_actions.log')
    user_handler = RotatingFileHandler(
        user_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    user_handler.setLevel(logging.INFO)
    user_handler.setFormatter(file_formatter)
    
    # Create separate logger for user actions
    user_logger = logging.getLogger('user_actions')
    user_logger.setLevel(logging.INFO)
    user_logger.addHandler(user_handler)
    
    # API requests log
    api_log_file = os.path.join(log_dir, 'api_requests.log')
    api_handler = RotatingFileHandler(
        api_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(file_formatter)
    
    api_logger = logging.getLogger('api_requests')
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(api_handler)
    
    app.logger.info(f"=" * 80)
    app.logger.info(f"APPLICATION STARTED AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    app.logger.info(f"Log files location: {log_dir}")
    app.logger.info(f"  - Application log: {app_log_file}")
    app.logger.info(f"  - User actions log: {user_log_file}")
    app.logger.info(f"  - API requests log: {api_log_file}")
    app.logger.info(f"=" * 80)


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Setup logging FIRST
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Add request/response logging middleware
    @app.before_request
    def log_request():
        from flask import request
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        
        # Get user info if authenticated
        user_info = "Anonymous"
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                from app.models import User
                user = User.query.get(user_id)
                if user:
                    user_info = f"{user.username} ({user.role})"
        except:
            pass
        
        api_logger = logging.getLogger('api_requests')
        api_logger.info(f">>> {request.method} {request.path} | User: {user_info} | IP: {request.remote_addr}")
        
        # Log request body for POST/PUT/PATCH (sanitize passwords)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            try:
                data = request.get_json()
                if 'password' in data:
                    data = {**data, 'password': '***REDACTED***'}
                api_logger.debug(f"    Request data: {data}")
            except:
                pass
    
    @app.after_request
    def log_response(response):
        from flask import request
        api_logger = logging.getLogger('api_requests')
        api_logger.info(f"<<< {request.method} {request.path} -> {response.status_code}")
        return response
    
    # Register blueprints
    from app.routes import auth, patients, medications, assessments, visits, users, caregiver_support, organizations, adr_alerts, reconciliation, pharmacist
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(patients.bp)
    app.register_blueprint(medications.bp)
    app.register_blueprint(assessments.bp)
    app.register_blueprint(visits.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(caregiver_support.bp)
    app.register_blueprint(organizations.organizations_bp)
    app.register_blueprint(adr_alerts.bp)
    app.register_blueprint(reconciliation.bp)
    app.register_blueprint(pharmacist.bp)
    
    app.logger.info("All routes registered successfully")
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'homecare-ehr-api'}
    
    @app.route('/')
    def index():
        return {
            'service': 'Home Care EHR API',
            'version': '1.0.0',
            'status': 'running'
        }
    
    return app
