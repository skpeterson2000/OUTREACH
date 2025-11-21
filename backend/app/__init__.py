"""Flask application factory."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
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
