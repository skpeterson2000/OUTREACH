"""
ADR Surveillance Service - Active monitoring for adverse drug reactions.

This service continuously monitors patient observations and correlates them
with known adverse reactions for currently prescribed medications.
"""
from datetime import datetime, timedelta
from app import db
from app.models import (
    Patient, Medication, PatientObservation, ADRAlert,
    MedicationAdverseReaction, PharmacistIntervention, ADRSurveillanceLog
)
from sqlalchemy import and_, or_


class ADRSurveillanceService:
    """
    Service for detecting potential adverse drug reactions through active surveillance.
    """
    
    @staticmethod
    def analyze_observation(observation_id):
        """
        Analyze a single observation for potential ADRs.
        
        Called when new observation is created (real-time surveillance).
        Returns list of generated alerts.
        """
        observation = PatientObservation.query.get(observation_id)
        if not observation:
            return []
        
        # Mark surveillance as performed
        observation.adr_surveillance_performed = True
        
        # Get patient's current active medications
        active_medications = Medication.query.filter_by(
            patient_id=observation.patient_id,
            status='active'
        ).all()
        
        if not active_medications:
            db.session.commit()
            return []
        
        alerts = []
        
        # Check each medication for potential ADRs
        for medication in active_medications:
            # Find known ADRs for this medication (by name, generic, or class)
            known_adrs = MedicationAdverseReaction.query.filter(
                or_(
                    MedicationAdverseReaction.medication_name.ilike(f'%{medication.name}%'),
                    MedicationAdverseReaction.generic_name.ilike(f'%{medication.generic_name}%') if medication.generic_name else False,
                    MedicationAdverseReaction.drug_class == medication.drug_class if medication.drug_class else False
                )
            ).all()
            
            # Analyze each known ADR for correlation
            for known_adr in known_adrs:
                alert = ADRSurveillanceService._evaluate_correlation(
                    observation, medication, known_adr
                )
                
                if alert:
                    alerts.append(alert)
        
        # Update observation flag if any alerts generated
        if alerts:
            observation.potential_adr_detected = True
        
        db.session.commit()
        return alerts
    
    @staticmethod
    def _evaluate_correlation(observation, medication, known_adr):
        """
        Evaluate correlation between observation and known ADR.
        Returns ADRAlert if correlation found, None otherwise.
        """
        matching_symptoms = []
        matching_vital_signs = []
        matching_behaviors = []
        correlation_score = 0.0
        max_score = 0.0
        
        # Check symptom matches
        if observation.standardized_terms and known_adr.observable_symptoms:
            obs_terms = set(term.lower() for term in observation.standardized_terms)
            adr_symptoms = set(symptom.lower() for symptom in known_adr.observable_symptoms)
            matches = obs_terms.intersection(adr_symptoms)
            
            if matches:
                matching_symptoms = list(matches)
                correlation_score += len(matches) * 3.0  # Weight symptoms heavily
                max_score += len(adr_symptoms) * 3.0
        
        # Check vital sign changes
        if observation.related_vital_signs and known_adr.vital_sign_changes:
            for vs_name, expected_change in known_adr.vital_sign_changes.items():
                if vs_name in observation.related_vital_signs:
                    # Simple string matching for now (could be enhanced with thresholds)
                    if expected_change.lower() in str(observation.related_vital_signs.get(vs_name, '')).lower():
                        matching_vital_signs.append(vs_name)
                        correlation_score += 2.0
                max_score += 2.0
        
        # Check behavioral changes
        if observation.observation_type == 'BEHAVIOR' and known_adr.behavioral_changes:
            obs_text_lower = observation.observation_text.lower()
            for behavior in known_adr.behavioral_changes:
                if behavior.lower() in obs_text_lower:
                    matching_behaviors.append(behavior)
                    correlation_score += 2.0
                    max_score += 2.0
        
        # Calculate final correlation score (0.0 - 1.0)
        if max_score > 0:
            correlation_score = min(correlation_score / max_score, 1.0)
        
        # Determine if correlation is strong enough to generate alert
        # Require at least 1 symptom match OR 2+ vital sign/behavior matches
        if not matching_symptoms and len(matching_vital_signs) + len(matching_behaviors) < 2:
            return None
        
        # Calculate confidence level based on correlation
        if correlation_score >= 0.75:
            confidence = ADRAlert.CONFIDENCE_VERY_HIGH
        elif correlation_score >= 0.5:
            confidence = ADRAlert.CONFIDENCE_HIGH
        elif correlation_score >= 0.3:
            confidence = ADRAlert.CONFIDENCE_MODERATE
        else:
            confidence = ADRAlert.CONFIDENCE_LOW
        
        # Check timing - does onset match expected timeline?
        expected_onset_match = False
        days_since_start = None
        
        if medication.start_date:
            days_since_start = (observation.observation_datetime.date() - medication.start_date).days
            
            # Check if within expected onset window
            if known_adr.typical_onset_days:
                # Allow 50% margin on either side
                margin = max(known_adr.typical_onset_days * 0.5, 2)
                if abs(days_since_start - known_adr.typical_onset_days) <= margin:
                    expected_onset_match = True
                    correlation_score = min(correlation_score + 0.1, 1.0)  # Boost confidence
            elif known_adr.typical_onset_hours:
                hours_since_start = days_since_start * 24
                margin = max(known_adr.typical_onset_hours * 0.5, 12)
                if abs(hours_since_start - known_adr.typical_onset_hours) <= margin:
                    expected_onset_match = True
                    correlation_score = min(correlation_score + 0.1, 1.0)
        
        # Check patient risk factors
        patient_risk_factors = []
        if known_adr.risk_factors:
            # This would check patient demographics, conditions, other meds
            # Simplified for now - would integrate with patient assessment data
            patient = observation.patient
            if 'elderly' in known_adr.risk_factors and patient.age >= 65:
                patient_risk_factors.append('elderly')
                correlation_score = min(correlation_score + 0.05, 1.0)
        
        # Check if patient is hospice - modifies alert approach
        patient = observation.patient
        is_hospice = patient.is_hospice or patient.comfort_measures_only
        
        # Determine notification urgency based on severity, correlation, and goals of care
        if is_hospice:
            # For hospice patients, focus on comfort/symptom management
            # Never STAT unless directly impacting comfort
            if known_adr.severity == MedicationAdverseReaction.SEVERITY_LIFE_THREATENING and correlation_score >= 0.5:
                # Still urgent but frame as comfort/symptom management
                notification_urgency = 'URGENT'
                requires_immediate_action = True  # But will suggest comfort measures, not 911
            elif known_adr.severity in [MedicationAdverseReaction.SEVERITY_MAJOR, MedicationAdverseReaction.SEVERITY_MODERATE]:
                notification_urgency = 'URGENT' if correlation_score >= 0.6 else 'ROUTINE'
                requires_immediate_action = False
            else:
                notification_urgency = 'ROUTINE'
                requires_immediate_action = False
        else:
            # Standard urgency determination for non-hospice patients
            if known_adr.severity == MedicationAdverseReaction.SEVERITY_LIFE_THREATENING and correlation_score >= 0.5:
                notification_urgency = 'STAT'
                requires_immediate_action = True
            elif known_adr.severity == MedicationAdverseReaction.SEVERITY_MAJOR and correlation_score >= 0.6:
                notification_urgency = 'URGENT'
                requires_immediate_action = True
            elif known_adr.severity in [MedicationAdverseReaction.SEVERITY_MODERATE, MedicationAdverseReaction.SEVERITY_MAJOR]:
                notification_urgency = 'URGENT'
                requires_immediate_action = False
            else:
                notification_urgency = 'ROUTINE'
                requires_immediate_action = False
        
        # Separate nursing actions from provider orders
        nursing_actions = ADRSurveillanceService._extract_nursing_interventions(known_adr.nursing_interventions or [])
        provider_orders = ADRSurveillanceService._extract_provider_orders(known_adr.nursing_interventions or [])
        
        # Generate hospice-specific comfort guidance if applicable
        hospice_comfort_guidance = None
        if is_hospice:
            hospice_comfort_guidance = ADRSurveillanceService._generate_hospice_comfort_guidance(
                known_adr, matching_symptoms
            )
        
        # Generate alert summary
        alert_summary = ADRSurveillanceService._generate_alert_summary(
            observation, medication, known_adr, 
            matching_symptoms, matching_vital_signs, matching_behaviors
        )
        
        # Create the alert
        alert = ADRAlert(
            patient_id=observation.patient_id,
            facility_id=observation.facility_id,
            medication_id=medication.id,
            observation_id=observation.id,
            known_adr_id=known_adr.id,
            suspected_reaction=known_adr.reaction_name,
            alert_summary=alert_summary,
            confidence_level=confidence,
            severity=known_adr.severity,
            matching_symptoms=matching_symptoms,
            matching_vital_signs=matching_vital_signs,
            matching_behaviors=matching_behaviors,
            correlation_score=correlation_score,
            medication_start_date=medication.start_date,
            days_since_medication_start=days_since_start,
            expected_onset_match=expected_onset_match,
            patient_risk_factors=patient_risk_factors,
            nursing_interventions=nursing_actions,
            provider_notification_needed=True,
            provider_notification_urgency=notification_urgency,
            provider_notification_guidance=known_adr.provider_notification_guidance,
            suggested_provider_orders=provider_orders,
            requires_immediate_action=requires_immediate_action,
            escalation_guidance=known_adr.when_to_escalate,
            is_hospice_patient=is_hospice,
            hospice_comfort_focus=hospice_comfort_guidance
        )
        
        db.session.add(alert)
        return alert
    
    @staticmethod
    def _generate_alert_summary(observation, medication, known_adr, 
                               matching_symptoms, matching_vital_signs, matching_behaviors):
        """Generate human-readable alert summary."""
        summary_parts = []
        
        patient = observation.patient
        is_hospice = patient.is_hospice or patient.comfort_measures_only
        
        # Tailor alert header based on goals of care
        if is_hospice:
            summary_parts.append(
                f"💙 HOSPICE PATIENT - Comfort-Focused Care\n⚠️ Potential adverse reaction to {medication.name}: {known_adr.reaction_name}"
            )
            summary_parts.append(
                "⚕️ Focus: Symptom management and comfort measures per hospice goals"
            )
        else:
            summary_parts.append(
                f"⚠️ Potential adverse reaction to {medication.name}: {known_adr.reaction_name}"
            )
        
        if matching_symptoms:
            summary_parts.append(
                f"Patient experiencing: {', '.join(matching_symptoms)}"
            )
        
        if matching_vital_signs:
            summary_parts.append(
                f"Vital sign changes: {', '.join(matching_vital_signs)}"
            )
        
        if matching_behaviors:
            summary_parts.append(
                f"Behavioral changes: {', '.join(matching_behaviors)}"
            )
        
        summary_parts.append(
            f"Severity: {known_adr.severity} | Likelihood: {known_adr.likelihood or 'Unknown'}"
        )
        
        if is_hospice:
            summary_parts.append(
                "🏥 Do Not Hospitalize - Per advance directives"
            )
            if patient.hospice_agency:
                summary_parts.append(
                    f"Hospice Agency: {patient.hospice_agency}"
                )
                if patient.hospice_nurse_phone:
                    summary_parts.append(
                        f"Hospice Nurse: {patient.hospice_nurse_name or 'On-call'} - {patient.hospice_nurse_phone}"
                    )
        
        if known_adr.monitoring_recommendations:
            summary_parts.append(
                f"Monitor for: {known_adr.monitoring_recommendations}"
            )
        
        return "\n\n".join(summary_parts)
    
    @staticmethod
    def batch_surveillance(facility_id=None, hours_lookback=24):
        """
        Run batch surveillance for recent observations.
        
        Useful for catching anything missed by real-time surveillance,
        or for periodic review of all patients.
        """
        start_time = datetime.utcnow()
        
        # Get recent observations that haven't been analyzed
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_lookback)
        
        query = PatientObservation.query.filter(
            PatientObservation.created_at >= cutoff_time,
            PatientObservation.adr_surveillance_performed == False
        )
        
        if facility_id:
            query = query.filter(PatientObservation.facility_id == facility_id)
        
        observations = query.all()
        
        total_alerts = 0
        high_severity_count = 0
        immediate_action_count = 0
        
        for observation in observations:
            alerts = ADRSurveillanceService.analyze_observation(observation.id)
            total_alerts += len(alerts)
            
            for alert in alerts:
                if alert.severity in ['MAJOR', 'LIFE_THREATENING']:
                    high_severity_count += 1
                if alert.requires_immediate_action:
                    immediate_action_count += 1
        
        # Log the surveillance run
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        log = ADRSurveillanceLog(
            run_type='BATCH',
            patients_screened=len(set(obs.patient_id for obs in observations)),
            observations_analyzed=len(observations),
            alerts_generated=total_alerts,
            execution_time_seconds=execution_time,
            high_severity_alerts=high_severity_count,
            immediate_action_alerts=immediate_action_count
        )
        db.session.add(log)
        db.session.commit()
        
        return {
            'observations_analyzed': len(observations),
            'alerts_generated': total_alerts,
            'high_severity_alerts': high_severity_count,
            'immediate_action_alerts': immediate_action_count,
            'execution_time_seconds': round(execution_time, 2)
        }
    
    @staticmethod
    def _generate_hospice_comfort_guidance(known_adr, matching_symptoms):
        """
        Generate hospice-appropriate comfort-focused guidance.
        
        Reframes interventions around symptom management and quality of life,
        NOT curative treatment or aggressive measures.
        """
        guidance_parts = []
        
        # Map symptoms to comfort measures
        comfort_measures = {
            'nausea': [
                'Small, frequent sips of clear fluids',
                'Anti-nausea medication as ordered (Zofran, Compazine)',
                'Cool cloth to forehead',
                'Quiet, calm environment',
                'Avoid strong odors'
            ],
            'vomiting': [
                'Position on side to prevent aspiration',
                'Oral care after episodes',
                'Anti-emetic medication as ordered',
                'Small ice chips if tolerated'
            ],
            'pain': [
                'Pain medication as ordered - do not delay',
                'Comfort positioning',
                'Massage or gentle touch if desired',
                'Quiet, dimmed environment',
                'Music or spiritual support if patient desires'
            ],
            'dyspnea': [
                'Elevate head of bed',
                'Fan directed toward face',
                'Oxygen for comfort (not to prolong life)',
                'Morphine for air hunger as ordered',
                'Calm, reassuring presence'
            ],
            'agitation': [
                'Calm, soothing environment',
                'Familiar voices, music, or items',
                'Anti-anxiety medication as ordered',
                'Gentle reorientation',
                'Family/spiritual support presence'
            ],
            'confusion': [
                'Do not force reorientation if distressing',
                'Provide reassurance and comfort',
                'Ensure safety (bed alarm, supervision)',
                'Consider medication review for delirium',
                'Allow family to stay at bedside'
            ]
        }
        
        guidance_parts.append("═══════════════════════════════════════")
        guidance_parts.append("💙 HOSPICE COMFORT MEASURES:")
        guidance_parts.append("═══════════════════════════════════════")
        guidance_parts.append("Focus: Symptom relief and quality of life\n")
        
        # Add symptom-specific comfort measures
        for symptom in matching_symptoms:
            symptom_lower = symptom.lower()
            for key, measures in comfort_measures.items():
                if key in symptom_lower:
                    guidance_parts.append(f"For {symptom}:")
                    for measure in measures:
                        guidance_parts.append(f"  • {measure}")
                    guidance_parts.append("")
        
        # General hospice guidance
        guidance_parts.append("General Hospice Considerations:")
        guidance_parts.append("  • Prioritize comfort over labs/tests")
        guidance_parts.append("  • Medication changes should enhance quality of life")
        guidance_parts.append("  • Coordinate with hospice nurse before changes")
        guidance_parts.append("  • Keep family informed and involved in decisions")
        guidance_parts.append("  • Document interventions and patient response")
        
        guidance_parts.append("\n═══════════════════════════════════════")
        guidance_parts.append("📞 COORDINATE WITH HOSPICE TEAM:")
        guidance_parts.append("═══════════════════════════════════════")
        guidance_parts.append("  • Contact hospice nurse for medication adjustments")
        guidance_parts.append("  • Hospice can provide additional comfort meds")
        guidance_parts.append("  • Do NOT call 911 unless specifically requested by family")
        guidance_parts.append("  • Do NOT transfer to hospital - per advance directives")
        
        return "\n".join(guidance_parts)
    
    @staticmethod
    def _extract_nursing_interventions(intervention_list):
        """
        Extract interventions within nursing scope of practice.
        
        Nursing scope: Assess, monitor, notify, document, comfort measures.
        NOT in scope: Order labs, change medications, diagnose.
        """
        nursing_keywords = [
            'assess', 'monitor', 'check', 'observe', 'document', 'notify',
            'measure', 'evaluate', 'report', 'increase frequency', 'watch for',
            'comfort', 'position', 'encourage', 'assist', 'ensure', 'review'
        ]
        
        nursing_actions = []
        for intervention in intervention_list:
            intervention_lower = intervention.lower()
            # Check if intervention is within nursing scope
            if any(keyword in intervention_lower for keyword in nursing_keywords):
                nursing_actions.append(intervention)
            # Explicitly exclude ordering actions
            elif not any(word in intervention_lower for word in ['order', 'prescribe', 'change dose', 'start medication', 'stop medication']):
                nursing_actions.append(intervention)
        
        return nursing_actions
    
    @staticmethod
    def _extract_provider_orders(intervention_list):
        """
        Extract actions that require provider orders.
        
        Provider scope: Order labs, change medications, order diagnostics.
        """
        provider_keywords = [
            'order', 'lab', 'test', 'x-ray', 'imaging', 'prescribe',
            'change dose', 'adjust', 'discontinue', 'start', 'add medication',
            'consult', 'refer', 'diagnosis'
        ]
        
        provider_orders = []
        for intervention in intervention_list:
            intervention_lower = intervention.lower()
            if any(keyword in intervention_lower for keyword in provider_keywords):
                provider_orders.append(intervention)
        
        return provider_orders
    
    @staticmethod
    def get_active_alerts(patient_id=None, facility_id=None, severity=None):
        """
        Get active (unresolved) ADR alerts.
        
        Used for dashboard display and clinical review.
        """
        query = ADRAlert.query.filter(
            ADRAlert.status.in_([
                ADRAlert.STATUS_NEW,
                ADRAlert.STATUS_ACKNOWLEDGED,
                ADRAlert.STATUS_INVESTIGATING
            ])
        )
        
        if patient_id:
            query = query.filter(ADRAlert.patient_id == patient_id)
        
        if facility_id:
            query = query.filter(ADRAlert.facility_id == facility_id)
        
        if severity:
            query = query.filter(ADRAlert.severity == severity)
        
        return query.order_by(
            ADRAlert.requires_immediate_action.desc(),
            ADRAlert.created_at.desc()
        ).all()
    
    @staticmethod
    def acknowledge_alert(alert_id, user_id, notes=None):
        """
        Acknowledge an ADR alert.
        
        Updates status and records who acknowledged it.
        """
        alert = ADRAlert.query.get(alert_id)
        if not alert:
            return None
        
        alert.status = ADRAlert.STATUS_ACKNOWLEDGED
        alert.acknowledged_by_user_id = user_id
        alert.acknowledged_at = datetime.utcnow()
        
        if notes:
            alert.investigation_notes = notes
        
        db.session.commit()
        return alert
    
    @staticmethod
    def escalate_to_pharmacist(alert_id, user_id):
        """
        Create pharmacist intervention from ADR alert.
        
        Links alert to formal pharmacist review process.
        """
        alert = ADRAlert.query.get(alert_id)
        if not alert or alert.pharmacist_consulted:
            return None
        
        # Create pharmacist intervention
        intervention = PharmacistIntervention(
            patient_id=alert.patient_id,
            facility_id=alert.facility_id,
            pharmacist_id=user_id,  # Assuming user is pharmacist
            medication_id=alert.medication_id,
            intervention_type=PharmacistIntervention.TYPE_ADVERSE_REACTION,
            severity=PharmacistIntervention.SEVERITY_URGENT if alert.requires_immediate_action else PharmacistIntervention.SEVERITY_RECOMMEND_CHANGE,
            clinical_concern=alert.alert_summary,
            recommendation="Review for potential adverse drug reaction. " + (alert.escalation_guidance or ""),
            provider_notified=False
        )
        
        db.session.add(intervention)
        
        # Link alert to intervention
        alert.pharmacist_consulted = True
        alert.pharmacist_intervention_id = intervention.id
        alert.status = ADRAlert.STATUS_INVESTIGATING
        
        db.session.commit()
        return intervention
    
    @staticmethod
    def resolve_alert(alert_id, status, outcome_notes, action_taken=None):
        """
        Resolve an ADR alert with outcome documentation.
        """
        alert = ADRAlert.query.get(alert_id)
        if not alert:
            return None
        
        valid_resolution_statuses = [
            ADRAlert.STATUS_CONFIRMED_ADR,
            ADRAlert.STATUS_NOT_ADR,
            ADRAlert.STATUS_DISMISSED
        ]
        
        if status not in valid_resolution_statuses:
            raise ValueError(f"Invalid resolution status: {status}")
        
        alert.status = status
        alert.outcome = outcome_notes
        alert.action_taken = action_taken
        alert.resolved_at = datetime.utcnow()
        
        db.session.commit()
        return alert
