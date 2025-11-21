"""User model for authentication and role-based access control."""
from datetime import datetime
from app import db
import bcrypt


class User(db.Model):
    """User model for healthcare staff."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))  # Contact phone number
    
    # Professional Information
    role = db.Column(db.String(50), nullable=False)  # RN, LPN, CNA, Admin, etc.
    license_number = db.Column(db.String(100))
    license_state = db.Column(db.String(2))
    license_expiration = db.Column(db.Date)
    
    # Employment
    employee_id = db.Column(db.String(50), unique=True)
    department = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    
    # Account Status
    status = db.Column(db.String(20), default='active', nullable=False)  # active, inactive, suspended
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    facility = db.relationship('Facility', back_populates='users')
    visits = db.relationship('Visit', back_populates='nurse', lazy='dynamic')
    assessments = db.relationship('Assessment', back_populates='nurse', lazy='dynamic')
    medication_administrations = db.relationship('MedicationAdministration', 
                                                  foreign_keys='MedicationAdministration.administered_by',
                                                  back_populates='administered_by_user', 
                                                  lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def has_permission(self, permission):
        """Check if user has specific permission based on role."""
        role_permissions = {
            'Admin': ['all'],
            'RN': ['assess', 'medicate', 'document', 'care_plan', 'supervise'],
            'LPN': ['assess', 'medicate', 'document'],
            'CNA': ['vital_signs', 'document', 'basic_care'],
            'Supervisor': ['assess', 'medicate', 'document', 'care_plan', 'supervise', 'review']
        }
        
        permissions = role_permissions.get(self.role, [])
        return 'all' in permissions or permission in permissions
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'role': self.role,
            'license_number': self.license_number,
            'license_state': self.license_state,
            'employee_id': self.employee_id,
            'department': self.department,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
