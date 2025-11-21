"""
Organization and Facility models for multi-tenant architecture.

Supports multiple organization types:
- Home Health Agencies
- Assisted Living Facilities (ALF)
- Memory Care Units
- Skilled Nursing Facilities (SNF)
"""
from datetime import datetime
from app import db

class Organization(db.Model):
    """
    Top-level entity representing a healthcare organization.
    
    An organization can operate multiple facilities across different care settings.
    Examples:
    - "Comfort Care Inc" operating 3 home health branches + 2 ALFs
    - "Memory Care Partners" with 5 memory care facilities
    - "Senior Living Group" with mixed ALF/Memory Care/SNF campuses
    """
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    organization_type = db.Column(db.String(50))  # home_health, alf, memory_care, snf, hospice
    
    # Organization identification
    npi = db.Column(db.String(10), unique=True, index=True)  # National Provider Identifier
    tax_id = db.Column(db.String(20), unique=True)  # EIN for billing
    license_number = db.Column(db.String(100))
    
    # Contact information
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    
    # Settings and configuration
    settings = db.Column(db.JSON, default={})  # Org-wide settings, branding, etc.
    status = db.Column(db.String(20), default='active', nullable=False)  # active, inactive, suspended
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    facilities = db.relationship('Facility', back_populates='organization', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Organization {self.name}>'
    
    def to_dict(self, include_facilities=False):
        """Serialize organization to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'npi': self.npi,
            'tax_id': self.tax_id,
            'license_number': self.license_number,
            'address': {
                'line1': self.address_line1,
                'line2': self.address_line2,
                'city': self.city,
                'state': self.state,
                'zip_code': self.zip_code
            },
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_facilities:
            data['facilities'] = [f.to_dict() for f in self.facilities.all()]
        
        return data


class Facility(db.Model):
    """
    Individual care facility within an organization.
    
    Facility types determine available features and workflows:
    - HOME_HEALTH: Visiting nurse services, scattered patient locations
    - ALF: Assisted Living Facility, centralized resident care
    - MEMORY_CARE: Specialized dementia/Alzheimer's care, behavior tracking
    - SNF: Skilled Nursing Facility, intensive nursing care
    - TCU: Transitional Care Unit, post-acute rehabilitation (often SNF wing)
    - HOSPICE: End-of-life care specialization
    """
    __tablename__ = 'facilities'
    
    # Facility type constants
    TYPE_HOME_HEALTH = 'HOME_HEALTH'
    TYPE_ALF = 'ALF'
    TYPE_MEMORY_CARE = 'MEMORY_CARE'
    TYPE_SNF = 'SNF'
    TYPE_TCU = 'TCU'
    TYPE_HOSPICE = 'HOSPICE'
    
    FACILITY_TYPES = [
        TYPE_HOME_HEALTH,
        TYPE_ALF,
        TYPE_MEMORY_CARE,
        TYPE_SNF,
        TYPE_TCU,
        TYPE_HOSPICE
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Basic information
    name = db.Column(db.String(200), nullable=False, index=True)
    facility_type = db.Column(db.String(50), nullable=False, index=True)
    
    # Facility identification
    facility_code = db.Column(db.String(50), unique=True, index=True)  # Internal code
    license_number = db.Column(db.String(100))  # State license
    medicaid_provider_number = db.Column(db.String(50))
    medicare_provider_number = db.Column(db.String(50))
    
    # Location
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    
    # Capacity (for residential facilities)
    licensed_beds = db.Column(db.Integer)  # Total licensed capacity
    current_census = db.Column(db.Integer, default=0)  # Current occupied beds/active patients
    
    # Configuration
    settings = db.Column(db.JSON, default={})  # Facility-specific settings
    features = db.Column(db.JSON, default={})  # Enabled modules and features
    status = db.Column(db.String(20), default='active', nullable=False)  # active, inactive, suspended
    capacity = db.Column(db.Integer)  # Shorthand for licensed_beds (backward compatibility)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = db.relationship('Organization', back_populates='facilities')
    devices = db.relationship('Device', back_populates='facility', lazy='dynamic',
                             cascade='all, delete-orphan')
    users = db.relationship('User', back_populates='facility', lazy='dynamic')
    patients = db.relationship('Patient', back_populates='facility', lazy='dynamic')
    
    def __repr__(self):
        return f'<Facility {self.name} ({self.facility_type})>'
    
    @property
    def occupancy_rate(self):
        """Calculate current occupancy percentage."""
        if not self.licensed_beds or self.licensed_beds == 0:
            return None
        return round((self.current_census / self.licensed_beds) * 100, 1)
    
    @property
    def available_beds(self):
        """Calculate available bed capacity."""
        if not self.licensed_beds:
            return None
        return self.licensed_beds - (self.current_census or 0)
    
    def to_dict(self, include_devices=False, include_stats=False):
        """Serialize facility to dictionary."""
        data = {
            'id': self.id,
            'organization_id': self.organization_id,
            'name': self.name,
            'facility_type': self.facility_type,
            'facility_code': self.facility_code,
            'license_number': self.license_number,
            'medicaid_provider_number': self.medicaid_provider_number,
            'medicare_provider_number': self.medicare_provider_number,
            'address': {
                'line1': self.address_line1,
                'line2': self.address_line2,
                'city': self.city,
                'state': self.state,
                'zip_code': self.zip_code
            },
            'phone': self.phone,
            'licensed_beds': self.licensed_beds,
            'current_census': self.current_census,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_stats and self.licensed_beds:
            data['stats'] = {
                'occupancy_rate': self.occupancy_rate,
                'available_beds': self.available_beds
            }
        
        if include_devices:
            data['devices'] = [d.to_dict() for d in self.devices.all()]
        
        return data


class Device(db.Model):
    """
    Agency-owned device for accessing the EHR system.
    
    Device types:
    - RASPBERRY_PI: Wall-mounted kiosks, common areas
    - TABLET: iPad/Android tablets for mobile nursing
    - LAPTOP: Full workstation capability
    - WORKSTATION: Desktop computers in med room/nurse station
    - BADGE_READER: NFC/RFID authentication device
    """
    __tablename__ = 'devices'
    
    # Device type constants
    TYPE_RASPBERRY_PI = 'RASPBERRY_PI'
    TYPE_TABLET = 'TABLET'
    TYPE_LAPTOP = 'LAPTOP'
    TYPE_WORKSTATION = 'WORKSTATION'
    TYPE_BADGE_READER = 'BADGE_READER'
    
    DEVICE_TYPES = [
        TYPE_RASPBERRY_PI,
        TYPE_TABLET,
        TYPE_LAPTOP,
        TYPE_WORKSTATION,
        TYPE_BADGE_READER
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False, index=True)
    
    # Device identification
    device_name = db.Column(db.String(100), nullable=False)  # Human-readable name
    device_type = db.Column(db.String(50), nullable=False)
    device_uuid = db.Column(db.String(100), unique=True, index=True)  # Hardware UUID (optional for testing)
    serial_number = db.Column(db.String(100), unique=True)  # Physical serial number
    mac_address = db.Column(db.String(17), unique=True, index=True)  # Network MAC
    
    # Location within facility
    location = db.Column(db.String(100))  # "Med Room", "3rd Floor Hall", "Nurse Station B"
    
    # Hardware details
    hardware_info = db.Column(db.JSON, default={})  # CPU, RAM, storage, OS version
    
    # Security
    encryption_enabled = db.Column(db.Boolean, default=True, nullable=False)
    last_security_audit = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(20), default='active', nullable=False)  # active, inactive, maintenance
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_seen = db.Column(db.DateTime)  # Last heartbeat/check-in
    last_sync = db.Column(db.DateTime)  # Last successful data sync
    
    # Configuration
    settings = db.Column(db.JSON, default={})  # Device-specific settings
    offline_capable = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    facility = db.relationship('Facility', back_populates='devices')
    
    def __repr__(self):
        return f'<Device {self.device_name} ({self.device_type})>'
    
    @property
    def is_online(self):
        """Check if device has checked in recently (within last 5 minutes)."""
        if not self.last_seen:
            return False
        time_diff = datetime.utcnow() - self.last_seen
        return time_diff.total_seconds() < 300  # 5 minutes
    
    @property
    def sync_status(self):
        """Get sync freshness status."""
        if not self.last_sync:
            return 'NEVER_SYNCED'
        
        time_diff = datetime.utcnow() - self.last_sync
        minutes_ago = time_diff.total_seconds() / 60
        
        if minutes_ago < 15:
            return 'SYNCED'
        elif minutes_ago < 60:
            return 'STALE'
        else:
            return 'OUT_OF_SYNC'
    
    def to_dict(self, include_hardware=False):
        """Serialize device to dictionary."""
        data = {
            'id': self.id,
            'facility_id': self.facility_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'device_uuid': self.device_uuid,
            'mac_address': self.mac_address,
            'location': self.location,
            'encryption_enabled': self.encryption_enabled,
            'is_active': self.is_active,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_status': self.sync_status,
            'offline_capable': self.offline_capable,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None
        }
        
        if include_hardware:
            data['hardware_info'] = self.hardware_info
            data['last_security_audit'] = self.last_security_audit.isoformat() if self.last_security_audit else None
        
        return data
