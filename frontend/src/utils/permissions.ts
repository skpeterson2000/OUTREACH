/**
 * Role-based permission utilities for frontend access control
 */

export type UserRole = 'RN' | 'LPN' | 'Pharmacist' | 'Admin' | 'CNA' | 'TMA' | 'HHA' | 'Family'

/**
 * Licensed clinical staff who can administer medications independently
 */
export const LICENSED_ROLES: UserRole[] = ['RN', 'LPN', 'Admin']

/**
 * Delegated medication administration - TMAs (Trained Medication Assistants)
 * CNAs with additional training who can administer medications under RN supervision/delegation
 * Scope varies by state - some allow oral/topical, some allow injections with additional training
 */
export const DELEGATED_MEDICATION_ROLES: UserRole[] = ['TMA']

/**
 * All staff who can administer medications (licensed + delegated)
 */
export const MEDICATION_ADMINISTRATION_ROLES: UserRole[] = [...LICENSED_ROLES, ...DELEGATED_MEDICATION_ROLES]

/**
 * Staff who can modify medication orders (add/edit/hold/resume/discontinue per MD orders)
 * TMAs cannot modify orders - only administer as directed
 */
export const MEDICATION_MANAGEMENT_ROLES: UserRole[] = ['RN', 'LPN', 'Pharmacist', 'Admin']

/**
 * Staff who can view patient clinical data
 */
export const CLINICAL_VIEW_ROLES: UserRole[] = ['RN', 'LPN', 'Pharmacist', 'Admin', 'CNA', 'TMA', 'HHA']

/**
 * Staff who can modify patient demographics and admission data
 */
export const PATIENT_ADMIN_ROLES: UserRole[] = ['RN', 'Admin']

/**
 * Check if user has permission to administer medications (licensed or delegated)
 */
export const canAdministerMedications = (userRole?: string): boolean => {
  if (!userRole) return false
  return MEDICATION_ADMINISTRATION_ROLES.includes(userRole as UserRole)
}

/**
 * Check if user is administering under delegation (TMA)
 * These staff need additional safeguards and supervision tracking
 */
export const isDelegatedMedicationRole = (userRole?: string): boolean => {
  if (!userRole) return false
  return DELEGATED_MEDICATION_ROLES.includes(userRole as UserRole)
}

/**
 * Check if user is licensed independent practitioner (can administer without delegation)
 */
export const isLicensedPractitioner = (userRole?: string): boolean => {
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

/**
 * Check if user is unlicensed direct care staff (can request actions, report concerns)
 */
export const isUnlicensedStaff = (userRole?: string): boolean => {
  return userRole === 'CNA' || userRole === 'HHA'
}

/**
 * Check if user can request medication reorders
 */
export const canRequestMedicationReorder = (userRole?: string): boolean => {
  if (!userRole) return false
  // All clinical staff can request reorders
  return CLINICAL_VIEW_ROLES.includes(userRole as UserRole)
}

/**
 * Check if user can acknowledge ADR (Adverse Drug Reaction) alerts
 * Staff who administer medications need to acknowledge alerts about medications they give
 */
export const canAcknowledgeADRAlerts = (userRole?: string): boolean => {
  if (!userRole) return false
  // Licensed and delegated medication administrators can acknowledge
  return MEDICATION_ADMINISTRATION_ROLES.includes(userRole as UserRole)
}
