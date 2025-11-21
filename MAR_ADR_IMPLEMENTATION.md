# MAR & ADR Alert Routes - Implementation Summary

## Completed Routes

### Medication Administration Record (MAR)

**File**: `/backend/app/routes/medications.py`

#### 1. Get Patient Medications
```
GET /api/patients/<patient_id>/medications
```
- Lists all patient medications (active by default)
- Filters: `status`, `include_history`
- Enriched with last administration and next due time
- RBAC: All authenticated users (filtered by facility)

#### 2. Get Due Medications
```
GET /api/patients/<patient_id>/mar/due
```
- Returns medications due now or within window
- Query params: `window_hours` (default 2), `include_prn`, `shift`
- Separates scheduled vs PRN medications
- Real-time due calculation based on last administration

#### 3. Administer Medication
```
POST /api/medications/<medication_id>/administer
```
- Documents medication administration
- Validates required fields based on status (given/refused/held/omitted)
- Requires PRN reason for PRN medications
- Creates MedicationAdministration record with audit trail
- RBAC: RN, LPN, Admin only

**Request Body Example**:
```json
{
  "scheduled_time": "2025-11-20T14:00:00Z",
  "actual_time": "2025-11-20T14:05:00Z",
  "status": "given",
  "dose_given": "500mg",
  "pre_administration_assessment": "BP 128/82, P 76",
  "administration_site": "PO",
  "prn_reason_given": "Patient c/o pain 7/10",
  "notes": "Patient tolerated well"
}
```

#### 4. PRN Effectiveness Reassessment
```
POST /api/medication-administrations/<admin_id>/reassess-prn
```
- Documents PRN medication effectiveness (1-5 scale)
- Validates this is a PRN medication that was given
- Records reassessment time and detailed notes
- Critical for Memory Care behavior medication tracking
- RBAC: RN, LPN, Admin only

**Request Body Example**:
```json
{
  "prn_effectiveness_rating": 4,
  "prn_effectiveness_notes": "Pain reduced to 3/10 after 30 minutes",
  "prn_reassessment_time": "2025-11-20T14:35:00Z"
}
```

#### 5. Get Full MAR
```
GET /api/patients/<patient_id>/mar
```
- Complete MAR for date range
- Shows all medications with administration history
- Calculates statistics (given_count, missed_count)
- Query params: `start_date`, `end_date`, `shift`
- Print-ready format for regulatory compliance

#### 6. Get Administration Details
```
GET /api/medication-administrations/<admin_id>
```
- Detailed view of single administration record
- Includes medication and patient info
- Used for reviewing/auditing specific administrations

---

### ADR Surveillance & Alerts

**File**: `/backend/app/routes/adr_alerts.py`

#### 1. Create Patient Observation
```
POST /api/patients/<patient_id>/observations
```
- Documents patient symptoms, vital signs, behaviors, physical findings
- **Automatically triggers ADR surveillance** via `ADRSurveillanceService.analyze_observation()`
- Captures structured data for pattern matching (standardized_terms)
- Returns any ADR alerts generated
- RBAC: RN, LPN, CNA, Admin

**Request Body Example**:
```json
{
  "observation_type": "SYMPTOM",
  "observation_category": "GI",
  "observation_text": "Patient reports nausea, vomited x2 this shift",
  "standardized_terms": ["nausea", "vomiting"],
  "severity_rating": 6,
  "patient_reported": true,
  "observation_datetime": "2025-11-20T14:00:00Z",
  "related_vital_signs": {
    "blood_pressure": "118/72",
    "heart_rate": 88
  }
}
```

**Response includes**:
```json
{
  "status": "success",
  "data": { ...observation... },
  "adr_alerts_generated": 2,
  "message": "Observation documented. 2 ADR alert(s) generated."
}
```

#### 2. Get Patient Observations
```
GET /api/patients/<patient_id>/observations
```
- Lists patient observations with optional filters
- Query params: `days` (default 7), `type`, `with_alerts` (only obs that triggered alerts)
- Used for trending patient condition over time

#### 3. Get ADR Alerts (Dashboard)
```
GET /api/adr-alerts
```
- **Primary dashboard endpoint** for ADR surveillance
- Returns active alerts for facility sorted by urgency
- Filters: `status`, `severity`, `confidence`, `patient_id`, `days`
- Default: Shows NEW, ACKNOWLEDGED, INVESTIGATING alerts
- Urgency ordering: STAT → URGENT → ROUTINE
- Enriched with patient name and room number

#### 4. Get Patient ADR Alerts
```
GET /api/patients/<patient_id>/adr-alerts
```
- All ADR alerts for specific patient
- Filtered by status and date range
- Used in patient summary views

#### 5. Get Alert Details
```
GET /api/adr-alerts/<alert_id>
```
- Comprehensive alert information
- Includes: patient, medication, observation, pharmacist intervention (if escalated)
- Shows correlation details (matching symptoms, vital signs, behaviors)
- Displays nursing interventions vs provider orders (scope of practice)
- Hospice-specific comfort guidance if applicable

#### 6. Acknowledge Alert
```
POST /api/adr-alerts/<alert_id>/acknowledge
```
- Nurse acknowledges awareness of alert
- Updates status to ACKNOWLEDGED
- Records acknowledging user and timestamp
- Optional notes field
- RBAC: RN, LPN, Admin only

**Request Body Example**:
```json
{
  "notes": "Aware of alert, monitoring patient closely. Will notify provider if symptoms worsen."
}
```

#### 7. Escalate to Pharmacist
```
POST /api/adr-alerts/<alert_id>/escalate-pharmacist
```
- Creates PharmacistIntervention record
- Links intervention to ADR alert
- Updates alert status to INVESTIGATING
- Intervention type: ADR_EVALUATION
- Severity based on alert urgency (STAT → URGENT)
- RBAC: RN, LPN, Admin only

**Workflow**:
1. Nurse escalates alert
2. System creates intervention with clinical concern
3. Pharmacist sees intervention in their queue
4. Pharmacist reviews and provides recommendation
5. Provider collaboration ensues if needed

#### 8. Notify Provider
```
POST /api/adr-alerts/<alert_id>/notify-provider
```
- Documents that provider was notified
- Records notification method, provider name, response
- Appends to investigation notes timeline
- RBAC: RN, LPN, Admin only

**Request Body Example**:
```json
{
  "notification_method": "Phone call",
  "provider_name": "Dr. Smith",
  "provider_response": "Will evaluate patient, may discontinue medication"
}
```

#### 9. Resolve Alert
```
POST /api/adr-alerts/<alert_id>/resolve
```
- Closes alert with outcome determination
- Final statuses: CONFIRMED_ADR, NOT_ADR, DISMISSED
- Requires outcome notes and optional action taken
- Records resolution time for metrics
- RBAC: RN, Admin, Pharmacist

**Request Body Example**:
```json
{
  "status": "CONFIRMED_ADR",
  "outcome_notes": "Vancomycin discontinued, symptoms resolved within 24 hours",
  "action_taken": "Medication discontinued per provider order, switched to alternative antibiotic"
}
```

---

## Key Features Implemented

### MAR Functionality
✅ **Real-time medication due calculations** - Window-based lookups for shift workflow  
✅ **Status tracking** - Given, refused, held, omitted with required reasons  
✅ **PRN effectiveness tracking** - 1-5 scale ratings with reassessment times  
✅ **Pre/post administration assessments** - Vital signs, patient response  
✅ **Witness documentation** - For controlled substances  
✅ **Date range MAR views** - Daily, weekly, custom periods  
✅ **Audit logging** - Every administration logged to AuditLog  
✅ **RBAC enforcement** - Role-based access (RN/LPN can administer, CNA cannot)  

### ADR Surveillance
✅ **Automatic surveillance trigger** - Every observation analyzed in real-time  
✅ **Pattern matching** - Symptoms, vital signs, behaviors correlated with known ADRs  
✅ **Confidence scoring** - LOW → MODERATE → HIGH → VERY_HIGH based on correlation  
✅ **Urgency classification** - ROUTINE, URGENT, STAT based on severity  
✅ **Hospice awareness** - Different guidance for hospice patients (comfort-focused)  
✅ **Scope of practice separation** - Nursing interventions vs provider orders  
✅ **Escalation workflow** - Acknowledge → Escalate to pharmacist → Notify provider → Resolve  
✅ **Timeline tracking** - Response time, resolution time metrics  
✅ **Multi-factor correlation** - Timing (onset), risk factors, symptom clusters  

### Clinical Workflows Supported

**MAR Shift Workflow**:
1. Nurse starts shift
2. GET `/api/patients/<id>/mar/due?window_hours=2` → See medications due
3. Prepare medications
4. POST `/api/medications/<id>/administer` → Document administration
5. (For PRN) Wait 30-60 min
6. POST `/api/medication-administrations/<id>/reassess-prn` → Rate effectiveness

**ADR Detection Workflow**:
1. CNA observes patient: "Patient vomited, looks pale"
2. POST `/api/patients/<id>/observations` → System automatically runs surveillance
3. System detects correlation: Patient on vancomycin, vomiting/nausea are known ADR
4. ADR alert generated with HIGH confidence
5. RN sees alert on dashboard: GET `/api/adr-alerts`
6. RN acknowledges: POST `/api/adr-alerts/<id>/acknowledge`
7. Symptoms worsen → RN escalates: POST `/api/adr-alerts/<id>/escalate-pharmacist`
8. Pharmacist reviews, recommends discontinuation
9. RN notifies provider: POST `/api/adr-alerts/<id>/notify-provider`
10. Provider orders alternative antibiotic
11. Symptoms resolve → RN closes: POST `/api/adr-alerts/<id>/resolve` → CONFIRMED_ADR

**Hospice Workflow**:
1. Observation created for hospice patient
2. ADR alert generated but marked `is_hospice_patient: true`
3. Alert shows comfort-focused guidance (not curative)
4. Explicit "Do NOT call 911" messaging
5. Hospice nurse contact info displayed
6. Suggested interventions focus on comfort measures

---

## Integration Points

### With Existing Models
- **Medication** model: Used for med lookups, high-risk flags
- **MedicationAdministration** model: Created by administer endpoint
- **Patient** model: Access control, hospice status checks
- **User** model: RBAC, audit trail (who did what)
- **AuditLog** model: Every action logged for HIPAA compliance
- **PharmacistIntervention** model: Created when alerts escalated

### With Existing Services
- **ADRSurveillanceService**: Called automatically when observations created
- Pattern matching algorithms: `_evaluate_correlation()`
- Hospice detection: `_generate_hospice_comfort_guidance()`

### Blueprint Registration
- Both blueprints registered in `/backend/app/__init__.py`
- Routes mounted at `/api` prefix
- JWT authentication on all routes
- RBAC decorators on restricted routes

---

## Database Updates Required

### Migration Needed
```bash
flask db migrate -m "Add resolved_by_user_id to ADRAlert"
flask db upgrade
```

**Changes**:
- Added `resolved_by_user_id` column to `adr_alerts` table
- Added `resolved_by` relationship to User model

---

## Testing the Routes

### MAR Testing
```bash
# Get due medications
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/patients/1/mar/due?window_hours=4

# Administer medication
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_time": "2025-11-20T14:00:00Z",
    "actual_time": "2025-11-20T14:05:00Z",
    "status": "given",
    "dose_given": "500mg",
    "pre_administration_assessment": "BP 128/82",
    "prn_reason_given": "Pain 7/10"
  }' \
  http://localhost:5000/api/medications/5/administer

# Document PRN effectiveness
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prn_effectiveness_rating": 4,
    "prn_effectiveness_notes": "Pain reduced to 3/10"
  }' \
  http://localhost:5000/api/medication-administrations/123/reassess-prn
```

### ADR Testing
```bash
# Create observation (triggers surveillance)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "observation_type": "SYMPTOM",
    "observation_category": "GI",
    "observation_text": "Patient reports nausea",
    "standardized_terms": ["nausea", "vomiting"],
    "severity_rating": 6
  }' \
  http://localhost:5000/api/patients/1/observations

# Get ADR alerts dashboard
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/adr-alerts?status=NEW

# Acknowledge alert
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Monitoring patient, will notify provider if worsens"
  }' \
  http://localhost:5000/api/adr-alerts/10/acknowledge

# Escalate to pharmacist
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/adr-alerts/10/escalate-pharmacist

# Resolve alert
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "CONFIRMED_ADR",
    "outcome_notes": "Medication discontinued, symptoms resolved"
  }' \
  http://localhost:5000/api/adr-alerts/10/resolve
```

---

## Next Steps

### Immediate
1. Run database migration for `resolved_by_user_id` field
2. Test routes with Postman or curl
3. Seed ADR knowledge base (MedicationAdverseReaction records)
4. Seed test medications and patients

### Frontend Integration
- MAR UI showing due medications with administer button
- PRN effectiveness modal popup (30-60 min post-admin reminder)
- ADR alert dashboard with urgency color coding
- Observation documentation form with standardized term picker
- Alert detail view with escalation/resolution workflow buttons

### Performance Optimization
- Index on `observation_datetime`, `status`, `facility_id` for fast queries
- Cache active medications per patient (reduce repeated queries)
- Batch surveillance for nightly reviews (supplement real-time)
- WebSocket notifications for new STAT alerts

### Additional Features (Future)
- Barcode scanning for medication verification
- Photo upload for PRN reassessment (behavior documentation)
- Push notifications for high-urgency alerts
- ADR reporting to FDA MedWatch
- Analytics dashboard (ADR trends, medication error rates)
