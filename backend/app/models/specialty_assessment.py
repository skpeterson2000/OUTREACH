"""Systems-based assessment model for comprehensive clinical documentation."""
from datetime import datetime
from app import db
import json


class SpecialtyAssessment(db.Model):
    """Systems-based clinical assessments organized by body system."""
    
    __tablename__ = 'specialty_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    assessed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'))
    
    # Body System
    body_system = db.Column(db.String(100), nullable=False, index=True)
    # Systems: integumentary, respiratory, cardiovascular, neurological, gastrointestinal,
    #          genitourinary, musculoskeletal, endocrine, hematologic, immunologic, psychosocial
    
    # Specific Assessment Type within the system
    assessment_subtype = db.Column(db.String(100), nullable=False, index=True)
    # Examples: 
    #   integumentary: burn, wound, pressure_injury, surgical_site, skin_integrity
    #   respiratory: copd, asthma, pneumonia, oxygen_therapy, tracheostomy_care
    #   cardiovascular: heart_failure, hypertension, peripheral_vascular, dvt_assessment
    #   neurological: stroke, seizure, pain_assessment, cognitive, consciousness
    #   gastrointestinal: nutrition, swallowing, bowel_function, tube_feeding, ostomy_care
    #   genitourinary: catheter_care, bladder_function, renal_function, incontinence
    #   musculoskeletal: mobility, fall_risk, amputation_care, fracture_care
    #   endocrine: diabetes, thyroid, glucose_management
    #   hematologic: anemia, anticoagulation, transfusion
    #   immunologic: infection_precautions, wound_healing, immunosuppression
    #   psychosocial: depression, anxiety, dementia, substance_abuse, caregiver_stress
    
    # Assessment Data (JSON)
    # This stores the system-specific data in a flexible format
    assessment_data = db.Column(db.JSON, nullable=False)
    
    # Scores/Results
    score = db.Column(db.Numeric(10, 2))  # calculated score if applicable
    score_interpretation = db.Column(db.String(100))  # low, moderate, high risk, etc.
    
    # Clinical Notes
    clinical_findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    interventions_initiated = db.Column(db.Text)
    
    # Follow-up
    requires_follow_up = db.Column(db.Boolean, default=False)
    follow_up_timeframe = db.Column(db.String(100))
    physician_notification_required = db.Column(db.Boolean, default=False)
    physician_notified = db.Column(db.Boolean, default=False)
    physician_notification_date = db.Column(db.DateTime)
    
    # Timestamps
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='specialty_assessments')
    nurse = db.relationship('User')
    visit = db.relationship('Visit')
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'body_system': self.body_system,
            'assessment_subtype': self.assessment_subtype,
            'assessment_data': self.assessment_data,
            'score': float(self.score) if self.score else None,
            'score_interpretation': self.score_interpretation,
            'clinical_findings': self.clinical_findings,
            'recommendations': self.recommendations,
            'assessment_date': self.assessment_date.isoformat(),
            'assessed_by': self.assessed_by,
            'requires_follow_up': self.requires_follow_up
        }
    
    def __repr__(self):
        return f'<SpecialtyAssessment {self.body_system}/{self.assessment_subtype} for patient {self.patient_id}>'


# =============================================================================
# INTEGUMENTARY SYSTEM ASSESSMENTS
# =============================================================================

class IntegumentaryAssessments:
    """Assessment tools for skin, burns, wounds, and related conditions."""
    
    @staticmethod
    def calculate_tbsa_adults(affected_areas):
        """
        Calculate Total Body Surface Area (TBSA) using Rule of Nines for adults.
        
        affected_areas: dict like {
            'head': 9, 'chest': 9, 'abdomen': 9, 'back_upper': 9, 
            'back_lower': 9, 'arm_left': 9, 'arm_right': 9,
            'leg_left': 18, 'leg_right': 18, 'perineum': 1
        }
        """
        return sum(affected_areas.values())
    
    @staticmethod
    def calculate_tbsa_pediatric(age_months, affected_areas):
        """
        Calculate TBSA for pediatric patients using age-adjusted percentages.
        Uses modified rule accounting for larger head and smaller legs in children.
        """
        # Simplified - in practice would use more detailed age-adjusted percentages
        if age_months < 12:
            # Infant: Head ~18%, legs ~14% each
            return sum(affected_areas.values())
        elif age_months < 60:
            # Toddler: Head ~15%, legs ~15% each
            return sum(affected_areas.values())
        else:
            # Child: approaching adult proportions
            return sum(affected_areas.values())
    
    @staticmethod
    def classify_burn_severity(tbsa, has_inhalation_injury, has_circumferential, depth):
        """
        Classify burn severity.
        
        Returns: minor, moderate, major
        """
        if depth in ['full_thickness', 'fourth_degree'] or has_inhalation_injury:
            return 'major'
        elif tbsa > 20 or has_circumferential:
            return 'major'
        elif tbsa > 10:
            return 'moderate'
        else:
            return 'minor'
    
    @staticmethod
    def calculate_braden_scale(data):
        """
        Calculate Braden Scale for pressure injury risk.
        
        Each category scored 1-4 (lower = higher risk):
        - Sensory perception, Moisture, Activity, Mobility, Nutrition, Friction/Shear
        Total: 6-23 (≤18 = at risk)
        """
        score = 0
        score += data.get('sensory_perception', 1)
        score += data.get('moisture', 1)
        score += data.get('activity', 1)
        score += data.get('mobility', 1)
        score += data.get('nutrition', 1)
        score += data.get('friction_shear', 1)
        
        if score <= 12:
            risk = 'high'
        elif score <= 14:
            risk = 'moderate'
        elif score <= 18:
            risk = 'mild'
        else:
            risk = 'no_risk'
        
        return score, risk


# =============================================================================
# RESPIRATORY SYSTEM ASSESSMENTS
# =============================================================================

class RespiratoryAssessments:


class RespiratoryAssessments:
    """Assessment tools for respiratory conditions and breathing function."""
    
    @staticmethod
    def calculate_respiratory_distress_score(data):
        """
        Calculate respiratory distress score.
        
        data: dict with respiratory_rate, oxygen_saturation, accessory_muscle_use, etc.
        """
        score = 0
        
        rr = data.get('respiratory_rate', 0)
        if rr > 24 or rr < 12:
            score += 2
        elif rr > 20 or rr < 14:
            score += 1
            
        spo2 = data.get('oxygen_saturation', 100)
        if spo2 < 88:
            score += 3
        elif spo2 < 92:
            score += 2
        elif spo2 < 95:
            score += 1
        
        if data.get('accessory_muscle_use', False):
            score += 2
        if data.get('nasal_flaring', False):
            score += 1
        if data.get('wheezing', False):
            score += 1
        if data.get('rhonchi', False):
            score += 1
        
        if score >= 7:
            severity = 'severe'
        elif score >= 4:
            severity = 'moderate'
        elif score >= 2:
            severity = 'mild'
        else:
            severity = 'normal'
            
        return score, severity
    
    @staticmethod
    def copd_assessment_test(data):
        """
        COPD Assessment Test (CAT) - 8 questions, 0-5 points each.
        Total: 0-40 (higher = more impact)
        """
        total = sum([
            data.get('cough', 0),
            data.get('phlegm', 0),
            data.get('chest_tightness', 0),
            data.get('breathlessness_hills', 0),
            data.get('activity_limitation', 0),
            data.get('confidence_leaving_home', 0),
            data.get('sleep_quality', 0),
            data.get('energy_level', 0)
        ])
        
        if total < 10:
            impact = 'low'
        elif total < 20:
            impact = 'medium'
        elif total < 30:
            impact = 'high'
        else:
            impact = 'very_high'
        
        return total, impact


# =============================================================================
# CARDIOVASCULAR SYSTEM ASSESSMENTS
# =============================================================================

class CardiovascularAssessments:
    """Assessment tools for heart, circulation, and vascular conditions."""
    
    @staticmethod
    def calculate_chf_symptoms_score(data):
        """
        Heart Failure symptom assessment.
        Tracks fluid retention, dyspnea, activity tolerance.
        """
        score = 0
        
        # Dyspnea
        if data.get('dyspnea_at_rest', False):
            score += 3
        elif data.get('dyspnea_minimal_exertion', False):
            score += 2
        elif data.get('dyspnea_moderate_exertion', False):
            score += 1
        
        # Edema
        edema = data.get('peripheral_edema_grade', 0)  # 0-4+
        score += edema
        
        # Weight gain
        weight_gain_lbs = data.get('weight_gain_48hrs', 0)
        if weight_gain_lbs >= 5:
            score += 3
        elif weight_gain_lbs >= 3:
            score += 2
        elif weight_gain_lbs >= 2:
            score += 1
        
        # Other symptoms
        if data.get('orthopnea', False):
            score += 2
        if data.get('paroxysmal_nocturnal_dyspnea', False):
            score += 2
        if data.get('decreased_activity_tolerance', False):
            score += 1
        
        if score >= 10:
            status = 'severe_decompensation'
        elif score >= 6:
            status = 'moderate_decompensation'
        elif score >= 3:
            status = 'mild_decompensation'
        else:
            status = 'stable'
        
        return score, status
    
    @staticmethod
    def assess_peripheral_vascular(data):
        """
        Peripheral vascular assessment for arterial/venous insufficiency.
        """
        findings = {
            'arterial_insufficiency_indicators': [],
            'venous_insufficiency_indicators': []
        }
        
        # Arterial insufficiency signs
        if data.get('absent_pulses', False):
            findings['arterial_insufficiency_indicators'].append('absent_pulses')
        if data.get('skin_cool_to_touch', False):
            findings['arterial_insufficiency_indicators'].append('cool_skin')
        if data.get('delayed_capillary_refill', False):
            findings['arterial_insufficiency_indicators'].append('delayed_cap_refill')
        if data.get('claudication', False):
            findings['arterial_insufficiency_indicators'].append('claudication')
        if data.get('skin_shiny_hairless', False):
            findings['arterial_insufficiency_indicators'].append('trophic_changes')
        
        # Venous insufficiency signs
        if data.get('edema_lower_extremities', False):
            findings['venous_insufficiency_indicators'].append('edema')
        if data.get('hemosiderin_staining', False):
            findings['venous_insufficiency_indicators'].append('hemosiderin_staining')
        if data.get('varicose_veins', False):
            findings['venous_insufficiency_indicators'].append('varicose_veins')
        if data.get('skin_thickened', False):
            findings['venous_insufficiency_indicators'].append('lipodermatosclerosis')
        
        return findings


# =============================================================================
# NEUROLOGICAL SYSTEM ASSESSMENTS
# =============================================================================

class NeurologicalAssessments:
    """Assessment tools for neurological function, cognition, and pain."""
    
    @staticmethod
    def glasgow_coma_scale(data):
        """
        Glasgow Coma Scale (GCS).
        Eye opening (1-4) + Verbal response (1-5) + Motor response (1-6)
        Total: 3-15 (lower = worse)
        """
        eye = data.get('eye_opening', 1)
        verbal = data.get('verbal_response', 1)
        motor = data.get('motor_response', 1)
        
        total = eye + verbal + motor
        
        if total <= 8:
            severity = 'severe'
        elif total <= 12:
            severity = 'moderate'
        else:
            severity = 'mild'
        
        return total, severity
    
    @staticmethod
    def stroke_assessment_nihss_simplified(data):
        """
        Simplified NIH Stroke Scale indicators.
        Tracks key stroke symptoms.
        """
        findings = []
        
        if data.get('facial_droop', False):
            findings.append('facial_weakness')
        if data.get('arm_drift', False):
            findings.append('arm_weakness')
        if data.get('leg_drift', False):
            findings.append('leg_weakness')
        if data.get('slurred_speech', False):
            findings.append('dysarthria')
        if data.get('aphasia', False):
            findings.append('language_deficit')
        if data.get('visual_field_deficit', False):
            findings.append('visual_deficit')
        if data.get('gaze_deviation', False):
            findings.append('gaze_abnormality')
        if data.get('ataxia', False):
            findings.append('coordination_deficit')
        if data.get('sensory_loss', False):
            findings.append('sensory_deficit')
        
        return findings
    
    @staticmethod
    def pain_assessment_comprehensive(data):
        """
        Comprehensive pain assessment.
        Returns structured pain data.
        """
        assessment = {
            'intensity': data.get('pain_scale_0_10', 0),
            'location': data.get('pain_location', []),
            'quality': data.get('pain_quality', []),  # sharp, dull, burning, aching, etc.
            'onset': data.get('onset', ''),
            'duration': data.get('duration', ''),
            'aggravating_factors': data.get('aggravating_factors', []),
            'relieving_factors': data.get('relieving_factors', []),
            'radiation': data.get('radiation', False),
            'associated_symptoms': data.get('associated_symptoms', [])
        }
        
        return assessment


# =============================================================================
# GASTROINTESTINAL SYSTEM ASSESSMENTS
# =============================================================================

class GastrointestinalAssessments:
    """Assessment tools for nutrition, digestion, and GI function."""
    
    @staticmethod
    def calculate_bmi(weight_kg, height_cm):
        """Calculate Body Mass Index."""
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
    
    @staticmethod
    def classify_bmi(bmi):
        """Classify BMI category."""
        if bmi < 18.5:
            return 'underweight'
        elif bmi < 25:
            return 'normal'
        elif bmi < 30:
            return 'overweight'
        elif bmi < 35:
            return 'obese_class_1'
        elif bmi < 40:
            return 'obese_class_2'
        else:
            return 'obese_class_3'
    
    @staticmethod
    def malnutrition_screening_tool(data):
        """
        Mini Nutritional Assessment Short Form.
        Screens for malnutrition risk.
        """
        score = 0
        
        # Food intake decline
        score += data.get('food_intake_decline', 0)  # 0-2 points
        
        # Weight loss
        score += data.get('weight_loss_score', 0)  # 0-3 points
        
        # Mobility
        score += data.get('mobility_score', 0)  # 0-2 points
        
        # Psychological stress
        score += data.get('psychological_stress', 0)  # 0-2 points
        
        # Neuropsychological problems
        score += data.get('neuropsych_problems', 0)  # 0-2 points
        
        # BMI score
        bmi = data.get('bmi', 0)
        if bmi < 19:
            score += 0
        elif bmi < 21:
            score += 1
        elif bmi < 23:
            score += 2
        else:
            score += 3
        
        if score >= 12:
            status = 'normal_nutritional_status'
        elif score >= 8:
            status = 'at_risk_malnutrition'
        else:
            status = 'malnourished'
        
        return score, status
    
    @staticmethod
    def swallowing_assessment(data):
        """
        Dysphagia screening.
        """
        concerns = []
        
        if data.get('coughing_during_meals', False):
            concerns.append('coughing_choking')
        if data.get('wet_voice_after_swallow', False):
            concerns.append('wet_voice')
        if data.get('pocketing_food', False):
            concerns.append('pocketing')
        if data.get('prolonged_meal_time', False):
            concerns.append('slow_eating')
        if data.get('difficulty_specific_textures', False):
            concerns.append('texture_difficulty')
        if data.get('weight_loss', False):
            concerns.append('weight_loss')
        if data.get('recurrent_pneumonia', False):
            concerns.append('aspiration_risk')
        
        if len(concerns) >= 3:
            risk = 'high'
        elif len(concerns) >= 1:
            risk = 'moderate'
        else:
            risk = 'low'
        
        return concerns, risk


# =============================================================================
# GENITOURINARY SYSTEM ASSESSMENTS
# =============================================================================

class GenitourinaryAssessments:
    """Assessment tools for bladder, kidney, and urinary function."""
    
    @staticmethod
    def bladder_function_assessment(data):
        """
        Assess bladder function and continence.
        """
        assessment = {
            'voiding_frequency': data.get('voids_per_24hrs', 0),
            'nocturia': data.get('nighttime_voids', 0),
            'urgency': data.get('urgency_present', False),
            'incontinence_type': data.get('incontinence_type', 'none'),  # stress, urge, overflow, functional
            'catheter_present': data.get('catheter_present', False),
            'catheter_type': data.get('catheter_type', None),
            'urine_characteristics': data.get('urine_characteristics', {}),
            'hydration_status': data.get('hydration_status', 'adequate')
        }
        
        return assessment


# =============================================================================
# MUSCULOSKELETAL SYSTEM ASSESSMENTS
# =============================================================================

class MusculoskeletalAssessments:
    """Assessment tools for mobility, fall risk, and musculoskeletal function."""
    
    @staticmethod
    def morse_fall_scale(data):


class MusculoskeletalAssessments:
    """Assessment tools for mobility, fall risk, and musculoskeletal function."""
    
    @staticmethod
    def morse_fall_scale(data):
        """
        Calculate Morse Fall Scale score.
        
        Returns score and risk level.
        """
        score = 0
        
        # History of falling
        if data.get('history_of_falling') == 'yes':
            score += 25
        
        # Secondary diagnosis
        if data.get('secondary_diagnosis', False):
            score += 15
        
        # Ambulatory aid
        aid = data.get('ambulatory_aid', 'none')
        if aid in ['walker', 'crutches', 'cane']:
            score += 15
        elif aid in ['furniture', 'walls']:
            score += 30
        
        # IV therapy
        if data.get('iv_therapy', False):
            score += 20
        
        # Gait
        gait = data.get('gait', 'normal')
        if gait == 'weak':
            score += 10
        elif gait == 'impaired':
            score += 20
        
        # Mental status
        if data.get('mental_status', 'oriented') == 'forgets_limitations':
            score += 15
        
        # Risk level
        if score < 25:
            risk = 'low'
        elif score < 45:
            risk = 'moderate'
        else:
            risk = 'high'
        
        return score, risk
    
    @staticmethod
    def timed_up_and_go(seconds):
        """
        Timed Up and Go test for mobility and fall risk.
        Patient stands from chair, walks 3 meters, turns, returns, sits.
        """
        if seconds < 10:
            interpretation = 'normal_mobility'
        elif seconds < 20:
            interpretation = 'good_mobility_mostly_independent'
        elif seconds < 30:
            interpretation = 'mobility_problems_some_assistance'
        else:
            interpretation = 'significant_mobility_impairment'
        
        return interpretation
    
    @staticmethod
    def barthel_index(data):
        """
        Barthel Index for Activities of Daily Living.
        Measures functional independence.
        Scores: feeding, bathing, grooming, dressing, bowels, bladder,
                toilet use, transfers, mobility, stairs
        Total: 0-100 (higher = more independent)
        """
        total = sum([
            data.get('feeding', 0),
            data.get('bathing', 0),
            data.get('grooming', 0),
            data.get('dressing', 0),
            data.get('bowel_control', 0),
            data.get('bladder_control', 0),
            data.get('toilet_use', 0),
            data.get('transfers', 0),
            data.get('mobility', 0),
            data.get('stairs', 0)
        ])
        
        if total >= 80:
            dependency = 'independent'
        elif total >= 60:
            dependency = 'minimally_dependent'
        elif total >= 40:
            dependency = 'partially_dependent'
        elif total >= 20:
            dependency = 'very_dependent'
        else:
            dependency = 'totally_dependent'
        
        return total, dependency


# =============================================================================
# ENDOCRINE SYSTEM ASSESSMENTS
# =============================================================================

class EndocrineAssessments:
    """Assessment tools for diabetes, thyroid, and metabolic conditions."""
    
    @staticmethod
    def diabetes_foot_assessment(data):
        """
        Comprehensive diabetic foot assessment.
        """
        findings = {
            'sensation': data.get('monofilament_test', 'intact'),
            'pulses': data.get('pedal_pulses', 'present_bilateral'),
            'skin_integrity': data.get('skin_integrity', 'intact'),
            'deformities': data.get('foot_deformities', []),
            'nails': data.get('nail_condition', 'normal'),
            'footwear': data.get('appropriate_footwear', True)
        }
        
        risk_factors = []
        if findings['sensation'] == 'diminished':
            risk_factors.append('neuropathy')
        if findings['pulses'] in ['diminished', 'absent']:
            risk_factors.append('peripheral_vascular_disease')
        if findings['skin_integrity'] != 'intact':
            risk_factors.append('active_wound')
        if findings['deformities']:
            risk_factors.append('structural_deformity')
        
        if len(risk_factors) >= 3:
            risk = 'high'
        elif len(risk_factors) >= 1:
            risk = 'moderate'
        else:
            risk = 'low'
        
        return findings, risk_factors, risk
    
    @staticmethod
    def hypoglycemia_awareness(data):
        """
        Assess hypoglycemia awareness and frequency.
        """
        assessment = {
            'episodes_past_week': data.get('episodes_past_week', 0),
            'recognizes_symptoms': data.get('recognizes_symptoms', True),
            'typical_symptoms': data.get('symptoms', []),
            'severe_episodes_past_year': data.get('severe_episodes_year', 0)
        }
        
        if not assessment['recognizes_symptoms']:
            awareness = 'impaired_awareness'
        elif assessment['episodes_past_week'] > 2:
            awareness = 'frequent_episodes'
        elif assessment['severe_episodes_past_year'] > 0:
            awareness = 'history_severe_episodes'
        else:
            awareness = 'good_awareness'
        
        return assessment, awareness


# =============================================================================
# PSYCHOSOCIAL ASSESSMENTS
# =============================================================================

class PsychosocialAssessments:
    """Assessment tools for mental health, cognition, and social support."""
    
    @staticmethod
    def phq9_depression_screening(data):
        """
        PHQ-9 Depression Screening.
        9 items, each scored 0-3.
        Total: 0-27
        """
        total = sum([
            data.get('little_interest', 0),
            data.get('feeling_down', 0),
            data.get('sleep_problems', 0),
            data.get('tired_no_energy', 0),
            data.get('appetite_changes', 0),
            data.get('feeling_bad_about_self', 0),
            data.get('trouble_concentrating', 0),
            data.get('moving_slowly_or_restless', 0),
            data.get('thoughts_of_death', 0)
        ])
        
        if total < 5:
            severity = 'none_minimal'
        elif total < 10:
            severity = 'mild'
        elif total < 15:
            severity = 'moderate'
        elif total < 20:
            severity = 'moderately_severe'
        else:
            severity = 'severe'
        
        return total, severity
    
    @staticmethod
    def gad7_anxiety_screening(data):
        """
        GAD-7 Anxiety Screening.
        7 items, each scored 0-3.
        Total: 0-21
        """
        total = sum([
            data.get('feeling_nervous', 0),
            data.get('cant_stop_worrying', 0),
            data.get('worrying_too_much', 0),
            data.get('trouble_relaxing', 0),
            data.get('restless', 0),
            data.get('easily_annoyed', 0),
            data.get('feeling_afraid', 0)
        ])
        
        if total < 5:
            severity = 'minimal'
        elif total < 10:
            severity = 'mild'
        elif total < 15:
            severity = 'moderate'
        else:
            severity = 'severe'
        
        return total, severity
    
    @staticmethod
    def mini_cog(data):
        """
        Mini-Cog for dementia screening.
        3-word recall (0-3) + Clock drawing (0-2)
        Total: 0-5 (0-2 = likely dementia)
        """
        recall_score = data.get('word_recall_count', 0)  # 0-3
        clock_score = data.get('clock_drawing_score', 0)  # 0=abnormal, 2=normal
        
        total = recall_score + clock_score
        
        if total <= 2:
            result = 'positive_screen'
        else:
            result = 'negative_screen'
        
        return total, result
    
    @staticmethod
    def caregiver_strain_index(data):
        """
        Modified Caregiver Strain Index.
        13 yes/no items. Score ≥7 indicates high strain.
        """
        strain_items = [
            data.get('sleep_disturbed', False),
            data.get('inconvenient', False),
            data.get('physical_strain', False),
            data.get('confining', False),
            data.get('family_adjustments', False),
            data.get('changes_in_plans', False),
            data.get('other_demands', False),
            data.get('emotional_adjustments', False),
            data.get('upsetting_behavior', False),
            data.get('behavioral_changes', False),
            data.get('work_adjustments', False),
            data.get('financial_strain', False),
            data.get('overwhelming', False)
        ]
        
        score = sum(strain_items)
        
        if score >= 7:
            strain_level = 'high'
        else:
            strain_level = 'low_to_moderate'
        
        return score, strain_level
