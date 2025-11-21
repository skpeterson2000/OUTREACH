"""Audit log model for HIPAA compliance."""
from datetime import datetime
from app import db


class AuditLog(db.Model):
    """Comprehensive audit trail for all data access and modifications."""
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Who
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    username = db.Column(db.String(80))
    user_role = db.Column(db.String(50))
    
    # What
    action = db.Column(db.String(50), nullable=False, index=True)
    # Actions: login, logout, view, create, update, delete, export, print
    
    resource_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: patient, medication, assessment, wound, user, etc.
    
    resource_id = db.Column(db.Integer, index=True)
    
    # Context
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), index=True)
    description = db.Column(db.Text)
    
    # Changes (for updates)
    old_values = db.Column(db.JSON)  # before update
    new_values = db.Column(db.JSON)  # after update
    
    # Request Details
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(500))
    endpoint = db.Column(db.String(200))
    http_method = db.Column(db.String(10))
    
    # Status
    status = db.Column(db.String(20))  # success, failure, unauthorized
    error_message = db.Column(db.Text)
    
    # Compliance
    phi_accessed = db.Column(db.Boolean, default=False)  # Protected Health Information
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'patient_id': self.patient_id,
            'description': self.description,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }
    
    @staticmethod
    def log_action(user, action, resource_type, resource_id=None, 
                   patient_id=None, description=None, old_values=None, 
                   new_values=None, request=None, phi_accessed=False):
        """
        Create an audit log entry.
        
        Args:
            user: User object who performed the action
            action: Type of action (view, create, update, delete, etc.)
            resource_type: Type of resource (patient, medication, etc.)
            resource_id: ID of the resource
            patient_id: Patient ID if applicable
            description: Human-readable description
            old_values: Dict of old values (for updates)
            new_values: Dict of new values (for updates)
            request: Flask request object
            phi_accessed: Whether PHI was accessed
        """
        log = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else 'system',
            user_role=user.role if user else 'system',
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            phi_accessed=phi_accessed,
            status='success'
        )
        
        if request:
            log.ip_address = request.remote_addr
            log.user_agent = request.headers.get('User-Agent', '')
            log.endpoint = request.endpoint
            log.http_method = request.method
        
        db.session.add(log)
        db.session.commit()
        
        return log
    
    @staticmethod
    def log_access(user_id, action, resource_type, resource_id=None, 
                   details=None, contains_phi=False, facility_id=None):
        """
        Simplified audit logging for access events.
        Compatibility wrapper for older code.
        """
        from app.models.user import User
        user = User.query.get(user_id) if user_id else None
        
        return AuditLog.log_action(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=details,
            phi_accessed=contains_phi
        )
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.username} {self.action} {self.resource_type}>'
