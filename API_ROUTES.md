# API Routes Reference

Complete API endpoint documentation for the Home Care EHR system.

**Base URL**: `http://localhost:5000` (development)

**Authentication**: All routes (except `/api/auth/*`) require JWT token in header:
```
Authorization: Bearer <token>
```

---

## Authentication & Users

### Authentication
```
POST   /api/auth/login           # Login with username/password
POST   /api/auth/refresh         # Refresh access token
POST   /api/auth/logout          # Logout and invalidate token
POST   /api/auth/change-password # Change user password
```

### User Management
```
GET    /api/users                # List users (filtered by facility for non-admins)
POST   /api/users                # Create new user (admin only)
GET    /api/users/<id>           # Get user details
PUT    /api/users/<id>           # Update user
DELETE /api/users/<id>           # Deactivate user (admin only)
GET    /api/users/me             # Get current user profile
PUT    /api/users/me             # Update current user profile
```

---

## Organizations & Facilities

### Organizations
```
GET    /api/organizations              # List organizations (admin sees all, users see their org)
POST   /api/organizations              # Create organization (admin only)
GET    /api/organizations/<id>         # Get organization details (includes facilities)
PUT    /api/organizations/<id>         # Update organization (admin only)
```

### Facilities
```
GET    /api/facilities                 # List facilities in user's organization
POST   /api/facilities                 # Create facility (admin only)
GET    /api/facilities/<id>            # Get facility details (includes devices, stats)
PUT    /api/facilities/<id>            # Update facility (admin only)
PUT    /api/facilities/<id>/census     # Update current census count
GET    /api/facilities/<id>/dashboard  # Get facility dashboard metrics
```

### Devices
```
GET    /api/facilities/<id>/devices    # List devices for facility
POST   /api/devices                    # Register new device (admin only)
GET    /api/devices/<id>               # Get device details
PUT    /api/devices/<id>               # Update device (admin only)
POST   /api/devices/<id>/heartbeat     # Device check-in (updates last_seen, last_sync)
POST   /api/devices/<id>/deactivate    # Deactivate device (admin only)
```

---

## Patients

### Patient Management
```
GET    /api/patients                   # List patients in user's facility
POST   /api/patients                   # Admit new patient
GET    /api/patients/<id>              # Get patient details
PUT    /api/patients/<id>              # Update patient information
DELETE /api/patients/<id>              # Discharge patient (soft delete)
GET    /api/patients/<id>/summary      # Get comprehensive patient summary (meds, alerts, recent vitals)
GET    /api/patients/<id>/timeline     # Get patient care timeline (visits, meds, assessments)
```

### Patient Search & Filtering
```
GET    /api/patients?status=active              # Filter by status
GET    /api/patients?search=<name>              # Search by name/MRN
GET    /api/patients?is_hospice=true           # Filter hospice patients
GET    /api/patients?high_risk=true            # Filter high-risk patients
```

---

## Medications

### Medication Orders
```
GET    /api/patients/<id>/medications          # List patient's medications
POST   /api/patients/<id>/medications          # Add medication order
GET    /api/medications/<id>                   # Get medication details
PUT    /api/medications/<id>                   # Update medication order
POST   /api/medications/<id>/discontinue       # Discontinue medication
GET    /api/medications/<id>/history           # Get medication administration history
```

### Medication Administration (MAR)
```
GET    /api/patients/<id>/mar                  # Get MAR for patient (current shift or date range)
GET    /api/patients/<id>/mar/due              # Get medications due now
POST   /api/medications/<id>/administer        # Document medication administration
PUT    /api/medication-administrations/<id>    # Update administration record
GET    /api/medication-administrations/<id>    # Get administration details
```

**POST /api/medications/<id>/administer** - Request Body:
```json
{
  "scheduled_time": "2025-11-20T14:00:00Z",
  "actual_time": "2025-11-20T14:05:00Z",
  "status": "given",  // given, refused, held, omitted
  "dose_given": "500mg",
  "not_given_reason": null,
  "pre_administration_assessment": "BP 128/82, P 76",
  "administration_site": "PO",
  "prn_reason_given": "Patient c/o pain 7/10",  // if PRN
  "prn_effectiveness_rating": null,  // assess later
  "notes": "Patient tolerated well"
}
```

**POST /api/medication-administrations/<id>/reassess-prn** - PRN Effectiveness:
```json
{
  "prn_effectiveness_rating": 4,  // 1-5 scale
  "prn_effectiveness_notes": "Pain reduced to 3/10 after 30 minutes",
  "prn_reassessment_time": "2025-11-20T14:35:00Z"
}
```

### Medication Reconciliation
```
GET    /api/patients/<id>/reconciliations         # List reconciliation events
POST   /api/patients/<id>/reconciliations         # Start new reconciliation
GET    /api/reconciliations/<id>                  # Get reconciliation details (includes discrepancies)
PUT    /api/reconciliations/<id>                  # Update reconciliation
POST   /api/reconciliations/<id>/complete         # Complete reconciliation
GET    /api/reconciliations/<id>/discrepancies    # Get discrepancies for reconciliation
```

**POST /api/patients/<id>/reconciliations** - Request Body:
```json
{
  "reconciliation_type": "ADMISSION",  // ADMISSION, TRANSFER, DISCHARGE, ROUTINE_REVIEW
  "transition_from": "St. Mary's Hospital",
  "transition_to": "Sunrise TCU",
  "source_document_type": "Hospital discharge summary",
  "source_medications": [
    {
      "name": "Metformin",
      "dose": "500mg",
      "frequency": "BID",
      "route": "PO"
    }
  ],
  "current_medications": []  // Will compare against source
}
```

### Medication Discrepancies
```
GET    /api/reconciliations/<id>/discrepancies    # List discrepancies
POST   /api/discrepancies/<id>/resolve            # Resolve discrepancy
PUT    /api/discrepancies/<id>                    # Update discrepancy
```

**POST /api/discrepancies/<id>/resolve** - Request Body:
```json
{
  "resolution_action": "ACCEPTED",  // ACCEPTED, MODIFIED, DISCONTINUED, CLARIFICATION_NEEDED
  "resolution_notes": "Dose increase appropriate due to A1C 8.2",
  "resolved_by_user_id": 123
}
```

---

## Pharmacist Collaboration

### Pharmacist Interventions
```
GET    /api/patients/<id>/interventions           # List pharmacist interventions
POST   /api/patients/<id>/interventions           # Create pharmacist intervention
GET    /api/interventions/<id>                    # Get intervention details
PUT    /api/interventions/<id>                    # Update intervention
POST   /api/interventions/<id>/notify-provider    # Notify provider of intervention
POST   /api/interventions/<id>/resolve            # Resolve intervention with outcome
```

**POST /api/patients/<id>/interventions** - Request Body:
```json
{
  "intervention_type": "DRUG_INTERACTION",
  "severity": "URGENT",
  "medication_id": 456,
  "clinical_concern": "Patient on warfarin and new NSAID order - increased bleeding risk",
  "recommendation": "Consider alternative analgesic (Tylenol) or monitor INR closely",
  "clinical_rationale": "NSAIDs inhibit platelet function and increase GI bleeding risk with anticoagulants"
}
```

### Collaboration Threads
```
GET    /api/collaborations                        # List active collaboration threads (filtered by facility)
POST   /api/collaborations                        # Create collaboration thread
GET    /api/collaborations/<id>                   # Get thread with messages
PUT    /api/collaborations/<id>                   # Update thread status
POST   /api/collaborations/<id>/close             # Close thread with resolution
```

### Collaboration Messages
```
GET    /api/collaborations/<id>/messages          # Get messages in thread
POST   /api/collaborations/<id>/messages          # Add message to thread
```

**POST /api/collaborations/<id>/messages** - Request Body:
```json
{
  "message_type": "RESPONSE",  // QUESTION, RESPONSE, RECOMMENDATION, ORDER_CHANGE, RESOLUTION
  "message_text": "Agreed, will change to Tylenol 650mg q6h PRN. Please d/c ibuprofen order.",
  "attachments": []
}
```

---

## ADR Surveillance

### Patient Observations
```
GET    /api/patients/<id>/observations            # List patient observations
POST   /api/patients/<id>/observations            # Document new observation (triggers ADR surveillance)
GET    /api/observations/<id>                     # Get observation details
PUT    /api/observations/<id>                     # Update observation
```

**POST /api/patients/<id>/observations** - Request Body:
```json
{
  "observation_type": "SYMPTOM",  // SYMPTOM, VITAL_SIGN, BEHAVIOR, PHYSICAL_FINDING, LAB_RESULT
  "observation_category": "GI",
  "observation_text": "Patient reports nausea, vomited x2 this shift",
  "standardized_terms": ["nausea", "vomiting"],  // For ADR pattern matching
  "severity_rating": 6,
  "patient_reported": true,
  "observation_datetime": "2025-11-20T14:00:00Z",
  "related_vital_signs": {
    "blood_pressure": "118/72",
    "heart_rate": 88
  }
}
```

### ADR Alerts
```
GET    /api/adr-alerts                            # Get active ADR alerts (filtered by facility)
GET    /api/patients/<id>/adr-alerts              # Get alerts for specific patient
GET    /api/adr-alerts/<id>                       # Get alert details
POST   /api/adr-alerts/<id>/acknowledge           # Acknowledge alert
POST   /api/adr-alerts/<id>/escalate-pharmacist   # Escalate to pharmacist
POST   /api/adr-alerts/<id>/notify-provider       # Notify provider
POST   /api/adr-alerts/<id>/resolve               # Resolve alert with outcome
```

**POST /api/adr-alerts/<id>/acknowledge** - Request Body:
```json
{
  "notes": "Aware of alert, monitoring patient closely. Will notify provider if symptoms worsen."
}
```

**POST /api/adr-alerts/<id>/resolve** - Request Body:
```json
{
  "status": "CONFIRMED_ADR",  // CONFIRMED_ADR, NOT_ADR, DISMISSED
  "outcome_notes": "Vancomycin discontinued, symptoms resolved within 24 hours",
  "action_taken": "Medication discontinued per provider order, switched to alternative antibiotic"
}
```

### ADR Knowledge Base (Admin)
```
GET    /api/adr-knowledge                         # List known ADRs
POST   /api/adr-knowledge                         # Add known ADR (admin only)
GET    /api/adr-knowledge/<id>                    # Get ADR details
PUT    /api/adr-knowledge/<id>                    # Update ADR (admin only)
```

### ADR Surveillance Management
```
POST   /api/adr-surveillance/run-batch            # Manually trigger batch surveillance
GET    /api/adr-surveillance/logs                 # Get surveillance run logs
GET    /api/adr-surveillance/stats                # Get surveillance statistics
```

---

## Assessments

### Vital Signs
```
GET    /api/patients/<id>/vitals                  # List vital signs
POST   /api/patients/<id>/vitals                  # Record vital signs
GET    /api/vitals/<id>                           # Get specific vital signs
```

**POST /api/patients/<id>/vitals** - Request Body:
```json
{
  "temperature": 98.6,
  "temperature_unit": "F",
  "blood_pressure_systolic": 128,
  "blood_pressure_diastolic": 82,
  "heart_rate": 76,
  "respiratory_rate": 16,
  "oxygen_saturation": 98,
  "weight": 165.5,
  "weight_unit": "lbs",
  "pain_score": 3,
  "pain_location": "Lower back",
  "measured_at": "2025-11-20T08:00:00Z"
}
```

### Specialty Assessments
```
GET    /api/patients/<id>/specialty-assessments   # List specialty assessments
POST   /api/patients/<id>/specialty-assessments   # Create specialty assessment
GET    /api/specialty-assessments/<id>            # Get assessment details
PUT    /api/specialty-assessments/<id>            # Update assessment
GET    /api/specialty-assessments/types           # Get available assessment types by body system
```

**POST /api/patients/<id>/specialty-assessments** - Request Body:
```json
{
  "body_system": "INTEGUMENTARY",
  "assessment_subtype": "BURN_ASSESSMENT",
  "assessment_data": {
    "burn_location": "Right forearm",
    "burn_depth": "Partial thickness",
    "tbsa_percentage": 3,
    "rule_of_nines_calculation": {...},
    "pain_level": 6,
    "treatment_plan": "Silvadene cream BID, dressing changes daily"
  }
}
```

### Wound Care
```
GET    /api/patients/<id>/wounds                  # List wounds
POST   /api/patients/<id>/wounds                  # Document new wound
GET    /api/wounds/<id>                           # Get wound details
PUT    /api/wounds/<id>                           # Update wound assessment
POST   /api/wounds/<id>/photos                    # Upload wound photo
GET    /api/wounds/<id>/history                   # Get wound healing progression
POST   /api/wounds/<id>/close                     # Mark wound as healed/closed
```

**POST /api/patients/<id>/wounds** - Request Body:
```json
{
  "wound_type": "PRESSURE_ULCER",
  "location": "Sacrum",
  "stage": "Stage 2",
  "length_cm": 3.5,
  "width_cm": 2.8,
  "depth_cm": 0.5,
  "appearance": "Pink, granulating tissue",
  "drainage_type": "Serous",
  "drainage_amount": "Minimal",
  "odor": "None",
  "treatment": "DuoDerm dressing, turn q2h"
}
```

---

## Visits & Documentation

### Visits
```
GET    /api/patients/<id>/visits                  # List visits for patient
POST   /api/patients/<id>/visits                  # Start new visit
GET    /api/visits/<id>                           # Get visit details
PUT    /api/visits/<id>                           # Update visit documentation
POST   /api/visits/<id>/complete                  # Complete and sign visit
```

**POST /api/patients/<id>/visits** - Request Body:
```json
{
  "visit_type": "ROUTINE",  // ROUTINE, ADMISSION, DISCHARGE, PRN, ASSESSMENT
  "visit_purpose": "Weekly nursing assessment",
  "scheduled_datetime": "2025-11-20T10:00:00Z",
  "actual_datetime": "2025-11-20T10:15:00Z"
}
```

---

## Caregiver Support

### Stress Assessments
```
GET    /api/caregiver-support/assessments         # List stress assessments
POST   /api/caregiver-support/assessments         # Create stress assessment
GET    /api/caregiver-support/assessments/<id>    # Get assessment details
GET    /api/caregiver-support/high-risk           # Get high-risk caregivers
```

### Interventions
```
GET    /api/caregiver-support/interventions       # List interventions
POST   /api/caregiver-support/interventions       # Create intervention
GET    /api/caregiver-support/interventions/<id>  # Get intervention details
PUT    /api/caregiver-support/interventions/<id>  # Update intervention
```

### Wellness Dashboard
```
GET    /api/caregiver-support/dashboard           # Get team wellness metrics
GET    /api/caregiver-support/turnover-risk       # Get turnover risk analysis
GET    /api/caregiver-support/intervention-effectiveness  # Get intervention effectiveness report
```

---

## Reports & Analytics

### Facility Reports
```
GET    /api/reports/census                        # Current census report
GET    /api/reports/medication-errors             # Medication error tracking
GET    /api/reports/adr-summary                   # ADR alert summary
GET    /api/reports/staff-productivity            # Staff productivity metrics
GET    /api/reports/quality-indicators            # Quality indicator dashboard
```

### Patient Reports
```
GET    /api/reports/patients/<id>/care-summary    # Comprehensive care summary (for discharge/transfer)
GET    /api/reports/patients/<id>/medication-list # Current medication list
GET    /api/reports/patients/<id>/progress-notes  # Progress notes report
```

---

## Audit Logs

### Audit Trail
```
GET    /api/audit-logs                            # List audit logs (admin only, filtered)
GET    /api/audit-logs/patient/<id>               # Get audit trail for specific patient
GET    /api/audit-logs/user/<id>                  # Get audit trail for specific user
```

**Query Parameters**:
```
?action=CREATE,UPDATE,DELETE,ACCESS
?resource_type=Patient,Medication,Assessment
?start_date=2025-11-01
&end_date=2025-11-30
&contains_phi=true
```

---

## Health & System

### System Health
```
GET    /health                                    # Health check (no auth required)
GET    /                                          # API info
```

---

## Query Parameters (Global)

Most list endpoints support:
```
?page=1              # Pagination (default page size: 50)
&per_page=100        # Items per page
&sort_by=created_at  # Sort field
&sort_order=desc     # Sort direction (asc/desc)
&search=<term>       # Text search (where applicable)
```

---

## Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

### Paginated Response
```json
{
  "status": "success",
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 5,
    "total_items": 234
  }
}
```

---

## HTTP Status Codes

```
200 OK                  - Request succeeded
201 Created             - Resource created successfully
204 No Content          - Successful deletion
400 Bad Request         - Invalid request data
401 Unauthorized        - Missing or invalid JWT token
403 Forbidden           - User lacks required permissions
404 Not Found           - Resource not found
409 Conflict            - Resource conflict (duplicate)
422 Unprocessable       - Validation error
500 Internal Error      - Server error
```

---

## Permission Requirements

### By Role

**Admin**:
- Full access to all endpoints
- Organization/facility/device management
- User management
- System configuration

**RN (Registered Nurse)**:
- Full patient care documentation
- Medication administration and reconciliation
- Assessment documentation
- Create pharmacist interventions
- Access all patients in facility

**LPN (Licensed Practical Nurse)**:
- Patient care documentation (limited)
- Medication administration (no IV push)
- Vital signs and routine assessments
- View pharmacist interventions
- Access assigned patients only

**CNA (Certified Nursing Assistant)**:
- Vital signs documentation
- Basic patient observations
- ADL documentation
- View patient care plans
- Access assigned patients only

**Pharmacist**:
- View all medications
- Create/respond to interventions
- Medication reconciliation review
- ADR alert management
- Clinical decision support

**Family Caregiver** (future):
- View assigned patient info (limited)
- Document care provided
- View medication schedule
- No access to clinical interventions

---

## Rate Limiting

```
- 1000 requests per hour per user
- 100 requests per minute per user
- Burst allowance: 20 requests per 10 seconds
```

**Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1700515200
```

---

## Webhooks (Future)

```
POST   /api/webhooks/register                    # Register webhook endpoint
GET    /api/webhooks                             # List registered webhooks
DELETE /api/webhooks/<id>                        # Unregister webhook
```

**Events**:
- `patient.admitted`
- `patient.discharged`
- `medication.reconciliation.completed`
- `adr.alert.created`
- `adr.alert.escalated`
- `intervention.created`
- `device.offline`

---

## Notes for Frontend Implementation

1. **Token Management**: Store JWT in httpOnly cookie or secure localStorage. Refresh before expiry.

2. **Real-Time Updates**: Consider WebSocket connection for:
   - ADR alerts (immediate notification)
   - Pharmacist collaboration messages
   - Device status changes
   - Census updates

3. **Offline Support**: 
   - Queue failed requests for retry
   - Cache GET responses with timestamps
   - Sync when connection restored

4. **File Uploads**: Wound photos, discharge summaries
   - Use multipart/form-data
   - Compress images client-side
   - Show upload progress

5. **Print-Friendly**: MAR, care summaries, discharge instructions need print CSS

6. **Mobile Optimization**: All routes should work on tablets (Pi touchscreen UI)
