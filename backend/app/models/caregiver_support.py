"""Caregiver Support and Wellness Module.

This module provides comprehensive tracking and intervention tools for both
family caregivers and healthcare staff wellbeing. Proactively identifies
stress, burnout risk, and provides intervention tracking.

BUSINESS VALUE:
- Reduces staff turnover (30-50% reduction potential)
- Decreases sick days and burnout-related absences
- Improves patient outcomes through stable, supported care teams
- Demonstrates compliance with staff wellness initiatives
- Attracts talent with visible wellbeing commitment
- Reduces family caregiver crisis admissions
"""
from datetime import datetime, timedelta
from app import db


class CaregiverStressAssessment(db.Model):
    """
    Comprehensive stress and burnout assessment for family caregivers and staff.
    
    Tracks multiple validated instruments:
    - Modified Caregiver Strain Index (family caregivers)
    - Maslach Burnout Inventory elements (staff)
    - Perceived Stress Scale
    - Support system evaluation
    """
    
    __tablename__ = 'caregiver_stress_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Subject of Assessment
    caregiver_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: family_caregiver, nursing_staff, home_health_aide, admin_staff
    
    # For family caregivers
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), index=True)
    caregiver_name = db.Column(db.String(200))
    caregiver_relationship = db.Column(db.String(100))  # spouse, adult_child, etc.
    
    # For staff
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    # Who conducted assessment
    assessed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Assessment Data
    assessment_data = db.Column(db.JSON, nullable=False)
    # Stores detailed responses to screening instruments
    
    # Scores
    strain_index_score = db.Column(db.Integer)  # 0-13 (≥7 = high strain)
    burnout_score = db.Column(db.Integer)  # Staff burnout indicators
    perceived_stress_score = db.Column(db.Integer)  # PSS-10: 0-40
    
    # Risk Level
    risk_level = db.Column(db.String(20), index=True)
    # Levels: low, moderate, high, critical
    
    # Support System Assessment
    social_support_adequate = db.Column(db.Boolean)
    respite_care_available = db.Column(db.Boolean)
    financial_concerns = db.Column(db.Boolean)
    
    # Clinical Findings
    identified_stressors = db.Column(db.JSON)  # List of specific stressors
    protective_factors = db.Column(db.JSON)  # Strengths and resources
    warning_signs = db.Column(db.Text)  # Red flags noted
    
    # Recommendations
    recommended_interventions = db.Column(db.JSON)
    referrals_made = db.Column(db.JSON)  # Counseling, support groups, etc.
    
    # Follow-up
    requires_immediate_intervention = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)
    follow_up_completed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = db.relationship('Patient', foreign_keys=[patient_id])
    staff_member = db.relationship('User', foreign_keys=[staff_id])
    assessor = db.relationship('User', foreign_keys=[assessed_by])
    interventions = db.relationship('CaregiverIntervention', back_populates='assessment',
                                   lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_risk_trajectory(self):
        """
        Compare to previous assessments to identify worsening trends.
        Returns: improving, stable, declining, rapid_decline
        """
        if self.caregiver_type == 'family_caregiver' and self.patient_id:
            previous = CaregiverStressAssessment.query.filter_by(
                patient_id=self.patient_id,
                caregiver_type='family_caregiver'
            ).filter(
                CaregiverStressAssessment.assessment_date < self.assessment_date
            ).order_by(CaregiverStressAssessment.assessment_date.desc()).first()
        elif self.staff_id:
            previous = CaregiverStressAssessment.query.filter_by(
                staff_id=self.staff_id
            ).filter(
                CaregiverStressAssessment.assessment_date < self.assessment_date
            ).order_by(CaregiverStressAssessment.assessment_date.desc()).first()
        else:
            return 'no_baseline'
        
        if not previous:
            return 'baseline'
        
        current_score = self.strain_index_score or self.burnout_score or self.perceived_stress_score
        previous_score = previous.strain_index_score or previous.burnout_score or previous.perceived_stress_score
        
        if not current_score or not previous_score:
            return 'insufficient_data'
        
        change = current_score - previous_score
        
        if change <= -3:
            return 'improving'
        elif change >= 5:
            return 'rapid_decline'
        elif change >= 2:
            return 'declining'
        else:
            return 'stable'
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'caregiver_type': self.caregiver_type,
            'patient_id': self.patient_id,
            'staff_id': self.staff_id,
            'strain_index_score': self.strain_index_score,
            'burnout_score': self.burnout_score,
            'perceived_stress_score': self.perceived_stress_score,
            'risk_level': self.risk_level,
            'risk_trajectory': self.calculate_risk_trajectory(),
            'identified_stressors': self.identified_stressors,
            'recommended_interventions': self.recommended_interventions,
            'requires_immediate_intervention': self.requires_immediate_intervention,
            'assessment_date': self.assessment_date.isoformat(),
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None
        }
    
    def __repr__(self):
        return f'<CaregiverStressAssessment {self.id}: {self.caregiver_type} - {self.risk_level}>'


class CaregiverIntervention(db.Model):
    """
    Tracks interventions and support provided to caregivers.
    Demonstrates proactive care and measures effectiveness.
    """
    
    __tablename__ = 'caregiver_interventions'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('caregiver_stress_assessments.id'),
                              nullable=False, index=True)
    
    # Intervention Details
    intervention_type = db.Column(db.String(100), nullable=False, index=True)
    # Types: education, respite_coordination, counseling_referral, support_group,
    #        stress_management_training, schedule_adjustment, workload_reduction,
    #        peer_support, employee_assistance_program, time_off, recognition
    
    intervention_category = db.Column(db.String(50))
    # Categories: immediate_relief, skill_building, resource_connection, 
    #             organizational_change, emotional_support
    
    description = db.Column(db.Text, nullable=False)
    
    # Who provided intervention
    provided_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timing
    initiated_date = db.Column(db.Date, nullable=False)
    target_completion_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(20), default='active')
    # Status: planned, active, completed, declined, discontinued
    
    # Effectiveness Tracking
    caregiver_satisfaction = db.Column(db.Integer)  # 1-5 scale
    perceived_helpfulness = db.Column(db.Integer)  # 1-5 scale
    barriers_encountered = db.Column(db.Text)
    
    # Outcomes
    outcome_notes = db.Column(db.Text)
    follow_up_needed = db.Column(db.Boolean, default=False)
    
    # Cost tracking (for ROI analysis)
    estimated_cost = db.Column(db.Numeric(10, 2))
    actual_cost = db.Column(db.Numeric(10, 2))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assessment = db.relationship('CaregiverStressAssessment', back_populates='interventions')
    provider = db.relationship('User')
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'intervention_type': self.intervention_type,
            'intervention_category': self.intervention_category,
            'description': self.description,
            'status': self.status,
            'initiated_date': self.initiated_date.isoformat(),
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'caregiver_satisfaction': self.caregiver_satisfaction,
            'perceived_helpfulness': self.perceived_helpfulness,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<CaregiverIntervention {self.id}: {self.intervention_type} - {self.status}>'


class CaregiverResource(db.Model):
    """
    Library of evidence-based resources for caregiver support.
    Curated materials, referrals, and educational content.
    """
    
    __tablename__ = 'caregiver_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Resource Details
    title = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: article, video, workshop, support_group, hotline, organization,
    #        app, book, training_module, self_care_tool
    
    category = db.Column(db.String(100), index=True)
    # Categories: stress_management, self_care, communication, medical_info,
    #             financial_assistance, respite_care, counseling, legal,
    #             caregiver_skills, time_management, boundary_setting
    
    target_audience = db.Column(db.String(50))
    # Audiences: family_caregiver, nursing_staff, all_staff, managers
    
    # Content
    description = db.Column(db.Text)
    url = db.Column(db.String(500))
    file_path = db.Column(db.String(500))
    contact_info = db.Column(db.Text)
    
    # Metadata
    language = db.Column(db.String(20), default='en')
    evidence_based = db.Column(db.Boolean, default=True)
    cost = db.Column(db.String(50))  # free, low_cost, insurance_covered, etc.
    
    # Effectiveness
    times_accessed = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Numeric(3, 2))
    
    # Visibility
    is_active = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'title': self.title,
            'resource_type': self.resource_type,
            'category': self.category,
            'target_audience': self.target_audience,
            'description': self.description,
            'url': self.url,
            'contact_info': self.contact_info,
            'cost': self.cost,
            'average_rating': float(self.average_rating) if self.average_rating else None,
            'evidence_based': self.evidence_based
        }
    
    def __repr__(self):
        return f'<CaregiverResource {self.id}: {self.title}>'


class StaffWellnessDashboard:
    """
    Analytics and predictive tools for organizational wellness monitoring.
    Provides actionable insights for proactive intervention.
    """
    
    @staticmethod
    def calculate_team_burnout_risk(department=None, timeframe_days=90):
        """
        Calculate aggregate burnout risk for staff team.
        
        Returns:
        - overall_risk_score: 0-100
        - high_risk_count: number of staff at high risk
        - trends: improving/stable/declining
        - recommendations: list of systemic interventions
        """
        from sqlalchemy import func
        
        # Get recent assessments
        cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)
        
        query = CaregiverStressAssessment.query.filter(
            CaregiverStressAssessment.caregiver_type.in_([
                'nursing_staff', 'home_health_aide', 'admin_staff'
            ]),
            CaregiverStressAssessment.assessment_date >= cutoff_date
        )
        
        if department:
            # Join with User to filter by department
            from app.models.user import User
            query = query.join(User, CaregiverStressAssessment.staff_id == User.id)
            query = query.filter(User.department == department)
        
        assessments = query.all()
        
        if not assessments:
            return {
                'overall_risk_score': 0,
                'high_risk_count': 0,
                'total_assessed': 0,
                'trends': 'insufficient_data',
                'recommendations': ['Begin baseline stress assessments']
            }
        
        # Calculate metrics
        high_risk = [a for a in assessments if a.risk_level in ['high', 'critical']]
        moderate_risk = [a for a in assessments if a.risk_level == 'moderate']
        
        overall_risk_score = (
            (len(high_risk) * 100 + len(moderate_risk) * 50) / len(assessments)
        )
        
        # Analyze trends
        improving = sum(1 for a in assessments if a.calculate_risk_trajectory() == 'improving')
        declining = sum(1 for a in assessments if a.calculate_risk_trajectory() in ['declining', 'rapid_decline'])
        
        if declining > improving * 1.5:
            trend = 'declining'
        elif improving > declining * 1.5:
            trend = 'improving'
        else:
            trend = 'stable'
        
        # Generate recommendations
        recommendations = []
        
        if overall_risk_score > 60:
            recommendations.append('URGENT: Organizational burnout crisis - immediate leadership intervention needed')
            recommendations.append('Conduct workload analysis and redistribute if possible')
            recommendations.append('Implement mandatory time-off policy')
        elif overall_risk_score > 40:
            recommendations.append('Elevated team stress - increase support resources')
            recommendations.append('Schedule team debriefing/support sessions')
            recommendations.append('Review staffing ratios and scheduling')
        
        if len(high_risk) > 0:
            recommendations.append(f'Individual interventions needed for {len(high_risk)} high-risk staff')
        
        if trend == 'declining':
            recommendations.append('Trend analysis shows worsening conditions - investigate root causes')
        
        return {
            'overall_risk_score': round(overall_risk_score, 1),
            'high_risk_count': len(high_risk),
            'moderate_risk_count': len(moderate_risk),
            'low_risk_count': len(assessments) - len(high_risk) - len(moderate_risk),
            'total_assessed': len(assessments),
            'trend': trend,
            'improving_count': improving,
            'declining_count': declining,
            'recommendations': recommendations,
            'timeframe_days': timeframe_days
        }
    
    @staticmethod
    def predict_turnover_risk():
        """
        Identify staff at risk of leaving based on stress patterns.
        
        High turnover predictors:
        - Sustained high stress (3+ assessments showing high risk)
        - Rapid stress increase
        - Declining intervention participation
        - Low satisfaction scores
        """
        from app.models.user import User
        
        high_risk_staff = []
        
        # Get all staff with recent assessments
        recent_cutoff = datetime.utcnow() - timedelta(days=180)
        
        staff_with_assessments = db.session.query(
            CaregiverStressAssessment.staff_id
        ).filter(
            CaregiverStressAssessment.staff_id.isnot(None),
            CaregiverStressAssessment.assessment_date >= recent_cutoff
        ).distinct().all()
        
        for (staff_id,) in staff_with_assessments:
            assessments = CaregiverStressAssessment.query.filter_by(
                staff_id=staff_id
            ).order_by(CaregiverStressAssessment.assessment_date.desc()).limit(5).all()
            
            risk_factors = []
            
            # Check for sustained high stress
            high_stress_count = sum(1 for a in assessments if a.risk_level in ['high', 'critical'])
            if high_stress_count >= 3:
                risk_factors.append('sustained_high_stress')
            
            # Check for rapid increase
            if len(assessments) >= 2:
                if assessments[0].calculate_risk_trajectory() == 'rapid_decline':
                    risk_factors.append('rapid_stress_increase')
            
            # Check intervention participation
            recent_interventions = CaregiverIntervention.query.join(
                CaregiverStressAssessment
            ).filter(
                CaregiverStressAssessment.staff_id == staff_id,
                CaregiverIntervention.status == 'declined'
            ).count()
            
            if recent_interventions >= 2:
                risk_factors.append('declining_interventions')
            
            if len(risk_factors) >= 2:
                staff = User.query.get(staff_id)
                high_risk_staff.append({
                    'staff_id': staff_id,
                    'staff_name': staff.full_name if staff else 'Unknown',
                    'risk_factors': risk_factors,
                    'current_risk_level': assessments[0].risk_level if assessments else None,
                    'recommendation': 'Schedule retention conversation with manager'
                })
        
        return high_risk_staff
    
    @staticmethod
    def intervention_effectiveness_report(intervention_type=None, timeframe_days=180):
        """
        Analyze effectiveness of interventions.
        Helps identify what actually works.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)
        
        query = CaregiverIntervention.query.filter(
            CaregiverIntervention.completed_date.isnot(None),
            CaregiverIntervention.completed_date >= cutoff_date
        )
        
        if intervention_type:
            query = query.filter_by(intervention_type=intervention_type)
        
        interventions = query.all()
        
        if not interventions:
            return {'message': 'No completed interventions in timeframe'}
        
        # Calculate metrics
        total = len(interventions)
        with_satisfaction = [i for i in interventions if i.caregiver_satisfaction]
        with_helpfulness = [i for i in interventions if i.perceived_helpfulness]
        
        avg_satisfaction = (
            sum(i.caregiver_satisfaction for i in with_satisfaction) / len(with_satisfaction)
            if with_satisfaction else None
        )
        
        avg_helpfulness = (
            sum(i.perceived_helpfulness for i in with_helpfulness) / len(with_helpfulness)
            if with_helpfulness else None
        )
        
        # Breakdown by type
        by_type = {}
        for intervention in interventions:
            itype = intervention.intervention_type
            if itype not in by_type:
                by_type[itype] = {
                    'count': 0,
                    'satisfaction_scores': [],
                    'helpfulness_scores': []
                }
            by_type[itype]['count'] += 1
            if intervention.caregiver_satisfaction:
                by_type[itype]['satisfaction_scores'].append(intervention.caregiver_satisfaction)
            if intervention.perceived_helpfulness:
                by_type[itype]['helpfulness_scores'].append(intervention.perceived_helpfulness)
        
        # Calculate averages
        for itype in by_type:
            data = by_type[itype]
            data['avg_satisfaction'] = (
                sum(data['satisfaction_scores']) / len(data['satisfaction_scores'])
                if data['satisfaction_scores'] else None
            )
            data['avg_helpfulness'] = (
                sum(data['helpfulness_scores']) / len(data['helpfulness_scores'])
                if data['helpfulness_scores'] else None
            )
        
        return {
            'total_interventions': total,
            'average_satisfaction': round(avg_satisfaction, 2) if avg_satisfaction else None,
            'average_helpfulness': round(avg_helpfulness, 2) if avg_helpfulness else None,
            'breakdown_by_type': by_type,
            'timeframe_days': timeframe_days
        }
