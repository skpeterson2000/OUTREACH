import api from './api'
import type { ApiResponse } from '../types'
import type {
  CarePlan,
  NursingIntervention,
  PhysicianOrder,
  AssistanceTask,
  InterventionCompletion,
  OrderCompletion,
  TaskCompletion,
  CreateCarePlanRequest,
  UpdateCarePlanRequest,
  CreateInterventionRequest,
  CreateOrderRequest,
  CreateTaskRequest,
  CompleteInterventionRequest,
  CompleteOrderRequest,
  CompleteTaskRequest,
} from '../types/carePlan'

// Care Plans
export const carePlansApi = {
  // Get all care plans with optional filtering
  getAll: (params?: { patient_id?: number; status?: string }) =>
    api.get<ApiResponse<CarePlan[]>>('/care-plans', { params }),

  // Get single care plan with all related items
  getById: (id: number) =>
    api.get<ApiResponse<CarePlan>>(`/care-plans/${id}`),

  // Create new care plan
  create: (data: CreateCarePlanRequest) =>
    api.post<ApiResponse<CarePlan>>('/care-plans', data),

  // Update care plan
  update: (id: number, data: UpdateCarePlanRequest) =>
    api.put<ApiResponse<CarePlan>>(`/care-plans/${id}`, data),
}

// Nursing Interventions
export const interventionsApi = {
  // Create intervention for a care plan
  create: (carePlanId: number, data: CreateInterventionRequest) =>
    api.post<ApiResponse<NursingIntervention>>(`/care-plans/${carePlanId}/interventions`, data),

  // Update intervention
  update: (interventionId: number, data: Partial<CreateInterventionRequest> & { status?: string; discontinued_reason?: string }) =>
    api.put<ApiResponse<NursingIntervention>>(`/care-plans/interventions/${interventionId}`, data),

  // Complete/document intervention
  complete: (interventionId: number, data: CompleteInterventionRequest) =>
    api.post<ApiResponse<InterventionCompletion>>(`/care-plans/interventions/${interventionId}/complete`, data),

  // Get completion history for an intervention
  getCompletions: (interventionId: number) =>
    api.get<ApiResponse<InterventionCompletion[]>>(`/care-plans/interventions/${interventionId}/completions`),
}

// Physician Orders
export const ordersApi = {
  // Create physician order for a care plan
  create: (carePlanId: number, data: CreateOrderRequest) =>
    api.post<ApiResponse<PhysicianOrder>>(`/care-plans/${carePlanId}/orders`, data),

  // Verify physician order (RN/LPN only)
  verify: (orderId: number, data?: { verification_status?: string }) =>
    api.post<ApiResponse<PhysicianOrder>>(`/care-plans/orders/${orderId}/verify`, data || {}),

  // Complete/document order
  complete: (orderId: number, data: CompleteOrderRequest) =>
    api.post<ApiResponse<OrderCompletion>>(`/care-plans/orders/${orderId}/complete`, data),
}

// Assistance Tasks
export const tasksApi = {
  // Create assistance task for a care plan
  create: (carePlanId: number, data: CreateTaskRequest) =>
    api.post<ApiResponse<AssistanceTask>>(`/care-plans/${carePlanId}/tasks`, data),

  // Complete/document task
  complete: (taskId: number, data: CompleteTaskRequest) =>
    api.post<ApiResponse<TaskCompletion>>(`/care-plans/tasks/${taskId}/complete`, data),

  // Get completion history for a task
  getCompletions: (taskId: number) =>
    api.get<ApiResponse<TaskCompletion[]>>(`/care-plans/tasks/${taskId}/completions`),
}

// Combined export for convenience
export const carePlanService = {
  carePlans: carePlansApi,
  interventions: interventionsApi,
  orders: ordersApi,
  tasks: tasksApi,
}

export default carePlanService
