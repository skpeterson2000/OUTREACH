# EHR Training Scenarios & Simulation Guide

## Overview
This EHR system includes realistic training scenarios to onboard new staff in a safe simulation environment. Staff can practice workflows, learn documentation standards, and experience clinical decision-making without affecting real patient care.

---

## Training Environment Features

### Realistic Data
- **7 days of medication administration history** for all active patients
- **Mixed documentation** by RN, LPN, and TMA staff showing different documentation styles
- **PRN medications** with realistic usage patterns and pain reassessments
- **Held medications** demonstrating clinical judgment (e.g., digoxin held for low HR)
- **High-risk medications** including anticoagulants, insulin, and opioids
- **Sliding scale insulin** with documented blood glucose readings and dose calculations

### Patient Scenarios

#### 1. Mary Anderson (MRN001) - **Simple Routine Care**
**Complexity:** Low | **Use for:** Basic MAR navigation, routine medication administration

**Diagnoses:** Hypertension, Type 2 Diabetes  
**Medications:**
- Lisinopril 10mg PO daily @ 08:00 (consistently given, 7-day history)
- Metformin 500mg PO BID @ 08:00 & 18:00 (14 administrations over 7 days)
- Insulin Regular (sliding scale) AC & HS (variable dosing based on BG)

**Training Focus:**
- Navigate MAR and view previous administrations
- Understand scheduled vs PRN medications
- Practice sliding scale insulin calculator
- Document routine medication administration
- Review blood glucose patterns

**Realistic Patterns:**
- Consistent adherence to med schedule
- Insulin held when BG <150 (no coverage needed)
- Doses given by mix of RN, LPN, and TMA (demonstrates delegation)

---

#### 2. Robert Johnson (MRN002) - **Complex Hospice with PRN Management**
**Complexity:** High | **Use for:** Advanced assessment, PRN decision-making, ADR monitoring

**Diagnoses:** CHF, COPD, CKD Stage 3 (hospice)  
**High Risk:** Fall risk score 11, Digoxin toxicity alert  

**Medications:**
- Furosemide 40mg PO BID @ 08:00 & 14:00 (14 doses over 7 days)
- Albuterol 2.5mg INH QID @ 08:00, 12:00, 16:00, 20:00 (28 doses over 7 days)
- Morphine 5mg PO PRN for pain/dyspnea (8 administrations with varying symptoms)
- Digoxin 0.125mg PO daily @ 08:00 (6 doses given, 1 held for HR 54)

**Training Focus:**
- PRN decision-making and documentation
- Pre/post pain/dyspnea assessment
- Holding medications based on parameters (HR <60)
- ADR alert acknowledgment workflow
- Hospice symptom management
- Complex polypharmacy

**Realistic Patterns:**
- Increasing morphine use over 7 days (realistic hospice trajectory)
- One digoxin dose held with clear documentation of vital sign and MD notification
- Morphine given for both pain and dyspnea with effective reassessments
- **Active ADR Alert:** Digoxin toxicity (bradycardia, visual changes) requiring acknowledgment

**Training Scenario:**
1. Review patient chart and ADR alert
2. Acknowledge alert (requires 3-step verification)
3. Check HR before digoxin administration
4. Assess for dyspnea and decide if morphine PRN needed
5. Document pain/dyspnea scale before and after

---

#### 3. Patricia Williams (MRN003) - **Post-Surgical Pain Management**
**Complexity:** Moderate | **Use for:** Pain management, injection technique, reconciliation

**Diagnoses:** Post-surgical (hip replacement), Hypothyroidism  
**Status:** POD #7, preparing for discharge  

**Medications:**
- Oxycodone 5mg PO Q4-6H PRN pain (18 administrations, decreasing frequency = healing)
- Enoxaparin 40mg SUBQ daily @ 20:00 (7 doses, rotating injection sites documented)
- Levothyroxine 75mcg PO daily @ 06:00 (7 doses on empty stomach)

**Training Focus:**
- PRN pain management with reassessment
- Injection site rotation and documentation
- Post-op recovery patterns
- **Medication reconciliation** (3 discrepancies to resolve)
- Preparing patient for discharge

**Realistic Patterns:**
- Pain scores decrease over 7 days: 9/10 → 8/10 → 6/10 → 2/10 (healing progression)
- Oxycodone frequency: 3x/day early → 1-2x/day by day 7
- Pain reassessment 30min after each dose with effectiveness rating
- Enoxaparin sites documented: left/right abdomen, left/right thigh rotation

**Training Scenario:**
1. Review patient's pain trend over past 7 days
2. Patient requests pain medication - assess and decide if indicated
3. Administer oxycodone with pain scale documentation
4. Return in 30min for pain reassessment
5. Complete medication reconciliation (identify omission of home ibuprofen)

---

#### 4. James Brown (MRN004) - **High-Risk Anticoagulation**
**Complexity:** High | **Use for:** High-risk medication management, INR monitoring

**Diagnoses:** Atrial fibrillation, Type 1 Diabetes  
**High Risk:** Warfarin management, insulin pump  

**Medications:**
- Warfarin 5mg PO daily @ 18:00 (7 doses with INR monitoring notes)
- Insulin Aspart pump (continuous)
- Insulin Glargine 20 units SUBQ HS (long-acting)

**Training Focus:**
- Warfarin safety and INR interpretation
- High-risk medication double-checks
- Anticoagulation patient education
- Insulin pump vs injection administration

**Realistic Patterns:**
- INR checked on days 0 and 3: 2.4 and 2.6 (therapeutic range 2-3)
- Warfarin given consistently at same time daily by RN only (no delegation for warfarin)
- Documentation includes INR results with plan to continue current dose

**Training Scenario:**
1. Review INR trend and warfarin dosing
2. Check today's INR: 2.4 (therapeutic)
3. Administer warfarin with patient education on dietary consistency
4. Document INR result and therapeutic range
5. Educate patient on signs of bleeding

---

## Role-Based Training Paths

### RN (Registered Nurse) Training
**Access:** Full medication administration, holds, modifications, ADR acknowledgment

**Day 1:** Simple case (Mary Anderson)
- Navigate MAR interface
- Document routine medications
- Use sliding scale insulin calculator

**Day 2:** Complex case (Robert Johnson)
- PRN decision-making for hospice patient
- Hold medication based on vital signs
- Acknowledge ADR alert

**Day 3:** High-risk medications (James Brown)
- Warfarin management and INR monitoring
- High-risk medication protocols

---

### LPN (Licensed Practical Nurse) Training
**Access:** Medication administration, cannot modify orders

**Day 1:** Simple case (Mary Anderson)
- Basic MAR documentation
- Sliding scale insulin with supervision

**Day 2:** Post-surgical (Patricia Williams)
- PRN pain management
- Injection administration and site rotation

**Day 3:** Complex case (Robert Johnson)
- PRN symptom management
- Holding parameters (with RN consultation)

---

### TMA (Trained Medication Assistant) Training
**Access:** Delegated medication administration, cannot hold or modify

**Day 1:** Simple case (Mary Anderson)
- Routine oral medications only
- Basic documentation
- Understanding delegation scope

**Day 2:** Supervised insulin administration
- Sliding scale calculator
- Blood glucose documentation
- When to escalate to RN

**Day 3:** Multiple patient medications
- Time management with med pass
- Recognizing when RN assessment needed

---

### CNA/HHA (Support Staff) Training
**Access:** View-only, can request reorders and report concerns

**Day 1:** Navigation and reporting
- View patient medications
- Request medication reorder
- Report concerns to nurse

**Day 2:** Observation and documentation
- Recognize medication side effects
- Report PRN needs to nurse
- Assist with medication administration

---

## Training Scenarios by Clinical Skill

### Scenario 1: Sliding Scale Insulin Management
**Patient:** Mary Anderson  
**Skill Level:** Intermediate  

**Setup:**
1. Patient's pre-breakfast BG = 220 mg/dL
2. Order: Insulin Regular per sliding scale AC & HS

**Steps:**
1. Open MAR for Mary Anderson
2. Click "Give" on Insulin Regular
3. Enter blood glucose: 220
4. System calculates: 4 units per protocol
5. Verify dose on visual sliding scale
6. Check verification box
7. Document administration with BG reading

**Expected Outcomes:**
- Correct dose calculated (4 units for BG 201-250)
- Warning if BG <70 (hypoglycemia protocol)
- Critical alert if BG >400 (notify MD)

---

### Scenario 2: Holding Medications Based on Parameters
**Patient:** Robert Johnson  
**Skill Level:** Advanced  

**Setup:**
1. Patient's HR = 54 bpm (baseline usually 68-75)
2. Digoxin 0.125mg scheduled for 08:00
3. Order states: "Hold if HR <60"

**Steps:**
1. Take patient vital signs: HR 54, BP 110/70
2. Recognize HR below hold parameter
3. Open MAR and click "Give" on digoxin
4. Note the hold parameter warning
5. Click "Hold" instead of administering
6. Document reason: "HELD: HR 54 bpm per hold parameters"
7. Notify MD of held dose
8. Document MD notification in notes

**Expected Outcomes:**
- Medication held appropriately
- Clear documentation of vital sign and decision
- MD notification documented
- Understand when to recheck and potentially give later

---

### Scenario 3: PRN Pain Management with Reassessment
**Patient:** Patricia Williams  
**Skill Level:** Intermediate  

**Setup:**
1. Patient reports post-surgical pain 7/10
2. Last oxycodone dose was 6 hours ago (safe to give)
3. Order: Oxycodone 5mg PO Q4-6H PRN pain

**Steps:**
1. Assess patient pain: 7/10, sharp, at surgical site
2. Verify time since last dose (6hrs = safe)
3. Open MAR, click "Give" on Oxycodone
4. Enter PRN reason: "Post-surgical incision pain"
5. Enter pain level before: 7
6. Administer medication
7. Return in 30 minutes for reassessment
8. Enter pain level after: 3
9. Enter effectiveness rating: 5 (very effective)
10. Document: "Pain reduced from 7/10 to 3/10. Patient able to participate in PT."

**Expected Outcomes:**
- Proper assessment before administration
- Timely reassessment (30min for PO, 15min for IV)
- Documentation shows intervention effectiveness
- Pain management trend visible in history

---

### Scenario 4: ADR Alert Acknowledgment
**Patient:** Robert Johnson  
**Skill Level:** Advanced  

**Setup:**
1. Active ADR alert for digoxin toxicity
2. Correlation with bradycardia and visual changes
3. Must acknowledge before administering digoxin

**Steps:**
1. Open patient chart for Robert Johnson
2. See red ADR alert banner
3. Click "Acknowledge" button
4. Read alert details: bradycardia, blurred vision, nausea
5. Review nursing interventions required
6. Check 3 required acknowledgment boxes:
   - ✅ I have read and understood this alert
   - ✅ I will verify monitoring parameters BEFORE EACH administration
   - ✅ I will implement recommended interventions
7. Add notes about plan
8. Submit acknowledgment
9. See legal notice: "Recorded in permanent medical record"

**Expected Outcomes:**
- Understanding of ADR alert significance
- Proper acknowledgment workflow
- Commitment to enhanced monitoring
- Alert remains visible but marked as acknowledged

---

## Assessing Trainee Competency

### Documentation Quality Checklist
- ✅ All required fields completed
- ✅ Clear, concise notes without abbreviations
- ✅ Time stamps accurate
- ✅ Pre/post assessments for PRN medications
- ✅ Proper signature and credentials

### Clinical Decision-Making
- ✅ Appropriate PRN medication decisions
- ✅ Holds medications when parameters not met
- ✅ Recognizes need for RN assessment (for TMAs/CNAs)
- ✅ Proper escalation of concerns
- ✅ Patient safety prioritized

### System Navigation
- ✅ Efficient MAR navigation
- ✅ Can locate previous administrations
- ✅ Uses insulin calculator correctly
- ✅ Completes ADR acknowledgment workflow
- ✅ Finds patient information quickly

---

## Training Completion Criteria

### Basic Competency (CNA/HHA)
- Navigate patient list and view medications
- Report concerns using proper channels
- Recognize medication side effects
- Request reorders appropriately

### Intermediate Competency (TMA)
- Administer routine oral medications
- Use sliding scale insulin calculator
- Document clearly and completely
- Recognize when to escalate to RN

### Advanced Competency (LPN/RN)
- Manage complex medication schedules
- Make PRN medication decisions
- Hold medications based on parameters
- Complete medication reconciliation
- Acknowledge and act on ADR alerts
- Educate patients on medications

---

## Next Steps: Building Custom Scenarios

The system supports creating additional scenarios:

1. **Time-based scenarios** - Schedule patients to receive meds at specific times during training
2. **Error recovery** - Intentionally create documentation errors for trainees to find and correct
3. **Emergency scenarios** - PRN medications for acute changes (breakthrough pain, respiratory distress)
4. **Discharge planning** - Complete medication reconciliation before discharge
5. **Shift handoff** - Review medications administered during shift for handoff report

**To add new scenarios:** Modify `backend/seed_data.py` and regenerate database with `/home/pc/OUTREACH/.venv/bin/python seed_data.py`

---

## Support & Questions

For questions about training scenarios or to report issues:
- Review this document
- Check patient charts for realistic patterns
- Consult with facility trainer or preceptor
- Submit feedback for scenario improvements

**Remember:** This is a training environment. All data is simulated. Practice freely to build confidence before working with real patients.
