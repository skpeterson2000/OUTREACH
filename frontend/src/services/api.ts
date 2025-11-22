import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import type {
  User,
  Patient,
  Medication,
  MedicationAdministration,
  Visit,
  VitalSigns,
  ADRAlert,
  MedicationReconciliation,
  MedicationDiscrepancy,
  LoginCredentials,
  MedicationAdministrationForm,
  PatientFilters,
  ApiResponse,
  PaginatedResponse,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Authentication
export const authApi = {
  login: (credentials: LoginCredentials) =>
    api.post<{ access_token: string; refresh_token: string; user: User }>('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get<ApiResponse<User>>('/auth/me'),
}

// Patients
export const patientsApi = {
  getAll: (filters?: PatientFilters) =>
    api.get<PaginatedResponse<Patient>>('/patients', { params: filters }),
  getById: (id: number) => api.get<ApiResponse<Patient>>(`/patients/${id}`),
  create: (data: Partial<Patient>) => api.post<ApiResponse<Patient>>('/patients', data),
  update: (id: number, data: Partial<Patient>) =>
    api.put<ApiResponse<Patient>>(`/patients/${id}`, data),
  delete: (id: number) => api.delete(`/patients/${id}`),
}

// Medications
export const medicationsApi = {
  getByPatient: (patientId: number) =>
    api.get<ApiResponse<Medication[]>>(`/patients/${patientId}/medications`),
  getById: (id: number) => api.get<ApiResponse<Medication>>(`/medications/${id}`),
  create: (patientId: number, data: Partial<Medication>) => 
    api.post<ApiResponse<Medication>>(`/patients/${patientId}/medications`, data),
  update: (id: number, data: Partial<Medication>) =>
    api.put<ApiResponse<Medication>>(`/medications/${id}`, data),
  partialUpdate: (id: number, data: Partial<Medication>) =>
    api.patch<ApiResponse<Medication>>(`/medications/${id}`, data),
  discontinue: (id: number, data?: { reason?: string; discontinue_date?: string }) => 
    api.post(`/medications/${id}/discontinue`, data || {}),
  hold: (id: number, data: { reason: string; expected_resume_date?: string }) =>
    api.post(`/medications/${id}/hold`, data),
  resume: (id: number) =>
    api.post(`/medications/${id}/resume`),
  // MAR endpoints
  getPatientMAR: (patientId: number, params?: { start_date?: string; end_date?: string; shift?: string }) =>
    api.get(`/patients/${patientId}/mar`, { params }),
  getDueMedications: (patientId: number, params?: { window_hours?: number; include_prn?: boolean }) =>
    api.get(`/patients/${patientId}/mar/due`, { params }),
  getOverdue: (params?: { grace_period_minutes?: number; patient_id?: number }) =>
    api.get(`/mar/overdue`, { params }),
  administer: (medicationId: number, data: any) =>
    api.post(`/medications/${medicationId}/administer`, data),
}

  // Medication Administration Records (MAR)
export const marApi = {
  getScheduled: (params?: { patient_id?: number; date?: string }) =>
    api.get<ApiResponse<MedicationAdministration[]>>('/mar/scheduled', { params }),
  administer: (data: MedicationAdministrationForm) =>
    api.post<ApiResponse<MedicationAdministration>>('/mar/administer', data),
  getHistory: (patientId: number, params?: { start_date?: string; end_date?: string }) =>
    api.get<ApiResponse<MedicationAdministration[]>>(`/mar/history/${patientId}`, { params }),
  markLate: (administrationId: number, reason: string) =>
    api.put(`/mar/${administrationId}/late`, { reason }),
  markRefused: (administrationId: number, reason: string) =>
    api.put(`/mar/${administrationId}/refused`, { reason }),
  administerMedication: (patientId: number, medicationId: number, data: any) =>
    api.post(`/medications/${medicationId}/administer`, data),
  getOverdueMedications: (params?: { patient_id?: number; grace_period_minutes?: number }) =>
    api.get('/mar/overdue', { params }),
  getMedicationADRAlerts: (medicationId: number) =>
    api.get(`/medications/${medicationId}/adr-alerts`),
}// Visits
export const visitsApi = {
  getAll: (filters?: any) => api.get<PaginatedResponse<Visit>>('/visits', { params: filters }),
  getById: (id: number) => api.get<ApiResponse<Visit>>(`/visits/${id}`),
  create: (data: Partial<Visit>) => api.post<ApiResponse<Visit>>('/visits', data),
  update: (id: number, data: Partial<Visit>) =>
    api.put<ApiResponse<Visit>>(`/visits/${id}`, data),
  checkIn: (id: number) => api.put(`/visits/${id}/check-in`),
  checkOut: (id: number, data: any) => api.put(`/visits/${id}/check-out`, data),
}

// Vital Signs
export const vitalSignsApi = {
  getByVisit: (visitId: number) =>
    api.get<ApiResponse<VitalSigns[]>>(`/visits/${visitId}/vital-signs`),
  create: (data: Partial<VitalSigns>) =>
    api.post<ApiResponse<VitalSigns>>('/vital-signs', data),
  update: (id: number, data: Partial<VitalSigns>) =>
    api.put<ApiResponse<VitalSigns>>(`/vital-signs/${id}`, data),
}

// ADR Surveillance
export const adrApi = {
  // Active alerts (reactions that have occurred)
  getActiveAlerts: (params?: { patient_id?: number; facility_id?: number; status?: string }) =>
    api.get<ApiResponse<ADRAlert[]>>('/adr-alerts', { params }),
  getAlertById: (id: number) => api.get<ApiResponse<ADRAlert>>(`/adr-alerts/${id}`),
  acknowledgeAlert: (id: number, data: any) =>
    api.post(`/adr-alerts/${id}/acknowledge`, data),
  updateAlertStatus: (id: number, status: string, notes?: string) =>
    api.put(`/adr-alerts/${id}/status`, { status, notes }),
  // Patient-specific alerts
  getPatientAlerts: (patientId: number, params?: { status?: string }) =>
    api.get<ApiResponse<ADRAlert[]>>(`/patients/${patientId}/adr-alerts`, { params }),
  // Check if user has acknowledged all alerts for patient
  checkPatientAcknowledgments: (patientId: number) =>
    api.get(`/adr-alerts/check-patient-acknowledgments/${patientId}`),
  // Proactive guidance for medication pass
  getMedicationRisks: (medicationId: number) =>
    api.get<ApiResponse<any>>(`/medications/${medicationId}/adr-risks`),
}

// Medication Reconciliation
export const reconciliationApi = {
  getPending: (params?: { patient_id?: number }) =>
    api.get<ApiResponse<MedicationReconciliation[]>>('/reconciliation/pending', { params }),
  getById: (id: number) =>
    api.get<ApiResponse<MedicationReconciliation>>(`/reconciliation/${id}`),
  getDiscrepancies: (reconciliationId: number) =>
    api.get<ApiResponse<MedicationDiscrepancy[]>>(`/reconciliation/${reconciliationId}/discrepancies`),
  resolveDiscrepancy: (discrepancyId: number, data: { resolution_action: string; resolution_notes: string }) =>
    api.put(`/reconciliation/discrepancies/${discrepancyId}/resolve`, data),
  complete: (reconciliationId: number) =>
    api.put(`/reconciliation/${reconciliationId}/complete`),
}

// Dashboard stats
export const dashboardApi = {
  getStats: () => api.get<ApiResponse<any>>('/dashboard/stats'),
  getUpcomingVisits: () => api.get<ApiResponse<Visit[]>>('/dashboard/upcoming-visits'),
  getRecentAlerts: () => api.get<ApiResponse<ADRAlert[]>>('/dashboard/recent-alerts'),
}

export default api
