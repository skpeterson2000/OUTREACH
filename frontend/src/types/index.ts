// API Response Types for Home Care EHR

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: string
  license_number?: string
  phone?: string
  status: string
  is_active: boolean
  facility_id: number
}

export interface Patient {
  id: number
  medical_record_number: string
  first_name: string
  last_name: string
  full_name?: string
  date_of_birth: string
  age?: number
  gender: string
  address_line1?: string
  city?: string
  state?: string
  zip_code?: string
  phone_primary?: string
  email?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  facility_id: number
  admission_date: string
  discharge_date?: string
  status: string
  primary_diagnosis?: string
  secondary_diagnoses?: string[]
  allergies?: string[]
  code_status?: string
  fall_risk_score?: number
  braden_score?: number
  is_hospice: boolean
  active_medications_count?: number
  fall_risk?: boolean
}

export interface Medication {
  id: number
  patient_id: number
  medication_name: string
  generic_name?: string
  dose: string
  route: string
  frequency: string
  frequency_times_per_day?: number
  time_of_day?: string
  prescribing_physician: string
  start_date: string
  end_date?: string
  is_active: boolean
  is_prn: boolean
  prn_indication?: string
  instructions?: string
  is_controlled_substance: boolean
  status: string
}

export interface MedicationAdministration {
  id: number
  medication_id: number
  patient_id: number
  administered_by: number
  scheduled_time: string
  administration_time?: string
  status: string
  dose_given?: string
  route?: string
  notes?: string
  prn_reason?: string
  prn_pain_level_before?: number
  prn_pain_level_after?: number
  prn_effectiveness_rating?: number
  prn_effectiveness_notes?: string
  prn_reassessment_time?: string
  medication?: Medication
  nurse?: User
}

export interface Visit {
  id: number
  patient_id: number
  nurse_id: number
  visit_type: string
  scheduled_date: string
  check_in_time?: string
  check_out_time?: string
  status: string
  subjective?: string
  objective?: string
  assessment_text?: string
  plan?: string
  nurse_signature?: string
  patient?: Patient
  nurse?: User
}

export interface VitalSigns {
  id: number
  patient_id: number
  visit_id: number
  recorded_time: string
  temperature?: number
  pulse?: number
  respirations?: number
  blood_pressure_systolic?: number
  blood_pressure_diastolic?: number
  oxygen_saturation?: number
  pain_level?: number
  weight?: number
  height?: number
}

export interface PatientObservation {
  id: number
  patient_id: number
  facility_id: number
  observed_by_user_id: number
  observation_type: string
  observation_category: string
  observation_text: string
  severity_rating?: number
  related_vital_signs?: any
  observation_datetime: string
  patient?: Patient
  observed_by?: User
}

export interface ADRAlert {
  id: number
  patient_id: number
  facility_id: number
  medication_id: number
  observation_id: number
  known_adr_id: number
  suspected_reaction: string
  alert_summary: string
  confidence_level: string
  severity: string
  matching_symptoms: string[]
  matching_vital_signs: string[]
  correlation_score: number
  medication_start_date: string
  days_since_medication_start: number
  patient_risk_factors: string[]
  nursing_interventions: string[]
  provider_notification_needed: boolean
  provider_notification_urgency: string
  provider_notification_guidance: string
  suggested_provider_orders: string[]
  requires_immediate_action: boolean
  is_hospice_patient?: boolean
  hospice_comfort_focus?: string
  escalation_guidance?: string
  status: string
  created_at: string
  acknowledged_at?: string
  patient_name?: string
  patient_room?: string
  medication_ids?: number[]
  monitoring_parameters?: string[]
  clinical_guidance?: string
  reaction_type?: string
  patient?: Patient
  medication?: Medication
  observation?: PatientObservation
}

export interface MedicationReconciliation {
  id: number
  patient_id: number
  facility_id: number
  reconciliation_type: string
  transition_from?: string
  transition_to?: string
  source_medications: any[]
  current_medications: any[]
  discrepancies_count: number
  high_risk_discrepancies: number
  status: string
  requires_pharmacist_review: boolean
  created_at: string
  review_started_at?: string
  completed_at?: string
  patient?: Patient
}

export interface MedicationDiscrepancy {
  id: number
  reconciliation_id: number
  discrepancy_type: string
  severity: string
  medication_name: string
  source_details?: any
  current_details?: any
  clinical_concern?: string
  potential_impact?: string
  resolution_action: string
  resolution_notes?: string
  requires_pharmacist_input: boolean
  requires_provider_clarification: boolean
  created_at: string
  resolved_at?: string
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  status: string
  data: T[]
  count?: number
  page?: number
  per_page?: number
  pages?: number
  filters?: any
}

// Form types
export interface LoginCredentials {
  username: string
  password: string
}

export interface MedicationAdministrationForm {
  medication_id: number
  patient_id: number
  scheduled_time: string
  dose_given?: string
  route?: string
  notes?: string
  prn_reason?: string
  prn_pain_level_before?: number
}

export interface PatientFilters {
  status?: string
  facility_id?: number
  search?: string
  is_hospice?: boolean
}

export interface VisitFilters {
  patient_id?: number
  nurse_id?: number
  status?: string
  start_date?: string
  end_date?: string
}
