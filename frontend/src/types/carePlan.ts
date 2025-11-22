/**
 * Care Plan TypeScript Types
 * Matches backend models for care plan management system
 */

export interface CarePlan {
  id: number;
  patient_id: number;
  facility_id: number;
  plan_name: string;
  plan_type: string; // 'admission', 'comprehensive', 'focused', 'discharge'
  care_goals: string;
  clinical_summary?: string;
  discharge_plan?: string;
  status: 'active' | 'completed' | 'discontinued';
  start_date: string; // ISO date
  expected_end_date?: string; // ISO date
  actual_end_date?: string; // ISO date
  next_review_date?: string; // ISO date
  last_review_date?: string; // ISO date
  primary_nurse_id?: number;
  ordering_physician?: string;
  physician_npi?: string;
  physician_phone?: string;
  created_by_user_id: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  
  // Relationships (populated when requested)
  interventions?: NursingIntervention[];
  orders?: PhysicianOrder[];
  tasks?: AssistanceTask[];
}

export interface NursingIntervention {
  id: number;
  care_plan_id: number;
  patient_id: number;
  intervention_type: string; // 'assessment', 'wound_care', 'catheter_care', 'tracheostomy_care', etc.
  intervention_name: string;
  description: string;
  rationale?: string;
  frequency?: string; // 'Daily', 'BID', 'PRN', 'Weekly on Monday'
  frequency_times_per_day?: number;
  scheduled_times?: string; // JSON array of times
  prn_indication?: string;
  start_date: string; // ISO date
  end_date?: string; // ISO date
  assigned_role?: string; // 'RN', 'LPN', 'CNA', etc.
  assigned_user_id?: number;
  requires_rn: boolean;
  can_delegate: boolean;
  priority: 'stat' | 'urgent' | 'routine';
  expected_outcome?: string;
  documentation_requirements?: string;
  status: 'active' | 'completed' | 'discontinued';
  discontinued_at?: string; // ISO datetime
  discontinued_by_user_id?: number;
  discontinued_reason?: string;
  created_by_user_id: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  
  // Relationships
  completions?: InterventionCompletion[];
}

export interface PhysicianOrder {
  id: number;
  care_plan_id: number;
  patient_id: number;
  order_type: string; // 'medication', 'treatment', 'therapy', 'diagnostic', 'equipment', 'diet'
  order_category?: string;
  order_text: string;
  ordering_physician: string;
  physician_npi?: string;
  physician_phone?: string;
  order_date: string; // ISO datetime
  start_date: string; // ISO date
  end_date?: string; // ISO date
  frequency?: string;
  duration?: string;
  prn_indication?: string;
  priority: 'stat' | 'urgent' | 'routine';
  special_instructions?: string;
  contraindications?: string;
  precautions?: string;
  expected_results?: string;
  verification_status: 'pending' | 'verified' | 'clarification_needed';
  verified_by_user_id?: number;
  verified_at?: string; // ISO datetime
  status: 'active' | 'completed' | 'discontinued' | 'on_hold';
  discontinued_at?: string; // ISO datetime
  discontinued_by_user_id?: number;
  discontinued_reason?: string;
  created_by_user_id: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  
  // Relationships
  completions?: OrderCompletion[];
}

export interface AssistanceTask {
  id: number;
  care_plan_id: number;
  patient_id: number;
  task_category: 'adl' | 'meal' | 'hygiene' | 'mobility' | 'comfort' | 'safety';
  task_name: string;
  description: string;
  adl_type?: string; // 'bathing', 'dressing', 'toileting', 'transferring', 'feeding', 'grooming'
  assistance_level?: string; // 'independent', 'supervision', 'minimal_assist', 'moderate_assist', 'maximal_assist', 'total_care'
  frequency: string;
  frequency_times_per_day?: number;
  scheduled_times?: string; // JSON array
  estimated_duration_minutes?: number;
  start_date: string; // ISO date
  end_date?: string; // ISO date
  assigned_role: string; // 'CNA', 'HHA', 'TMA'
  assigned_user_id?: number;
  requires_two_person_assist: boolean;
  priority: 'stat' | 'urgent' | 'routine';
  equipment_needed?: string;
  safety_precautions?: string;
  fall_risk_precautions: boolean;
  patient_preferences?: string;
  cultural_considerations?: string;
  status: 'active' | 'completed' | 'discontinued';
  discontinued_at?: string; // ISO datetime
  discontinued_by_user_id?: number;
  discontinued_reason?: string;
  created_by_user_id: number;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  
  // Relationships
  completions?: TaskCompletion[];
}

export interface InterventionCompletion {
  id: number;
  intervention_id: number;
  patient_id: number;
  completed_at: string; // ISO datetime
  completed_by_user_id: number;
  status: 'completed' | 'partially_completed' | 'not_done' | 'refused';
  completion_notes: string;
  patient_response?: string;
  outcome_achieved?: string;
  outcome_notes?: string;
  reason_not_done?: string;
  duration_minutes?: number;
  requires_follow_up: boolean;
  follow_up_notes?: string;
  created_at: string; // ISO datetime
}

export interface OrderCompletion {
  id: number;
  order_id: number;
  patient_id: number;
  completed_at: string; // ISO datetime
  completed_by_user_id: number;
  status: 'completed' | 'in_progress' | 'cancelled' | 'refused';
  completion_notes: string;
  results?: string;
  reason_not_done?: string;
  requires_follow_up: boolean;
  follow_up_notes?: string;
  physician_notified: boolean;
  notification_date?: string; // ISO datetime
  notification_method?: string;
  notification_notes?: string;
  created_at: string; // ISO datetime
}

export interface TaskCompletion {
  id: number;
  task_id: number;
  patient_id: number;
  completed_at: string; // ISO datetime
  completed_by_user_id: number;
  assisted_by_user_id?: number; // For two-person assists
  status: 'completed' | 'partially_completed' | 'not_done' | 'refused';
  completion_notes?: string;
  patient_tolerance?: string; // 'well_tolerated', 'some_difficulty', 'poorly_tolerated'
  patient_participation?: string;
  safety_incidents: boolean;
  incident_notes?: string;
  reason_not_done?: string;
  duration_minutes?: number;
  created_at: string; // ISO datetime
}

// Request/Response types for API calls
export interface CreateCarePlanRequest {
  patient_id: number;
  plan_name: string;
  plan_type: string;
  care_goals: string;
  clinical_summary?: string;
  start_date: string;
  expected_end_date?: string;
  primary_nurse_id?: number;
  ordering_physician?: string;
  physician_npi?: string;
  physician_phone?: string;
}

export interface UpdateCarePlanRequest {
  plan_name?: string;
  plan_type?: string;
  care_goals?: string;
  clinical_summary?: string;
  discharge_plan?: string;
  status?: 'active' | 'completed' | 'discontinued';
}

export interface CreateInterventionRequest {
  intervention_type: string;
  intervention_name: string;
  description: string;
  rationale?: string;
  frequency?: string;
  frequency_times_per_day?: number;
  scheduled_times?: string[];
  prn_indication?: string;
  start_date: string;
  end_date?: string;
  assigned_role?: string;
  assigned_user_id?: number;
  requires_rn?: boolean;
  priority?: 'stat' | 'urgent' | 'routine';
  expected_outcome?: string;
}

export interface CreateOrderRequest {
  order_type: string;
  order_category?: string;
  order_text: string;
  ordering_physician: string;
  physician_npi?: string;
  physician_phone?: string;
  order_date: string;
  start_date: string;
  end_date?: string;
  frequency?: string;
  duration?: string;
  prn_indication?: string;
  priority?: 'stat' | 'urgent' | 'routine';
  special_instructions?: string;
}

export interface CreateTaskRequest {
  task_category: 'adl' | 'meal' | 'hygiene' | 'mobility' | 'comfort' | 'safety';
  task_name: string;
  description: string;
  adl_type?: string;
  assistance_level?: string;
  frequency: string;
  frequency_times_per_day?: number;
  scheduled_times?: string[];
  estimated_duration_minutes?: number;
  start_date: string;
  end_date?: string;
  assigned_role: string;
  assigned_user_id?: number;
  requires_two_person_assist?: boolean;
  priority?: 'stat' | 'urgent' | 'routine';
  equipment_needed?: string;
  safety_precautions?: string;
  fall_risk_precautions?: boolean;
  patient_preferences?: string;
}

export interface CompleteInterventionRequest {
  completed_at?: string;
  status: 'completed' | 'partially_completed' | 'not_done' | 'refused';
  completion_notes: string;
  patient_response?: string;
  outcome_achieved?: string;
  outcome_notes?: string;
  reason_not_done?: string;
  duration_minutes?: number;
  requires_follow_up?: boolean;
  follow_up_notes?: string;
}

export interface CompleteOrderRequest {
  completed_at?: string;
  status: 'completed' | 'in_progress' | 'cancelled' | 'refused';
  completion_notes: string;
  results?: string;
  reason_not_done?: string;
  requires_follow_up?: boolean;
  follow_up_notes?: string;
  physician_notified?: boolean;
  notification_notes?: string;
}

export interface CompleteTaskRequest {
  completed_at?: string;
  assisted_by_user_id?: number;
  status: 'completed' | 'partially_completed' | 'not_done' | 'refused';
  completion_notes?: string;
  patient_tolerance?: string;
  patient_participation?: string;
  safety_incidents?: boolean;
  incident_notes?: string;
  reason_not_done?: string;
  duration_minutes?: number;
}
