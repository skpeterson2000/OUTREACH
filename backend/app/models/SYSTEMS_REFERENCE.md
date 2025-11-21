"""Documentation for systems-based assessment organization."""

# BODY SYSTEMS ASSESSMENT ORGANIZATION

This module organizes clinical assessments by major body systems, providing 
comprehensive tools for documenting patient conditions across all physiological systems.

## Body Systems Structure

### 1. INTEGUMENTARY SYSTEM
Skin, hair, nails, burns, wounds, pressure injuries

**Assessment Subtypes:**
- burn_assessment - TBSA calculation, Rule of Nines, depth classification
- wound_assessment - (See wound.py model for full wound documentation)
- pressure_injury - Braden Scale, staging, prevention
- skin_integrity - General skin condition, rashes, lesions
- surgical_site - Post-op wound monitoring

**Tools:**
- calculate_tbsa_adults()
- calculate_tbsa_pediatric()
- classify_burn_severity()
- calculate_braden_scale()


### 2. RESPIRATORY SYSTEM
Lungs, breathing, oxygenation

**Assessment Subtypes:**
- copd_assessment - CAT score, exacerbation monitoring
- asthma_assessment - Control test, peak flow monitoring
- pneumonia_assessment - Signs, symptoms, severity
- oxygen_therapy - Requirements, delivery method, weaning
- tracheostomy_care - Site assessment, secretion management
- respiratory_distress - Scoring and severity classification
- sleep_apnea - CPAP compliance, symptoms

**Tools:**
- calculate_respiratory_distress_score()
- copd_assessment_test()


### 3. CARDIOVASCULAR SYSTEM
Heart, circulation, blood vessels

**Assessment Subtypes:**
- heart_failure - CHF symptom tracking, fluid status
- hypertension - BP monitoring, medication compliance
- peripheral_vascular - Arterial/venous insufficiency
- dvt_assessment - Wells criteria, signs/symptoms
- arrhythmia - Heart rhythm, palpitations
- post_cardiac_surgery - Sternal healing, recovery progress

**Tools:**
- calculate_chf_symptoms_score()
- assess_peripheral_vascular()


### 4. NEUROLOGICAL SYSTEM
Brain, nerves, consciousness, cognition

**Assessment Subtypes:**
- stroke_assessment - NIHSS, recovery monitoring
- seizure_monitoring - Frequency, triggers, compliance
- pain_assessment - Comprehensive pain evaluation
- cognitive_function - Memory, orientation, executive function
- consciousness_level - Glasgow Coma Scale
- peripheral_neuropathy - Sensation, reflexes
- parkinson_assessment - Tremor, rigidity, gait

**Tools:**
- glasgow_coma_scale()
- stroke_assessment_nihss_simplified()
- pain_assessment_comprehensive()


### 5. GASTROINTESTINAL SYSTEM
Digestion, nutrition, elimination

**Assessment Subtypes:**
- nutrition_assessment - BMI, malnutrition screening
- swallowing_assessment - Dysphagia screening
- bowel_function - Constipation, diarrhea, ostomy
- tube_feeding - Tolerance, residuals, complications
- ostomy_care - Output, skin integrity, appliance fit
- nausea_vomiting - Severity, triggers, management
- liver_function - Jaundice, ascites, encephalopathy

**Tools:**
- calculate_bmi()
- classify_bmi()
- malnutrition_screening_tool()
- swallowing_assessment()


### 6. GENITOURINARY SYSTEM
Kidneys, bladder, urinary function

**Assessment Subtypes:**
- catheter_care - Type, output, complications
- bladder_function - Voiding pattern, incontinence
- renal_function - Output, fluid balance, labs
- incontinence_assessment - Type, frequency, management
- dialysis_care - Access site, schedule, complications

**Tools:**
- bladder_function_assessment()


### 7. MUSCULOSKELETAL SYSTEM
Bones, muscles, joints, mobility

**Assessment Subtypes:**
- mobility_assessment - Gait, transfers, assistive devices
- fall_risk - Morse Fall Scale, prevention strategies
- amputation_care - Stump care, prosthetic fitting
- fracture_care - Healing progress, cast care
- arthritis_assessment - Joint pain, ROM, function
- adls - Activities of Daily Living, Barthel Index
- physical_therapy - Progress, goals, exercises

**Tools:**
- morse_fall_scale()
- timed_up_and_go()
- barthel_index()


### 8. ENDOCRINE SYSTEM
Hormones, metabolism, glucose regulation

**Assessment Subtypes:**
- diabetes_management - Glucose monitoring, A1C tracking
- diabetic_foot - Comprehensive foot assessment
- thyroid_function - Signs of hypo/hyperthyroidism
- glucose_management - Hypo/hyperglycemia, insulin
- hypoglycemia_awareness - Recognition, frequency

**Tools:**
- diabetes_foot_assessment()
- hypoglycemia_awareness()


### 9. HEMATOLOGIC SYSTEM
Blood, coagulation, transfusion

**Assessment Subtypes:**
- anemia_assessment - Fatigue, pallor, labs
- anticoagulation - INR monitoring, bleeding risk
- transfusion_monitoring - Reactions, response
- bleeding_risk - Assessment and prevention
- clotting_disorders - DVT, PE risk

**Tools:**
- (To be implemented as needed)


### 10. IMMUNOLOGIC SYSTEM
Infection, immunity, wound healing

**Assessment Subtypes:**
- infection_assessment - Signs, symptoms, source
- infection_precautions - Isolation needs, PPE
- immunosuppression - Medication effects, protection
- wound_healing - Healing trajectory, complications
- sepsis_screening - Early warning signs

**Tools:**
- (To be implemented as needed)


### 11. PSYCHOSOCIAL SYSTEM
Mental health, cognition, social support

**Assessment Subtypes:**
- depression_screening - PHQ-9
- anxiety_screening - GAD-7
- dementia_assessment - Mini-Cog, behavior changes
- substance_abuse - Use patterns, withdrawal
- caregiver_stress - Strain index, support needs
- social_support - Resources, isolation, safety
- advance_directives - Code status, preferences

**Tools:**
- phq9_depression_screening()
- gad7_anxiety_screening()
- mini_cog()
- caregiver_strain_index()


## Usage Example

```python
from app.models.specialty_assessment import SpecialtyAssessment
from app.models.specialty_assessment import CardiovascularAssessments

# Create a heart failure assessment
chf_data = {
    'dyspnea_at_rest': False,
    'dyspnea_minimal_exertion': True,
    'peripheral_edema_grade': 2,
    'weight_gain_48hrs': 3,
    'orthopnea': True,
    'paroxysmal_nocturnal_dyspnea': False,
    'decreased_activity_tolerance': True
}

score, status = CardiovascularAssessments.calculate_chf_symptoms_score(chf_data)

# Save to database
assessment = SpecialtyAssessment(
    patient_id=123,
    assessed_by=nurse_id,
    visit_id=456,
    body_system='cardiovascular',
    assessment_subtype='heart_failure',
    assessment_data=chf_data,
    score=score,
    score_interpretation=status,
    clinical_findings='Patient showing signs of mild decompensation...',
    recommendations='Increase diuretic, daily weights, follow-up in 48 hours'
)
```

## Benefits of Systems-Based Organization

1. **Comprehensive Coverage** - All conditions fit naturally into a body system
2. **Clinical Intuition** - Nurses think in systems during assessments
3. **Flexibility** - Easy to add new assessment subtypes within existing systems
4. **Specialty Care** - Can focus on specific systems for specialty patients
5. **Education** - Training materials organize naturally by system
6. **Reporting** - Analytics can aggregate by system or condition
7. **Interdisciplinary** - Other disciplines (PT, OT, dietitian) use same framework
