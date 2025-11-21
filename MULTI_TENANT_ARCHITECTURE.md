# Multi-Tenant Architecture Implementation

## Overview

The system now supports a hierarchical multi-tenant architecture that enables organizations to operate multiple facilities across different care settings:

```
Organization (Top Level)
└── Facilities (Multiple)
    ├── Devices (Multiple per facility)
    ├── Users (Staff assigned to facility)
    └── Patients (Residents/clients at facility)
```

## Architecture Components

### 1. Organization Model

**Purpose**: Top-level entity representing a healthcare organization

**Supported Organization Types**:
- Home Health Agencies
- Assisted Living Facility operators
- Memory Care facility groups
- Skilled Nursing Facility chains
- Multi-site healthcare systems

**Key Features**:
- NPI (National Provider Identifier)
- Tax ID (EIN) for billing
- State licensing information
- Organization-wide settings and configuration
- Multi-facility management

### 2. Facility Model

**Purpose**: Individual care facility within an organization

**Facility Types**:
- `HOME_HEALTH` - Visiting nurse services, scattered patient locations
- `ALF` - Assisted Living Facility, centralized resident care
- `MEMORY_CARE` - Specialized dementia/Alzheimer's care with behavior tracking
- `SNF` - Skilled Nursing Facility, intensive nursing care
- `HOSPICE` - End-of-life care specialization

**Key Features**:
- Facility-specific licensing (Medicaid/Medicare provider numbers)
- Capacity management (licensed beds, current census, occupancy rate)
- Location-specific settings and enabled features
- Device registration per facility

**Capacity Tracking**:
```python
facility.licensed_beds = 32
facility.current_census = 28
facility.occupancy_rate  # Automatically calculates: 87.5%
facility.available_beds  # Automatically calculates: 4
```

### 3. Device Model

**Purpose**: Agency-owned device authentication and management

**Device Types**:
- `RASPBERRY_PI` - Wall-mounted kiosks, common areas
- `TABLET` - iPad/Android tablets for mobile nursing
- `LAPTOP` - Full workstation capability
- `WORKSTATION` - Desktop computers in med room/nurse station
- `BADGE_READER` - NFC/RFID authentication device

**Security Features**:
- Hardware UUID tracking (prevents device cloning)
- MAC address registration
- Encryption enforcement
- Security audit timestamps
- Session management per device

**Status Tracking**:
```python
device.is_online       # True if heartbeat within last 5 minutes
device.sync_status     # 'SYNCED', 'STALE', 'OUT_OF_SYNC', 'NEVER_SYNCED'
device.last_seen       # Last heartbeat timestamp
device.last_sync       # Last successful data sync
```

## Data Relationships

### Multi-Tenancy Structure

All users and patients are now assigned to a specific facility:

```python
# User assignment
user.facility_id = 1  # RN assigned to Facility #1
user.facility.name    # "Sunrise ALF - North Campus"
user.facility.organization.name  # "Sunrise Senior Living Inc"

# Patient assignment
patient.facility_id = 1  # Resident at Facility #1
patient.facility.facility_type  # "ALF"
```

### Data Isolation

- Users can only access patients within their facility
- Admins can access all facilities within their organization
- Organization-level admins can access all data across all facilities
- Audit logs track all cross-facility access

## API Endpoints

### Organization Management

```
GET    /api/organizations              # List organizations
POST   /api/organizations              # Create organization (admin)
GET    /api/organizations/<id>         # Get organization details
PUT    /api/organizations/<id>         # Update organization (admin)
```

### Facility Management

```
GET    /api/facilities                 # List facilities
POST   /api/facilities                 # Create facility (admin)
GET    /api/facilities/<id>            # Get facility details
PUT    /api/facilities/<id>            # Update facility (admin)
PUT    /api/facilities/<id>/census     # Update census count
```

### Device Management

```
GET    /api/facilities/<id>/devices    # List facility devices
POST   /api/devices                    # Register device (admin)
GET    /api/devices/<id>               # Get device details
PUT    /api/devices/<id>               # Update device (admin)
POST   /api/devices/<id>/heartbeat     # Device check-in
POST   /api/devices/<id>/deactivate    # Deactivate device (admin)
```

## Use Cases

### Home Health Agency

```python
org = Organization(name="ComfortCare Home Health")
facility = Facility(
    organization=org,
    name="ComfortCare - North Region",
    facility_type="HOME_HEALTH",
    current_census=45  # Active patients
)
```

- Devices: Tablets for nurses, laptops for case managers
- No bed capacity (patients in their homes)
- Scattered geographic service area

### Assisted Living Facility

```python
org = Organization(name="Golden Years Senior Living")
facility = Facility(
    organization=org,
    name="Golden Years ALF - Riverside",
    facility_type="ALF",
    licensed_beds=48,
    current_census=44
)
```

- Devices: Med room workstation, hall kiosks (Pi), nurse tablets
- Centralized resident care
- Capacity management critical for admissions

### Memory Care Unit

```python
org = Organization(name="Memory Lane Care Partners")
facility = Facility(
    organization=org,
    name="Memory Lane - Secure Unit",
    facility_type="MEMORY_CARE",
    licensed_beds=16,
    current_census=15,
    features={
        "behavior_tracking": True,
        "wandering_alerts": True,
        "family_portal": True
    }
)
```

- Devices: Badge readers at exits, behavior tracking tablets
- Specialized behavior/psychiatric assessments enabled
- PRN medication effectiveness tracking
- Family participation features

## Migration Path

### For Existing Installations

1. **Create Organization**:
   ```bash
   POST /api/organizations
   {
     "name": "Your Healthcare Organization",
     "npi": "1234567890"
   }
   ```

2. **Create Facility**:
   ```bash
   POST /api/facilities
   {
     "organization_id": 1,
     "name": "Main Campus",
     "facility_type": "HOME_HEALTH"
   }
   ```

3. **Assign Users**:
   ```sql
   UPDATE users SET facility_id = 1 WHERE organization = 'legacy';
   ```

4. **Assign Patients**:
   ```sql
   UPDATE patients SET facility_id = 1 WHERE location = 'main';
   ```

5. **Register Devices**:
   ```bash
   POST /api/devices
   {
     "facility_id": 1,
     "device_name": "Nurse Station A",
     "device_type": "WORKSTATION",
     "device_uuid": "550e8400-e29b-41d4-a716-446655440000"
   }
   ```

### Database Migration

Run Flask-Migrate to create new tables:

```bash
cd backend
flask db migrate -m "Add multi-tenant organization/facility/device models"
flask db upgrade
```

**Note**: Existing `users` and `patients` tables will gain a `facility_id` column. You must populate this column before the NOT NULL constraint is applied.

## Security Considerations

### Device Registration

- Only admins can register new devices
- Device UUID must be unique (hardware-based)
- MAC address tracked for network security
- Encryption enforcement per device

### Badge Authentication

- Badge readers are specialized devices (`TYPE_BADGE_READER`)
- NFC/RFID hardware integration at device level
- User badges linked to `user.employee_id`
- Badge swipe triggers device authentication

### Data Isolation

- Users can only query patients within their facility
- API automatically filters by `facility_id`
- Cross-facility access generates audit log entries
- Organization admins have full visibility

## Performance Optimization

### Indexing

All foreign keys are indexed:
- `users.facility_id`
- `patients.facility_id`
- `facilities.organization_id`
- `devices.facility_id`

### Query Patterns

Always filter by facility for performance:

```python
# Good - uses index
patients = Patient.query.filter_by(
    facility_id=current_user.facility_id,
    status='active'
).all()

# Bad - full table scan
patients = Patient.query.filter_by(status='active').all()
```

## Monitoring & Analytics

### Facility Dashboard Metrics

```python
facility = Facility.query.get(1)

# Capacity metrics
occupancy_rate = facility.occupancy_rate      # 87.5%
available_beds = facility.available_beds       # 4
census = facility.current_census               # 28

# Device health
devices = facility.devices.filter_by(is_active=True).all()
online_count = sum(1 for d in devices if d.is_online)
sync_issues = [d for d in devices if d.sync_status != 'SYNCED']

# Staffing
staff_count = facility.users.filter_by(is_active=True).count()
rn_count = facility.users.filter_by(role='RN', is_active=True).count()
```

## Next Steps

1. **Family Participation System**: CareParticipant model unifying staff + family + volunteers
2. **Offline Sync**: Device-level SQLite mirrors with intelligent sync queues
3. **Facility-Specific Features**: Behavior tracking for Memory Care, med room workflows for ALF
4. **Badge Reader Integration**: NFC/RFID hardware abstraction layer
5. **Family Portal**: Kiosk mode for family caregivers with simplified UI

## Market Opportunity

This architecture enables the system to serve:

- **11,400** Home Health Agencies
- **28,900** Assisted Living Facilities
- **15,000** Memory Care Units
- **15,600** Skilled Nursing Facilities

**Total Addressable Market**: 70,900+ care facilities in the United States
