"""
Organization and facility management routes.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Organization, Facility, Device, User
from app.models.audit_log import AuditLog
from functools import wraps

organizations_bp = Blueprint('organizations', __name__)


def admin_required(fn):
    """Decorator to require admin role."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper


# ===== ORGANIZATION ROUTES =====

@organizations_bp.route('/api/organizations', methods=['GET'])
@jwt_required()
def list_organizations():
    """List all organizations (admin only for full list, users see their org)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Admins see all organizations
    if user.role == 'Admin':
        organizations = Organization.query.filter_by(is_active=True).all()
    else:
        # Regular users only see their facility's organization
        if not user.facility:
            return jsonify({'error': 'User not assigned to facility'}), 400
        organizations = [user.facility.organization]
    
    return jsonify({
        'organizations': [org.to_dict() for org in organizations]
    }), 200


@organizations_bp.route('/api/organizations', methods=['POST'])
@admin_required
def create_organization():
    """Create a new organization (admin only)."""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Organization name is required'}), 400
    
    # Check if organization with same name exists
    existing = Organization.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Organization with this name already exists'}), 409
    
    # Create organization
    organization = Organization(
        name=data['name'],
        npi=data.get('npi'),
        tax_id=data.get('tax_id'),
        license_number=data.get('license_number'),
        address_line1=data.get('address_line1'),
        address_line2=data.get('address_line2'),
        city=data.get('city'),
        state=data.get('state'),
        zip_code=data.get('zip_code'),
        phone=data.get('phone'),
        email=data.get('email'),
        website=data.get('website'),
        settings=data.get('settings', {})
    )
    
    db.session.add(organization)
    db.session.commit()
    
    # Audit log
    user_id = get_jwt_identity()
    AuditLog.log_action(
        user_id=user_id,
        action='CREATE',
        resource_type='Organization',
        resource_id=organization.id,
        details=f"Created organization: {organization.name}"
    )
    
    return jsonify({
        'message': 'Organization created successfully',
        'organization': organization.to_dict()
    }), 201


@organizations_bp.route('/api/organizations/<int:org_id>', methods=['GET'])
@jwt_required()
def get_organization(org_id):
    """Get organization details."""
    organization = Organization.query.get_or_404(org_id)
    
    # Check access permission
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Users can only view their own organization unless they're admin
    if user.role != 'Admin' and user.facility.organization_id != org_id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'organization': organization.to_dict(include_facilities=True)
    }), 200


@organizations_bp.route('/api/organizations/<int:org_id>', methods=['PUT'])
@admin_required
def update_organization(org_id):
    """Update organization details (admin only)."""
    organization = Organization.query.get_or_404(org_id)
    data = request.get_json()
    
    # Update fields
    updatable_fields = [
        'name', 'npi', 'tax_id', 'license_number',
        'address_line1', 'address_line2', 'city', 'state', 'zip_code',
        'phone', 'email', 'website', 'settings', 'is_active'
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(organization, field, data[field])
    
    db.session.commit()
    
    # Audit log
    user_id = get_jwt_identity()
    AuditLog.log_action(
        user_id=user_id,
        action='UPDATE',
        resource_type='Organization',
        resource_id=organization.id,
        details=f"Updated organization: {organization.name}"
    )
    
    return jsonify({
        'message': 'Organization updated successfully',
        'organization': organization.to_dict()
    }), 200


# ===== FACILITY ROUTES =====

@organizations_bp.route('/api/facilities', methods=['GET'])
@jwt_required()
def list_facilities():
    """List facilities (filtered by user's organization)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Admins can see all facilities, users see their organization's facilities
    if user.role == 'Admin':
        facilities = Facility.query.filter_by(is_active=True).all()
    else:
        if not user.facility:
            return jsonify({'error': 'User not assigned to facility'}), 400
        org_id = user.facility.organization_id
        facilities = Facility.query.filter_by(
            organization_id=org_id,
            is_active=True
        ).all()
    
    return jsonify({
        'facilities': [f.to_dict(include_stats=True) for f in facilities]
    }), 200


@organizations_bp.route('/api/facilities', methods=['POST'])
@admin_required
def create_facility():
    """Create a new facility (admin only)."""
    data = request.get_json()
    
    # Validate required fields
    required = ['name', 'organization_id', 'facility_type']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate facility type
    if data['facility_type'] not in Facility.FACILITY_TYPES:
        return jsonify({'error': f'Invalid facility_type. Must be one of: {Facility.FACILITY_TYPES}'}), 400
    
    # Verify organization exists
    organization = Organization.query.get(data['organization_id'])
    if not organization:
        return jsonify({'error': 'Organization not found'}), 404
    
    # Create facility
    facility = Facility(
        organization_id=data['organization_id'],
        name=data['name'],
        facility_type=data['facility_type'],
        facility_code=data.get('facility_code'),
        license_number=data.get('license_number'),
        medicaid_provider_number=data.get('medicaid_provider_number'),
        medicare_provider_number=data.get('medicare_provider_number'),
        address_line1=data.get('address_line1'),
        address_line2=data.get('address_line2'),
        city=data.get('city'),
        state=data.get('state'),
        zip_code=data.get('zip_code'),
        phone=data.get('phone'),
        licensed_beds=data.get('licensed_beds'),
        current_census=data.get('current_census', 0),
        settings=data.get('settings', {}),
        features=data.get('features', {})
    )
    
    db.session.add(facility)
    db.session.commit()
    
    # Audit log
    user_id = get_jwt_identity()
    AuditLog.log_action(
        user_id=user_id,
        action='CREATE',
        resource_type='Facility',
        resource_id=facility.id,
        details=f"Created facility: {facility.name}"
    )
    
    return jsonify({
        'message': 'Facility created successfully',
        'facility': facility.to_dict()
    }), 201


@organizations_bp.route('/api/facilities/<int:facility_id>', methods=['GET'])
@jwt_required()
def get_facility(facility_id):
    """Get facility details."""
    facility = Facility.query.get_or_404(facility_id)
    
    # Check access permission
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Users can only view facilities in their organization unless they're admin
    if user.role != 'Admin':
        if not user.facility or user.facility.organization_id != facility.organization_id:
            return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'facility': facility.to_dict(include_devices=True, include_stats=True)
    }), 200


@organizations_bp.route('/api/facilities/<int:facility_id>', methods=['PUT'])
@admin_required
def update_facility(facility_id):
    """Update facility details (admin only)."""
    facility = Facility.query.get_or_404(facility_id)
    data = request.get_json()
    
    # Update fields
    updatable_fields = [
        'name', 'facility_type', 'facility_code', 'license_number',
        'medicaid_provider_number', 'medicare_provider_number',
        'address_line1', 'address_line2', 'city', 'state', 'zip_code',
        'phone', 'licensed_beds', 'current_census', 'settings', 'features', 'is_active'
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(facility, field, data[field])
    
    db.session.commit()
    
    # Audit log
    user_id = get_jwt_identity()
    AuditLog.log_action(
        user_id=user_id,
        action='UPDATE',
        resource_type='Facility',
        resource_id=facility.id,
        details=f"Updated facility: {facility.name}"
    )
    
    return jsonify({
        'message': 'Facility updated successfully',
        'facility': facility.to_dict(include_stats=True)
    }), 200


@organizations_bp.route('/api/facilities/<int:facility_id>/census', methods=['PUT'])
@jwt_required()
def update_census(facility_id):
    """Update facility census count."""
    facility = Facility.query.get_or_404(facility_id)
    data = request.get_json()
    
    # Check permission - users can update their own facility's census
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['Admin', 'RN', 'LPN'] or user.facility_id != facility_id:
        return jsonify({'error': 'Access denied'}), 403
    
    if 'current_census' not in data:
        return jsonify({'error': 'current_census is required'}), 400
    
    new_census = data['current_census']
    
    # Validate census doesn't exceed licensed beds
    if facility.licensed_beds and new_census > facility.licensed_beds:
        return jsonify({'error': 'Census cannot exceed licensed beds'}), 400
    
    old_census = facility.current_census
    facility.current_census = new_census
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        user_id=user_id,
        action='UPDATE',
        resource_type='Facility',
        resource_id=facility.id,
        details=f"Updated census from {old_census} to {new_census}"
    )
    
    return jsonify({
        'message': 'Census updated successfully',
        'facility': facility.to_dict(include_stats=True)
    }), 200


# ===== DEVICE ROUTES =====

@organizations_bp.route('/api/facilities/<int:facility_id>/devices', methods=['GET'])
@jwt_required()
def list_devices(facility_id):
    """List devices for a facility."""
    facility = Facility.query.get_or_404(facility_id)
    
    # Check permission
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'Admin' and user.facility_id != facility_id:
        return jsonify({'error': 'Access denied'}), 403
    
    devices = Device.query.filter_by(facility_id=facility_id).all()
    
    return jsonify({
        'devices': [d.to_dict(include_hardware=True) for d in devices]
    }), 200


@organizations_bp.route('/api/devices', methods=['POST'])
@admin_required
def register_device():
    """Register a new device (admin only)."""
    data = request.get_json()
    
    # Validate required fields
    required = ['facility_id', 'device_name', 'device_type', 'device_uuid']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate device type
    if data['device_type'] not in Device.DEVICE_TYPES:
        return jsonify({'error': f'Invalid device_type. Must be one of: {Device.DEVICE_TYPES}'}), 400
    
    # Verify facility exists
    facility = Facility.query.get(data['facility_id'])
    if not facility:
        return jsonify({'error': 'Facility not found'}), 404
    
    # Check if device UUID already exists
    existing = Device.query.filter_by(device_uuid=data['device_uuid']).first()
    if existing:
        return jsonify({'error': 'Device with this UUID already registered'}), 409
    
    # Create device
    device = Device(
        facility_id=data['facility_id'],
        device_name=data['device_name'],
        device_type=data['device_type'],
        device_uuid=data['device_uuid'],
        mac_address=data.get('mac_address'),
        location=data.get('location'),
        hardware_info=data.get('hardware_info', {}),
        encryption_enabled=data.get('encryption_enabled', True),
        offline_capable=data.get('offline_capable', True),
        settings=data.get('settings', {})
    )
    
    db.session.add(device)
    db.session.commit()
    
    # Audit log
    user_id = get_jwt_identity()
    AuditLog.log_action(
        user_id=user_id,
        action='CREATE',
        resource_type='Device',
        resource_id=device.id,
        details=f"Registered device: {device.device_name} at {facility.name}"
    )
    
    return jsonify({
        'message': 'Device registered successfully',
        'device': device.to_dict(include_hardware=True)
    }), 201


@organizations_bp.route('/api/devices/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id):
    """Get device details."""
    device = Device.query.get_or_404(device_id)
    
    # Check permission
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'Admin' and user.facility_id != device.facility_id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'device': device.to_dict(include_hardware=True)
    }), 200


@organizations_bp.route('/api/devices/<int:device_id>', methods=['PUT'])
@admin_required
def update_device(device_id):
    """Update device details (admin only)."""
    device = Device.query.get_or_404(device_id)
    data = request.get_json()
    
    # Update fields
    updatable_fields = [
        'device_name', 'device_type', 'location', 'hardware_info',
        'encryption_enabled', 'offline_capable', 'settings', 'is_active'
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(device, field, data[field])
    
    db.session.commit()
    
    # Audit log
    user_id = get_jwt_identity()
    AuditLog.log_action(
        user_id=user_id,
        action='UPDATE',
        resource_type='Device',
        resource_id=device.id,
        details=f"Updated device: {device.device_name}"
    )
    
    return jsonify({
        'message': 'Device updated successfully',
        'device': device.to_dict(include_hardware=True)
    }), 200


@organizations_bp.route('/api/devices/<int:device_id>/heartbeat', methods=['POST'])
@jwt_required()
def device_heartbeat(device_id):
    """Update device last_seen timestamp (device check-in)."""
    device = Device.query.get_or_404(device_id)
    
    from datetime import datetime
    device.last_seen = datetime.utcnow()
    
    # Optionally update sync timestamp if provided
    data = request.get_json() or {}
    if data.get('synced'):
        device.last_sync = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Heartbeat recorded',
        'device': {
            'id': device.id,
            'is_online': device.is_online,
            'sync_status': device.sync_status,
            'last_seen': device.last_seen.isoformat(),
            'last_sync': device.last_sync.isoformat() if device.last_sync else None
        }
    }), 200


@organizations_bp.route('/api/devices/<int:device_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_device(device_id):
    """Deactivate a device (admin only)."""
    device = Device.query.get_or_404(device_id)
    
    device.is_active = False
    db.session.commit()
    
    # Audit log
    user_id = get_jwt_identity()
    AuditLog.log_action(
        user_id=user_id,
        action='DEACTIVATE',
        resource_type='Device',
        resource_id=device.id,
        details=f"Deactivated device: {device.device_name}"
    )
    
    return jsonify({
        'message': 'Device deactivated successfully',
        'device': device.to_dict()
    }), 200
