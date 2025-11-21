/**
 * Role-based permission utilities for frontend access control
 */

export type UserRole = 'RN' | 'LPN' | 'Pharmacist' | 'Admin' | 'CNA' | 'HHA' | 'Family'

/**
 * Licensed clinical staff who can administer medications
 */
export const LICENSED_ROLES: UserRole[] = ['RN', 'LPN', 'Admin']

/**
 * Staff who can modify medication orders (add/edit/hold/resume/discontinue per MD orders)
 */
export const MEDICATION_MANAGEMENT_ROLES: UserRole[] = ['RN', 'LPN', 'Pharmacist', 'Admin']

/**
 * Staff who can view patient clinical data
 */
export const CLINICAL_VIEW_ROLES: UserRole[] = ['RN', 'LPN', 'Pharmacist', 'Admin', 'CNA', 'HHA']

/**
 * Staff who can modify patient demographics and admission data
 */
export const PATIENT_ADMIN_ROLES: UserRole[] = ['RN', 'Admin']

/**
 * Check if user has permission to administer medications
 */
export const canAdministerMedications = (userRole?: string): boolean => {
  if (!userRole) return false
  return LICENSED_ROLES.includes(userRole as UserRole)
}

/**
 * Check if user has permission to manage medication orders (add/edit/hold/resume/discontinue)
 * Nurses can add and modify medications per physician orders
 */
export const canManageMedications = (userRole?: string): boolean => {
  if (!userRole) return false
  return MEDICATION_MANAGEMENT_ROLES.includes(userRole as UserRole)
}

/**
 * Check if user has permission to view clinical data
 */
export const canViewClinicalData = (userRole?: string): boolean => {
  if (!userRole) return false
  return CLINICAL_VIEW_ROLES.includes(userRole as UserRole)
}

/**
 * Check if user has permission to modify patient records
 */
export const canEditPatients = (userRole?: string): boolean => {
  if (!userRole) return false
  return PATIENT_ADMIN_ROLES.includes(userRole as UserRole)
}

/**
 * Check if user has admin privileges
 */
export const isAdmin = (userRole?: string): boolean => {
  return userRole === 'Admin'
}

/**
 * Check if user is a pharmacist
 */
export const isPharmacist = (userRole?: string): boolean => {
  return userRole === 'Pharmacist'
}
