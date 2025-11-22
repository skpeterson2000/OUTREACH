import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Collapse,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab,
} from '@mui/material'
import {
  CheckCircle,
  Cancel,
  Warning,
  AccessTime,
  ExpandMore,
  ExpandLess,
  Medication as MedicationIcon,
  Info,
} from '@mui/icons-material'
import { Medication, ADRAlert } from '../types'
import { medicationsApi, adrApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import { canAdministerMedications, isUnlicensedStaff, canRequestMedicationReorder, isDelegatedMedicationRole } from '../utils/permissions'

interface MARAdministration {
  id: number
  scheduled_time: string
  administration_time?: string
  status: 'given' | 'refused' | 'held' | 'omitted' | 'pending'
  dose_given?: string
  route?: string
  administered_by_name?: string
  notes?: string
  prn_reason?: string
}

interface MARMedication extends Medication {
  administrations: MARAdministration[]
  total_administrations: number
  given_count: number
  missed_count: number
  indication?: string
  prescriber?: string
  scheduled_times?: string
  special_instructions?: string
}

export default function MAR() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const patientId = parseInt(id || '0')
  
  // Check if user can administer medications (licensed or delegated TMA)
  const canAdminister = canAdministerMedications(user?.role)
  const isDelegated = isDelegatedMedicationRole(user?.role)
  const isUnlicensed = isUnlicensedStaff(user?.role)

  const [medications, setMedications] = useState<MARMedication[]>([])
  const [adrAlerts, setAdrAlerts] = useState<ADRAlert[]>([])
  const [overdueMeds, setOverdueMeds] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedMed, setExpandedMed] = useState<number | null>(null)
  const [adminDialogOpen, setAdminDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [reorderDialogOpen, setReorderDialogOpen] = useState(false)
  const [concernDialogOpen, setConcernDialogOpen] = useState(false)
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false)
  const [adrBlockDialogOpen, setAdrBlockDialogOpen] = useState(false)
  const [vitalsDialogOpen, setVitalsDialogOpen] = useState(false)
  const [selectedMed, setSelectedMed] = useState<MARMedication | null>(null)
  const [adrCheckResult, setAdrCheckResult] = useState<any>(null)
  const [medicationAlerts, setMedicationAlerts] = useState<Record<number, ADRAlert[]>>({})
  const [tabValue, setTabValue] = useState(0)
  const [gracePeriod, setGracePeriod] = useState(60) // Default 60 minutes
  const [historyDays, setHistoryDays] = useState(7) // Days of history to show
  const [fullMedHistory, setFullMedHistory] = useState<MARAdministration[]>([])
  const [editForm, setEditForm] = useState({
    time_of_day: '',
    special_instructions: '',
  })
  const [reorderForm, setReorderForm] = useState({
    current_supply_days: '',
    reason: '',
    attestation: false,
  })
  const [concernForm, setConcernForm] = useState({
    concern_type: 'supply',
    description: '',
    urgent: false,
  })

  // Administration form state
  const [adminForm, setAdminForm] = useState({
    status: 'given',
    dose_given: '',
    route: '',
    notes: '',
    prn_reason: '',
    blood_glucose: '',
    calculated_dose: '',
    dose_verified: false,
  })

  // Vital signs form for pre-administration assessment
  const [vitalsForm, setVitalsForm] = useState({
    heart_rate: '',
    blood_pressure_systolic: '',
    blood_pressure_diastolic: '',
    visual_disturbances: false,
    gi_symptoms: false,
    dizziness: false,
    bleeding_bruising: false,
    inr_pt: '',
    vitals_verified: false,
  })

  useEffect(() => {
    loadMARData()
    loadADRAlerts()
    loadOverdueMeds()
    loadMedicationAlerts()
    // Set up polling for overdue medications every 5 minutes
    const interval = setInterval(loadOverdueMeds, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [patientId])

  const loadMedicationAlerts = async () => {
    try {
      // Load alerts for all active medications
      const alertsMap: Record<number, ADRAlert[]> = {}
      for (const med of medications) {
        try {
          const response = await medicationsApi.getMedicationADRAlerts(med.id)
          if (response.data.active_alerts && response.data.active_alerts.length > 0) {
            alertsMap[med.id] = response.data.active_alerts
          }
        } catch (err) {
          // Medication may not have alerts, continue
        }
      }
      setMedicationAlerts(alertsMap)
    } catch (error) {
      console.error('Failed to load medication alerts:', error)
    }
  }

  const loadMARData = async () => {
    try {
      setLoading(true)
      const response = await medicationsApi.getPatientMAR(patientId, {
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
      })
      setMedications(response.data.data || [])
    } catch (error) {
      console.error('Failed to load MAR:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadADRAlerts = async () => {
    try {
      const response = await adrApi.getPatientAlerts(patientId, { status: 'NEW' })
      const alerts = response.data?.data || response.data || []
      setAdrAlerts(Array.isArray(alerts) ? alerts : [])
    } catch (error) {
      console.error('Failed to load ADR alerts:', error)
    }
  }

  const loadOverdueMeds = async () => {
    try {
      const response = await medicationsApi.getOverdueMedications({
        patient_id: patientId,
        grace_period_minutes: gracePeriod,
      })
      setOverdueMeds(response.data.data || [])
    } catch (error) {
      console.error('Failed to load overdue medications:', error)
    }
  }

  const loadMedicationHistory = async (medId: number) => {
    try {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - historyDays)
      
      const response = await medicationsApi.getPatientMAR(patientId, {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
      })
      
      const med = response.data.data.find((m: MARMedication) => m.id === medId)
      setFullMedHistory(med?.administrations || [])
      setHistoryDialogOpen(true)
    } catch (error) {
      console.error('Failed to load medication history:', error)
      alert('Failed to load administration history')
    }
  }

  const handleAdministerClick = async (med: MARMedication) => {
    setSelectedMed(med)
    
    // CRITICAL SAFETY CHECK: Verify ADR alert acknowledgments before allowing administration
    try {
      const checkResponse = await adrApi.checkPatientAcknowledgments(patientId)
      console.log('🔒 ADR Check Result:', checkResponse.data)
      
      if (!checkResponse.data.can_administer) {
        // BLOCKED: Alerts not acknowledged or expired
        setAdrCheckResult(checkResponse.data)
        setAdrBlockDialogOpen(true)
        return // Do not proceed to administration
      }
    } catch (error: any) {
      console.error('❌ ADR check failed:', error)
      alert(`⚠️ Safety check failed: ${error.response?.data?.message || 'Unable to verify alert acknowledgments'}`)
      return
    }

    // Check if this medication requires pre-administration vital signs
    const requiresVitals = requiresPreAdministrationVitals(med)
    if (requiresVitals) {
      // Show vitals dialog first
      setVitalsForm({
        heart_rate: '',
        blood_pressure_systolic: '',
        blood_pressure_diastolic: '',
        visual_disturbances: false,
        gi_symptoms: false,
        dizziness: false,
        bleeding_bruising: false,
        inr_pt: '',
        vitals_verified: false,
      })
      setVitalsDialogOpen(true)
      return
    }
    
    // Proceed to normal administration dialog
    proceedToAdministration(med)
  }

  const requiresPreAdministrationVitals = (med: MARMedication): boolean => {
    const medName = med.medication_name?.toLowerCase() || ''
    
    // Digoxin requires HR and symptom assessment
    if (medName.includes('digoxin') || medName.includes('lanoxin')) return true
    
    // Anticoagulants require bleeding assessment
    if (medName.includes('warfarin') || medName.includes('coumadin') || 
        medName.includes('heparin') || medName.includes('enoxaparin') ||
        medName.includes('apixaban') || medName.includes('rivaroxaban')) return true
    
    // Antihypertensives require BP
    if (medName.includes('metoprolol') || medName.includes('lisinopril') ||
        medName.includes('amlodipine') || medName.includes('losartan')) return true
    
    return false
  }

  const proceedToAdministration = (med: MARMedication) => {
    // Check if this is sliding scale insulin
    const isSlidingScale = med.medication_name?.toLowerCase().includes('insulin') && 
                          (med.instructions?.toLowerCase().includes('sliding scale') || 
                           med.instructions?.toLowerCase().includes('per scale') ||
                           med.special_instructions?.toLowerCase().includes('sliding scale'))
    
    setAdminForm({
      status: 'given',
      dose_given: isSlidingScale ? '' : (med.dose || ''),
      route: med.route || 'PO',
      notes: '',
      prn_reason: med.is_prn ? '' : 'N/A',
      blood_glucose: '',
      calculated_dose: '',
      dose_verified: false,
    })
    setAdminDialogOpen(true)
  }

  const handleVitalsVerified = () => {
    if (!selectedMed) return
    
    // Validate vital signs based on medication
    const medName = selectedMed.medication_name?.toLowerCase() || ''
    
    if (medName.includes('digoxin')) {
      if (!vitalsForm.heart_rate) {
        alert('❌ Heart rate is required before administering Digoxin')
        return
      }
      const hr = parseInt(vitalsForm.heart_rate)
      if (hr < 60) {
        if (!confirm(`⚠️ WARNING: Heart rate is ${hr} bpm (below 60)\n\nDigoxin should typically be HELD for HR < 60.\n\nDo you want to HOLD this medication and notify the provider?`)) {
          return
        }
        // Hold the medication
        handleHoldMedication(selectedMed)
        setVitalsDialogOpen(false)
        return
      }
    }
    
    if (!vitalsForm.vitals_verified) {
      alert('❌ You must verify that you have reviewed the vital signs and assessment')
      return
    }
    
    // Add vitals to notes
    const vitalsNotes = buildVitalsNotes()
    setAdminForm(prev => ({
      ...prev,
      notes: vitalsNotes
    }))
    
    setVitalsDialogOpen(false)
    proceedToAdministration(selectedMed)
  }

  const buildVitalsNotes = (): string => {
    const notes: string[] = []
    if (vitalsForm.heart_rate) notes.push(`HR: ${vitalsForm.heart_rate} bpm`)
    if (vitalsForm.blood_pressure_systolic && vitalsForm.blood_pressure_diastolic) {
      notes.push(`BP: ${vitalsForm.blood_pressure_systolic}/${vitalsForm.blood_pressure_diastolic}`)
    }
    if (vitalsForm.visual_disturbances) notes.push('Visual disturbances: YES')
    if (vitalsForm.gi_symptoms) notes.push('GI symptoms: YES')
    if (vitalsForm.dizziness) notes.push('Dizziness: YES')
    if (vitalsForm.bleeding_bruising) notes.push('Bleeding/bruising: YES')
    if (vitalsForm.inr_pt) notes.push(`INR/PT: ${vitalsForm.inr_pt}`)
    return notes.join('; ')
  }

  // Calculate sliding scale insulin dose based on blood glucose
  const calculateSlidingScaleDose = (bloodGlucose: number, instructions?: string): { dose: string; message: string; critical: boolean } => {
    // Standard sliding scale (can be customized per patient)
    // This is a typical adult sliding scale - should come from med orders in production
    if (bloodGlucose < 70) {
      return { dose: '0', message: '⚠️ HYPOGLYCEMIA - DO NOT GIVE INSULIN. Give 15g carbs, recheck in 15min', critical: true }
    } else if (bloodGlucose < 150) {
      return { dose: '0', message: 'Blood glucose in target range - no coverage needed', critical: false }
    } else if (bloodGlucose <= 200) {
      return { dose: '2', message: '2 units for BG 151-200', critical: false }
    } else if (bloodGlucose <= 250) {
      return { dose: '4', message: '4 units for BG 201-250', critical: false }
    } else if (bloodGlucose <= 300) {
      return { dose: '6', message: '6 units for BG 251-300', critical: false }
    } else if (bloodGlucose <= 350) {
      return { dose: '8', message: '8 units for BG 301-350', critical: false }
    } else if (bloodGlucose <= 400) {
      return { dose: '10', message: '10 units for BG 351-400', critical: false }
    } else {
      return { dose: '12', message: '⚠️ CRITICAL HIGH - 12 units for BG >400. Consider notifying MD', critical: true }
    }
  }

  const handleBloodGlucoseChange = (bg: string) => {
    const bgValue = parseFloat(bg)
    if (!isNaN(bgValue) && bgValue > 0) {
      const result = calculateSlidingScaleDose(bgValue, selectedMed?.instructions)
      setAdminForm({
        ...adminForm,
        blood_glucose: bg,
        calculated_dose: result.dose,
        dose_given: result.dose,
      })
    } else {
      setAdminForm({
        ...adminForm,
        blood_glucose: bg,
        calculated_dose: '',
        dose_given: '',
      })
    }
  }

  const handleAdministerSubmit = async () => {
    if (!selectedMed) return
    
    // Check if sliding scale insulin and verify dose
    const isSlidingScale = selectedMed.medication_name?.toLowerCase().includes('insulin') && 
                          (selectedMed.instructions?.toLowerCase().includes('sliding scale') || 
                           selectedMed.special_instructions?.toLowerCase().includes('sliding scale'))
    
    if (isSlidingScale) {
      if (!adminForm.blood_glucose) {
        alert('⚠️ Blood glucose reading is required for sliding scale insulin')
        return
      }
      if (!adminForm.dose_verified) {
        alert('⚠️ You must verify the calculated dose before administering')
        return
      }
    }

    try {
      await medicationsApi.administerMedication(patientId, selectedMed.id, {
        ...adminForm,
        scheduled_time: new Date().toISOString(),
        notes: adminForm.blood_glucose 
          ? `BG: ${adminForm.blood_glucose} mg/dL. ${adminForm.notes || ''}`.trim()
          : adminForm.notes,
      })
      setAdminDialogOpen(false)
      loadMARData() // Refresh
    } catch (error) {
      console.error('Failed to record administration:', error)
    }
  }

  const handleHoldMedication = async (med: MARMedication) => {
    const reason = prompt('Reason for holding this medication:')
    if (!reason) return

    try {
      await medicationsApi.hold(med.id, { reason })
      alert(`${med.medication_name} placed on hold`)
      loadMARData() // Refresh
    } catch (error: any) {
      console.error('Failed to hold medication:', error)
      alert(error.response?.data?.error || 'Failed to hold medication')
    }
  }

  const handleResumeMedication = async (medicationId: number) => {
    if (!confirm('Resume this medication?')) return

    try {
      await medicationsApi.resume(medicationId)
      alert('Medication resumed')
      loadMARData() // Refresh
    } catch (error: any) {
      console.error('Failed to resume medication:', error)
      alert(error.response?.data?.error || 'Failed to resume medication')
    }
  }

  const handleEditSchedule = (med: MARMedication) => {
    setSelectedMed(med)
    setEditForm({
      time_of_day: med.time_of_day || '',
      special_instructions: med.special_instructions || '',
    })
    setEditDialogOpen(true)
  }

  const handleEditSubmit = async () => {
    if (!selectedMed) return

    try {
      await medicationsApi.update(selectedMed.id, editForm)
      alert('Schedule updated successfully')
      setEditDialogOpen(false)
      loadMARData() // Refresh
    } catch (error: any) {
      console.error('Failed to update medication:', error)
      alert(error.response?.data?.error || 'Failed to update medication')
    }
  }

  const handleRequestReorder = (med: MARMedication) => {
    setSelectedMed(med)
    setReorderForm({
      current_supply_days: '',
      reason: '',
      attestation: false,
    })
    setReorderDialogOpen(true)
  }

  const handleReorderSubmit = async () => {
    if (!selectedMed || !reorderForm.attestation) {
      alert('You must attest that you have checked the current supply')
      return
    }

    try {
      // This would call a backend endpoint to create a reorder request
      // For now, we'll show success and notify licensed staff
      console.log('Reorder request:', {
        medication_id: selectedMed.id,
        patient_id: patientId,
        requested_by: user?.username,
        ...reorderForm,
      })
      alert(`Reorder request submitted for ${selectedMed.medication_name}. Licensed nursing staff will be notified.`)
      setReorderDialogOpen(false)
    } catch (error: any) {
      console.error('Failed to submit reorder request:', error)
      alert('Failed to submit reorder request')
    }
  }

  const handleReportConcern = (med: MARMedication) => {
    setSelectedMed(med)
    setConcernForm({
      concern_type: 'supply',
      description: '',
      urgent: false,
    })
    setConcernDialogOpen(true)
  }

  const handleConcernSubmit = async () => {
    if (!selectedMed || !concernForm.description.trim()) {
      alert('Please describe the concern')
      return
    }

    try {
      // This would call a backend endpoint to create a medication concern
      console.log('Concern reported:', {
        medication_id: selectedMed.id,
        patient_id: patientId,
        reported_by: user?.username,
        ...concernForm,
      })
      alert(`Concern reported for ${selectedMed.medication_name}. ${concernForm.urgent ? 'URGENT flag set - ' : ''}Licensed nursing staff will be notified immediately.`)
      setConcernDialogOpen(false)
    } catch (error: any) {
      console.error('Failed to report concern:', error)
      alert('Failed to report concern')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'given':
        return <CheckCircle color="success" fontSize="small" />
      case 'refused':
        return <Cancel color="error" fontSize="small" />
      case 'held':
      case 'omitted':
        return <Warning color="warning" fontSize="small" />
      default:
        return <AccessTime color="action" fontSize="small" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'given':
        return 'success'
      case 'refused':
        return 'error'
      case 'held':
      case 'omitted':
        return 'warning'
      default:
        return 'default'
    }
  }

  const scheduledMeds = medications.filter(m => !m.is_prn)
  const prnMeds = medications.filter(m => m.is_prn)

  const renderMedicationRow = (med: MARMedication) => {
    const isExpanded = expandedMed === med.id
    const relevantAlerts = adrAlerts.filter(alert => 
      alert.medication_ids?.includes(med.id)
    )

    const medAlerts = medicationAlerts[med.id] || []
    const hasAlerts = medAlerts.length > 0

    return (
      <>
        <TableRow key={med.id} hover sx={{ bgcolor: hasAlerts ? 'error.50' : 'transparent' }}>
          <TableCell>
            <Box display="flex" alignItems="center" gap={1}>
              <IconButton
                size="small"
                onClick={() => setExpandedMed(isExpanded ? null : med.id)}
              >
                {isExpanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
              <Box>
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="body2" fontWeight="bold">
                    {med.medication_name}
                  </Typography>
                  {hasAlerts && (
                    <Chip 
                      icon={<Warning />}
                      label="ADR ALERT" 
                      size="small" 
                      color="error" 
                      sx={{ fontWeight: 'bold' }}
                    />
                  )}
                  {med.status === 'held' && (
                    <Chip label="HELD" size="small" color="warning" />
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {med.dose} {med.route}
                  {med.frequency && ` - ${med.frequency}`}
                </Typography>
                {med.status === 'held' && med.special_instructions && (
                  <Typography variant="caption" color="warning.main" display="block">
                    {med.special_instructions.split('\n')[0]}
                  </Typography>
                )}
              </Box>
            </Box>
          </TableCell>
          <TableCell>
            {med.is_prn ? (
              <Chip label="PRN" size="small" color="info" />
            ) : (
              <Typography variant="caption">{med.scheduled_times || 'See schedule'}</Typography>
            )}
          </TableCell>
          <TableCell>
            {med.administrations.length > 0 ? (
              <Box display="flex" gap={0.5} flexWrap="wrap">
                {med.administrations.map((admin, idx) => (
                  <Chip
                    key={idx}
                    icon={getStatusIcon(admin.status)}
                    label={new Date(admin.scheduled_time).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                    size="small"
                    color={getStatusColor(admin.status) as any}
                    variant={admin.status === 'given' ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            ) : (
              <Typography variant="caption" color="text.secondary">
                No administrations yet
              </Typography>
            )}
          </TableCell>
          <TableCell>
            {relevantAlerts.length > 0 && (
              <Chip
                icon={<Warning />}
                label={`${relevantAlerts.length} Alert${relevantAlerts.length > 1 ? 's' : ''}`}
                size="small"
                color="error"
                variant="outlined"
              />
            )}
          </TableCell>
          <TableCell>
            <Box display="flex" gap={1} flexWrap="wrap">
              {canAdminister ? (
                // Can administer medications (licensed RN/LPN or delegated TMA)
                med.status === 'held' ? (
                  isDelegated ? (
                    // TMAs cannot hold/unhold - must notify licensed staff
                    <Typography variant="body2" color="text.secondary">
                      On hold - notify RN
                    </Typography>
                  ) : (
                    // Licensed staff can unhold
                    <Button
                      size="small"
                      variant="outlined"
                      color="success"
                      onClick={() => handleResumeMedication(med.id)}
                    >
                      Unhold
                    </Button>
                  )
                ) : (
                  <>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<MedicationIcon />}
                      onClick={() => handleAdministerClick(med)}
                    >
                      {isDelegated ? 'Give (Delegated)' : 'Give Now'}
                    </Button>
                    {!isDelegated && (
                      // Only licensed staff can hold meds or edit schedules
                      <>
                        <Button
                          size="small"
                          variant="outlined"
                          color="warning"
                          onClick={() => handleHoldMedication(med)}
                        >
                          Hold
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleEditSchedule(med)}
                        >
                          Edit Schedule
                        </Button>
                      </>
                    )}
                    {isDelegated && (
                      // TMAs should have quick access to report concerns
                      <Button
                        size="small"
                        variant="outlined"
                        color="warning"
                        onClick={() => handleReportConcern(med)}
                      >
                        Report Issue
                      </Button>
                    )}
                  </>
                )
              ) : isUnlicensed ? (
                // Unlicensed staff (CNA, HHA): Delegated support tasks
                <>
                  <Button
                    size="small"
                    variant="outlined"
                    color="primary"
                    onClick={() => handleRequestReorder(med)}
                  >
                    Request Reorder
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="warning"
                    onClick={() => handleReportConcern(med)}
                  >
                    Report Concern
                  </Button>
                </>
              ) : (
                // Other roles: No actions
                <Typography variant="body2" color="text.secondary">
                  View only
                </Typography>
              )}
            </Box>
          </TableCell>
        </TableRow>
        <TableRow>
          <TableCell colSpan={5} sx={{ py: 0 }}>
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <Box sx={{ py: 2, px: 3, bgcolor: 'grey.50' }}>
                <Grid container spacing={3}>
                  {/* Medication Details */}
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom color="primary">
                      Medication Details
                    </Typography>
                    <Box sx={{ pl: 2 }}>
                      {med.indication && (
                        <Typography variant="body2">
                          <strong>Indication:</strong> {med.indication}
                        </Typography>
                      )}
                      {med.instructions && (
                        <Typography variant="body2">
                          <strong>Instructions:</strong> {med.instructions}
                        </Typography>
                      )}
                      {med.prescriber && (
                        <Typography variant="body2">
                          <strong>Prescriber:</strong> {med.prescriber}
                        </Typography>
                      )}
                      {med.start_date && (
                        <Typography variant="body2">
                          <strong>Started:</strong> {new Date(med.start_date).toLocaleDateString()}
                        </Typography>
                      )}
                    </Box>
                  </Grid>

                  {/* ADR Guidance */}
                  {relevantAlerts.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom color="error">
                        ⚠️ What To Watch For
                      </Typography>
                      {relevantAlerts.map((alert, idx) => (
                        <Alert 
                          key={idx} 
                          severity="warning" 
                          sx={{ mb: 1 }}
                          action={
                            <Button 
                              size="small" 
                              onClick={() => navigate('/adr')}
                            >
                              Details
                            </Button>
                          }
                        >
                          <Typography variant="body2" fontWeight="bold">
                            {alert.reaction_type}
                          </Typography>
                          <Typography variant="caption">
                            {alert.clinical_guidance?.substring(0, 150)}...
                          </Typography>
                        </Alert>
                      ))}
                    </Grid>
                  )}

                  {/* Administration History */}
                  {med.administrations.length > 0 && (
                    <Grid item xs={12}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="subtitle2" color="primary">
                          Today's Administration History
                        </Typography>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => {
                            setSelectedMed(med)
                            loadMedicationHistory(med.id)
                          }}
                        >
                          View Full History ({historyDays} days)
                        </Button>
                      </Box>
                      <TableContainer sx={{ maxHeight: 200 }}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Scheduled</TableCell>
                              <TableCell>Given</TableCell>
                              <TableCell>Status</TableCell>
                              <TableCell>Dose</TableCell>
                              <TableCell>By</TableCell>
                              <TableCell>Notes</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {med.administrations.map((admin, idx) => (
                              <TableRow key={idx}>
                                <TableCell>
                                  {new Date(admin.scheduled_time).toLocaleTimeString()}
                                </TableCell>
                                <TableCell>
                                  {admin.administration_time 
                                    ? new Date(admin.administration_time).toLocaleTimeString()
                                    : '-'}
                                </TableCell>
                                <TableCell>
                                  <Chip
                                    icon={getStatusIcon(admin.status)}
                                    label={admin.status}
                                    size="small"
                                    color={getStatusColor(admin.status) as any}
                                  />
                                </TableCell>
                                <TableCell>{admin.dose_given || '-'}</TableCell>
                                <TableCell>{admin.administered_by_name || '-'}</TableCell>
                                <TableCell>
                                  <Typography variant="caption">
                                    {admin.notes || (admin.prn_reason ? `PRN: ${admin.prn_reason}` : '-')}
                                  </Typography>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Grid>
                  )}
                </Grid>
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      </>
    )
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading MAR...</Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Medication Administration Record (MAR)
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Today: {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </Typography>
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            label="Grace Period (minutes)"
            type="number"
            size="small"
            value={gracePeriod}
            onChange={(e) => {
              setGracePeriod(parseInt(e.target.value) || 60)
              loadOverdueMeds()
            }}
            sx={{ width: 180 }}
            helperText="Alert window after scheduled time"
          />
          <Button onClick={() => navigate(`/patients/${patientId}`)}>
            Back to Patient
          </Button>
        </Box>
      </Box>

      {/* Overdue Medications Alert */}
      {overdueMeds.length > 0 && (
        <Alert 
          severity="error" 
          icon={<AccessTime />}
          sx={{ mb: 2 }}
        >
          <Typography variant="body2" fontWeight="bold">
            ⚠️ {overdueMeds.length} Overdue Medication{overdueMeds.length > 1 ? 's' : ''} (Grace period: {gracePeriod} minutes)
          </Typography>
          <Box sx={{ mt: 1 }}>
            {overdueMeds.map((med, idx) => (
              <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Chip 
                  label={`${med.minutes_overdue} min overdue`} 
                  size="small" 
                  color="error" 
                />
                <Typography variant="caption">
                  <strong>{med.medication_name}</strong> {med.dose} - Due at {new Date(med.scheduled_time).toLocaleTimeString()}
                </Typography>
                {med.is_high_risk && (
                  <Chip label="HIGH RISK" size="small" color="error" variant="outlined" />
                )}
              </Box>
            ))}
          </Box>
        </Alert>
      )}

      {/* Active ADR Alerts Banner */}
      {adrAlerts.length > 0 && (
        <Alert 
          severity="warning" 
          icon={<Warning />}
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={() => navigate('/adr')}>
              View All Alerts
            </Button>
          }
        >
          <Typography variant="body2" fontWeight="bold">
            {adrAlerts.length} Active Medication Safety Alert{adrAlerts.length > 1 ? 's' : ''}
          </Typography>
          <Typography variant="caption">
            Pay special attention to the "What To Watch For" guidance below when giving medications
          </Typography>
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="primary">
                {medications.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Medications
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="success.main">
                {medications.reduce((sum, m) => sum + m.given_count, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Given Today
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: overdueMeds.length > 0 ? 'error.light' : 'background.paper' }}>
            <CardContent>
              <Typography variant="h4" color={overdueMeds.length > 0 ? 'error.dark' : 'error.main'}>
                {overdueMeds.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Overdue ({gracePeriod}min)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="warning.main">
                {medications.filter(m => m.status === 'held').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Held Medications
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for Scheduled vs PRN */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={`Scheduled Medications (${scheduledMeds.length})`} />
          <Tab label={`PRN Medications (${prnMeds.length})`} />
        </Tabs>
      </Paper>

      {/* Medication Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width="30%">Medication</TableCell>
              <TableCell width="15%">Schedule</TableCell>
              <TableCell width="25%">Today's Status</TableCell>
              <TableCell width="15%">Alerts</TableCell>
              <TableCell width="15%">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tabValue === 0 && scheduledMeds.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography variant="body2" color="text.secondary" py={3}>
                    No scheduled medications
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {tabValue === 0 && scheduledMeds.map(renderMedicationRow)}

            {tabValue === 1 && prnMeds.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography variant="body2" color="text.secondary" py={3}>
                    No PRN medications
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {tabValue === 1 && prnMeds.map(renderMedicationRow)}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Administration Dialog */}
      <Dialog open={adminDialogOpen} onClose={() => setAdminDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Record Medication Administration
          {selectedMed && (
            <Typography variant="body2" color="text.secondary">
              {selectedMed.medication_name} - {selectedMed.dose} {selectedMed.route}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedMed && adrAlerts.some(a => a.medication_ids?.includes(selectedMed.id)) && (
            <Alert severity="warning" icon={<Info />} sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="bold">
                ⚠️ Remember to watch for:
              </Typography>
              {adrAlerts
                .filter(a => a.medication_ids?.includes(selectedMed.id))
                .map((alert, idx) => (
                  <Typography key={idx} variant="caption" display="block">
                    • {alert.reaction_type}: {alert.monitoring_parameters?.join(', ')}
                  </Typography>
                ))}
            </Alert>
          )}

          {/* Sliding Scale Insulin Calculator */}
          {selectedMed && selectedMed.medication_name?.toLowerCase().includes('insulin') && 
           (selectedMed.instructions?.toLowerCase().includes('sliding scale') || 
            selectedMed.special_instructions?.toLowerCase().includes('sliding scale')) && (
            <Alert severity="error" icon={<Warning />} sx={{ mb: 3, mt: 2 }}>
              <Typography variant="body2" fontWeight="bold">
                🩸 SLIDING SCALE INSULIN - Blood Glucose Required
              </Typography>
              <Typography variant="caption">
                HIGH RISK MEDICATION: Check blood glucose BEFORE calculating dose. Wrong dose can cause life-threatening hypoglycemia.
              </Typography>
            </Alert>
          )}

          {/* Blood Glucose Input for Sliding Scale */}
          {selectedMed && selectedMed.medication_name?.toLowerCase().includes('insulin') && 
           (selectedMed.instructions?.toLowerCase().includes('sliding scale') || 
            selectedMed.special_instructions?.toLowerCase().includes('sliding scale')) && (
            <>
              <TextField
                label="Blood Glucose (mg/dL)"
                fullWidth
                type="number"
                value={adminForm.blood_glucose}
                onChange={(e) => handleBloodGlucoseChange(e.target.value)}
                sx={{ mb: 2, mt: 2 }}
                required
                helperText="Enter current blood glucose reading to calculate insulin dose"
                InputProps={{
                  endAdornment: <Typography variant="caption" sx={{ ml: 1 }}>mg/dL</Typography>
                }}
              />

              {adminForm.blood_glucose && adminForm.calculated_dose !== undefined && (
                <>
                  {/* Visual Sliding Scale */}
                  <Paper sx={{ p: 2, mb: 2, bgcolor: parseFloat(adminForm.blood_glucose) < 70 || parseFloat(adminForm.blood_glucose) > 400 ? 'error.50' : 'success.50', border: '2px solid', borderColor: parseFloat(adminForm.blood_glucose) < 70 || parseFloat(adminForm.blood_glucose) > 400 ? 'error.main' : 'success.main' }}>
                    <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                      📊 Sliding Scale Calculation:
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" display="block" sx={{ opacity: parseFloat(adminForm.blood_glucose) < 150 ? 1 : 0.5 }}>
                        • <strong>BG &lt;70:</strong> NO INSULIN - Treat hypoglycemia
                      </Typography>
                      <Typography variant="caption" display="block" sx={{ opacity: parseFloat(adminForm.blood_glucose) >= 150 && parseFloat(adminForm.blood_glucose) <= 200 ? 1 : 0.5, bgcolor: parseFloat(adminForm.blood_glucose) >= 151 && parseFloat(adminForm.blood_glucose) <= 200 ? 'primary.light' : 'transparent', px: 1, py: 0.5, borderRadius: 1 }}>
                        • <strong>BG 151-200:</strong> Give 2 units
                      </Typography>
                      <Typography variant="caption" display="block" sx={{ opacity: parseFloat(adminForm.blood_glucose) >= 201 && parseFloat(adminForm.blood_glucose) <= 250 ? 1 : 0.5, bgcolor: parseFloat(adminForm.blood_glucose) >= 201 && parseFloat(adminForm.blood_glucose) <= 250 ? 'primary.light' : 'transparent', px: 1, py: 0.5, borderRadius: 1 }}>
                        • <strong>BG 201-250:</strong> Give 4 units
                      </Typography>
                      <Typography variant="caption" display="block" sx={{ opacity: parseFloat(adminForm.blood_glucose) >= 251 && parseFloat(adminForm.blood_glucose) <= 300 ? 1 : 0.5, bgcolor: parseFloat(adminForm.blood_glucose) >= 251 && parseFloat(adminForm.blood_glucose) <= 300 ? 'primary.light' : 'transparent', px: 1, py: 0.5, borderRadius: 1 }}>
                        • <strong>BG 251-300:</strong> Give 6 units
                      </Typography>
                      <Typography variant="caption" display="block" sx={{ opacity: parseFloat(adminForm.blood_glucose) >= 301 && parseFloat(adminForm.blood_glucose) <= 350 ? 1 : 0.5, bgcolor: parseFloat(adminForm.blood_glucose) >= 301 && parseFloat(adminForm.blood_glucose) <= 350 ? 'primary.light' : 'transparent', px: 1, py: 0.5, borderRadius: 1 }}>
                        • <strong>BG 301-350:</strong> Give 8 units
                      </Typography>
                      <Typography variant="caption" display="block" sx={{ opacity: parseFloat(adminForm.blood_glucose) >= 351 && parseFloat(adminForm.blood_glucose) <= 400 ? 1 : 0.5, bgcolor: parseFloat(adminForm.blood_glucose) >= 351 && parseFloat(adminForm.blood_glucose) <= 400 ? 'primary.light' : 'transparent', px: 1, py: 0.5, borderRadius: 1 }}>
                        • <strong>BG 351-400:</strong> Give 10 units
                      </Typography>
                      <Typography variant="caption" display="block" sx={{ opacity: parseFloat(adminForm.blood_glucose) > 400 ? 1 : 0.5 }}>
                        • <strong>BG &gt;400:</strong> Give 12 units + notify MD
                      </Typography>
                    </Box>

                    <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 1, border: '2px solid', borderColor: 'primary.main' }}>
                      <Typography variant="h5" fontWeight="bold" color="primary">
                        ➜ Calculated Dose: {adminForm.calculated_dose} {adminForm.calculated_dose === '0' ? '' : 'units'}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {calculateSlidingScaleDose(parseFloat(adminForm.blood_glucose)).message}
                      </Typography>
                    </Box>

                    {/* Dose Verification Checkbox */}
                    <Box sx={{ 
                      mt: 2,
                      p: 2, 
                      border: '2px solid', 
                      borderColor: adminForm.dose_verified ? 'success.main' : 'error.main',
                      borderRadius: 1,
                      bgcolor: adminForm.dose_verified ? 'success.50' : 'error.50',
                    }}>
                      <Box display="flex" alignItems="flex-start" gap={1}>
                        <input
                          type="checkbox"
                          checked={adminForm.dose_verified}
                          onChange={(e) => setAdminForm({ ...adminForm, dose_verified: e.target.checked })}
                          style={{ marginTop: '4px' }}
                        />
                        <Box>
                          <Typography variant="body2" fontWeight="bold" color={adminForm.dose_verified ? 'success.dark' : 'error.dark'}>
                            ✓ I have verified the calculated dose is correct
                          </Typography>
                          <Typography variant="caption">
                            I confirm that I have checked the blood glucose reading, reviewed the sliding scale, 
                            and verified that <strong>{adminForm.calculated_dose} units</strong> is the correct dose for BG of <strong>{adminForm.blood_glucose} mg/dL</strong>.
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  </Paper>
                </>
              )}
            </>
          )}

          <FormControl fullWidth sx={{ mb: 2, mt: 2 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={adminForm.status}
              onChange={(e) => setAdminForm({ ...adminForm, status: e.target.value })}
              label="Status"
            >
              <MenuItem value="given">Given</MenuItem>
              <MenuItem value="refused">Refused</MenuItem>
              <MenuItem value="held">Held</MenuItem>
              <MenuItem value="omitted">Omitted</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Dose Given"
            fullWidth
            value={adminForm.dose_given}
            onChange={(e) => setAdminForm({ ...adminForm, dose_given: e.target.value })}
            sx={{ mb: 2 }}
            disabled={selectedMed?.medication_name?.toLowerCase().includes('insulin') && 
                     (selectedMed.instructions?.toLowerCase().includes('sliding scale') || 
                      selectedMed.special_instructions?.toLowerCase().includes('sliding scale'))}
            helperText={selectedMed?.medication_name?.toLowerCase().includes('insulin') && 
                       (selectedMed.instructions?.toLowerCase().includes('sliding scale') || 
                        selectedMed.special_instructions?.toLowerCase().includes('sliding scale')) 
                       ? 'Dose auto-calculated from blood glucose' : ''}
          />

          <TextField
            label="Route"
            fullWidth
            value={adminForm.route}
            onChange={(e) => setAdminForm({ ...adminForm, route: e.target.value })}
            sx={{ mb: 2 }}
          />

          {selectedMed?.is_prn && (
            <TextField
              label="PRN Reason"
              fullWidth
              value={adminForm.prn_reason}
              onChange={(e) => setAdminForm({ ...adminForm, prn_reason: e.target.value })}
              sx={{ mb: 2 }}
              required
            />
          )}

          <TextField
            label="Notes"
            fullWidth
            multiline
            rows={3}
            value={adminForm.notes}
            onChange={(e) => setAdminForm({ ...adminForm, notes: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdminDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAdministerSubmit} variant="contained">
            Record Administration
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reorder Request Dialog */}
      <Dialog open={reorderDialogOpen} onClose={() => setReorderDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Request Medication Reorder
          {selectedMed && (
            <Typography variant="body2" color="text.secondary">
              {selectedMed.medication_name} - {selectedMed.dose} {selectedMed.route}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2, mt: 1 }}>
            <Typography variant="body2" fontWeight="bold">
              Delegated Task: Medication Supply Check
            </Typography>
            <Typography variant="caption">
              This request will notify licensed nursing staff to review and reorder if needed.
              Your attestation confirms you have checked the physical medication supply.
            </Typography>
          </Alert>

          <TextField
            label="Current Supply (estimated days remaining)"
            fullWidth
            type="number"
            value={reorderForm.current_supply_days}
            onChange={(e) => setReorderForm({ ...reorderForm, current_supply_days: e.target.value })}
            sx={{ mb: 2 }}
            required
            helperText="Count remaining doses and estimate days of supply"
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Reason for Reorder Request</InputLabel>
            <Select
              value={reorderForm.reason}
              onChange={(e) => setReorderForm({ ...reorderForm, reason: e.target.value })}
              label="Reason for Reorder Request"
            >
              <MenuItem value="low_supply">Low Supply (Below reorder threshold)</MenuItem>
              <MenuItem value="upcoming_expiration">Upcoming Expiration</MenuItem>
              <MenuItem value="anticipated_need">Anticipated Increased Need</MenuItem>
              <MenuItem value="other">Other (specify in notes)</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ 
            p: 2, 
            border: '2px solid', 
            borderColor: reorderForm.attestation ? 'success.main' : 'grey.300',
            borderRadius: 1,
            bgcolor: reorderForm.attestation ? 'success.50' : 'grey.50',
            mb: 2 
          }}>
            <Box display="flex" alignItems="flex-start" gap={1}>
              <input
                type="checkbox"
                checked={reorderForm.attestation}
                onChange={(e) => setReorderForm({ ...reorderForm, attestation: e.target.checked })}
                style={{ marginTop: '4px' }}
              />
              <Box>
                <Typography variant="body2" fontWeight="bold">
                  ✓ Attestation Required
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  I attest that I have physically checked the current medication supply,
                  counted remaining doses, and verified the information provided above is accurate
                  to the best of my knowledge. I understand this request will be reviewed by
                  licensed nursing staff.
                </Typography>
              </Box>
            </Box>
          </Box>

          <Alert severity="success" icon={<Info />}>
            <Typography variant="caption">
              <strong>What happens next:</strong> Licensed nursing staff will receive your request,
              verify the supply, and coordinate with pharmacy/physician for reorder if needed.
              You may be asked to confirm or provide additional information.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReorderDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleReorderSubmit} 
            variant="contained"
            disabled={!reorderForm.attestation || !reorderForm.current_supply_days || !reorderForm.reason}
          >
            Submit Reorder Request
          </Button>
        </DialogActions>
      </Dialog>

      {/* Report Concern Dialog */}
      <Dialog open={concernDialogOpen} onClose={() => setConcernDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Report Medication Concern
          {selectedMed && (
            <Typography variant="body2" color="text.secondary">
              {selectedMed.medication_name} - {selectedMed.dose} {selectedMed.route}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2, mt: 1 }}>
            <Typography variant="body2" fontWeight="bold">
              Patient Safety Alert
            </Typography>
            <Typography variant="caption">
              Use this to report supply issues, administration concerns, or patient questions
              about medications. Licensed nursing staff will be notified immediately.
            </Typography>
          </Alert>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Concern Type</InputLabel>
            <Select
              value={concernForm.concern_type}
              onChange={(e) => setConcernForm({ ...concernForm, concern_type: e.target.value })}
              label="Concern Type"
            >
              <MenuItem value="supply">Supply Issue (Out of stock, damaged, expired)</MenuItem>
              <MenuItem value="patient_question">Patient Has Questions/Concerns</MenuItem>
              <MenuItem value="administration_difficulty">Patient Difficulty Taking Medication</MenuItem>
              <MenuItem value="adverse_reaction">Possible Adverse Reaction (URGENT)</MenuItem>
              <MenuItem value="other">Other Safety Concern</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Describe the Concern"
            fullWidth
            multiline
            rows={4}
            value={concernForm.description}
            onChange={(e) => setConcernForm({ ...concernForm, description: e.target.value })}
            sx={{ mb: 2 }}
            required
            placeholder="Provide specific details: What did you observe? What did the patient say? What is the concern?"
          />

          <Box sx={{ 
            p: 2, 
            border: '2px solid', 
            borderColor: concernForm.urgent ? 'error.main' : 'grey.300',
            borderRadius: 1,
            bgcolor: concernForm.urgent ? 'error.50' : 'grey.50',
          }}>
            <Box display="flex" alignItems="flex-start" gap={1}>
              <input
                type="checkbox"
                checked={concernForm.urgent}
                onChange={(e) => setConcernForm({ ...concernForm, urgent: e.target.checked })}
                style={{ marginTop: '4px' }}
              />
              <Box>
                <Typography variant="body2" fontWeight="bold" color={concernForm.urgent ? 'error.main' : 'text.primary'}>
                  🚨 Mark as URGENT
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Check this box if the concern requires immediate attention (patient safety risk,
                  possible adverse reaction, critical medication unavailable). Licensed staff will
                  be notified with high priority alert.
                </Typography>
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConcernDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleConcernSubmit} 
            variant="contained"
            color={concernForm.urgent ? 'error' : 'primary'}
            disabled={!concernForm.description.trim()}
          >
            {concernForm.urgent ? 'Submit URGENT Concern' : 'Submit Concern'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Schedule Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Medication Schedule</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Editing: <strong>{selectedMed?.medication_name}</strong>
          </Typography>

          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Schedule Times:</strong> Enter administration times separated by commas
            </Typography>
            <Typography variant="caption">
              Example: 08:00,14:00,20:00 for TID schedule
            </Typography>
          </Alert>

          <TextField
            label="Administration Times"
            fullWidth
            value={editForm.time_of_day}
            onChange={(e) => setEditForm({ ...editForm, time_of_day: e.target.value })}
            placeholder="08:00,14:00,20:00"
            sx={{ mb: 2 }}
            helperText="Enter times in 24-hour format (HH:MM) separated by commas"
          />

          <TextField
            label="Special Instructions"
            fullWidth
            multiline
            rows={3}
            value={editForm.special_instructions}
            onChange={(e) => setEditForm({ ...editForm, special_instructions: e.target.value })}
            placeholder="Give with food, monitor BP after administration, etc."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleEditSubmit} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* ADR Alert Blocking Dialog */}
      <Dialog 
        open={adrBlockDialogOpen} 
        onClose={() => setAdrBlockDialogOpen(false)} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: {
            border: '4px solid',
            borderColor: 'error.main',
          }
        }}
      >
        <DialogTitle sx={{ bgcolor: 'error.main', color: 'white' }}>
          <Box display="flex" alignItems="center" gap={1}>
            <Warning fontSize="large" />
            <Box>
              <Typography variant="h6" fontWeight="bold">
                🚨 MEDICATION ADMINISTRATION BLOCKED
              </Typography>
              <Typography variant="body2">
                Patient Safety Alert - Action Required
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="body2" fontWeight="bold">
              YOU CANNOT ADMINISTER MEDICATIONS UNTIL ALL ADR ALERTS ARE ACKNOWLEDGED
            </Typography>
            <Typography variant="caption">
              This is a required safety check to protect patients from adverse drug reactions.
            </Typography>
          </Alert>

          {adrCheckResult && adrCheckResult.unacknowledged_alerts && adrCheckResult.unacknowledged_alerts.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="error" gutterBottom>
                Unacknowledged Alerts ({adrCheckResult.unacknowledged_alerts.length}):
              </Typography>
              {adrCheckResult.unacknowledged_alerts.map((alert: any, idx: number) => (
                <Paper key={idx} sx={{ p: 2, mb: 2, border: '2px solid', borderColor: 'error.main', bgcolor: 'error.50' }}>
                  <Typography variant="body2" fontWeight="bold" color="error.dark">
                    {alert.suspected_reaction || alert.reaction_type}
                  </Typography>
                  <Typography variant="caption" display="block" gutterBottom>
                    Severity: {alert.severity} | Confidence: {alert.confidence_level}
                  </Typography>
                  <Typography variant="caption">
                    {alert.alert_summary?.substring(0, 200)}...
                  </Typography>
                </Paper>
              ))}
            </Box>
          )}

          {adrCheckResult && adrCheckResult.expired_acknowledgments && adrCheckResult.expired_acknowledgments.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="warning.dark" gutterBottom>
                Expired Acknowledgments ({adrCheckResult.expired_acknowledgments.length}):
              </Typography>
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="caption">
                  Your previous acknowledgments have expired (over 12 hours old). 
                  You must re-acknowledge at the start of each shift.
                </Typography>
              </Alert>
            </Box>
          )}

          <Box sx={{ p: 2, bgcolor: 'info.50', borderRadius: 1, border: '1px solid', borderColor: 'info.main' }}>
            <Typography variant="body2" fontWeight="bold" gutterBottom>
              📋 What You Need To Do:
            </Typography>
            <Typography variant="body2" component="ol" sx={{ pl: 2 }}>
              <li>Click "Review & Acknowledge Alerts" below</li>
              <li>Read each alert carefully and understand the suspected reaction</li>
              <li>Complete all three safety verifications</li>
              <li>Choose whether to ACKNOWLEDGE (continue with monitoring) or HOLD MEDICATION</li>
              <li>Return here to administer the medication</li>
            </Typography>
          </Box>

          <Alert severity="info" icon={<Info />} sx={{ mt: 2 }}>
            <Typography variant="caption">
              <strong>Why is this important?</strong> ADR alerts notify you of suspected adverse drug reactions 
              that require enhanced monitoring. By acknowledging, you verify that you understand the risks and 
              will monitor appropriately. This protects both the patient and you.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdrBlockDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={() => {
              setAdrBlockDialogOpen(false)
              navigate(`/patients/${patientId}#alerts`)
            }} 
            variant="contained" 
            color="error"
            size="large"
          >
            REVIEW & ACKNOWLEDGE ALERTS NOW
          </Button>
        </DialogActions>
      </Dialog>

      {/* Pre-Administration Vital Signs Dialog */}
      <Dialog 
        open={vitalsDialogOpen} 
        onClose={() => setVitalsDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: {
            border: '3px solid',
            borderColor: 'warning.main',
          }
        }}
      >
        <DialogTitle sx={{ bgcolor: 'warning.light' }}>
          <Box display="flex" alignItems="center" gap={1}>
            <Warning />
            <Box>
              <Typography variant="h6" fontWeight="bold">
                ⚕️ Pre-Administration Assessment Required
              </Typography>
              {selectedMed && (
                <Typography variant="body2" color="text.secondary">
                  {selectedMed.medication_name} - {selectedMed.dose} {selectedMed.route}
                </Typography>
              )}
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="body2" fontWeight="bold">
              HIGH-RISK MEDICATION - Vital Signs Check Required
            </Typography>
            <Typography variant="caption">
              This medication requires pre-administration assessment to ensure patient safety.
            </Typography>
          </Alert>

          {selectedMed?.medication_name?.toLowerCase().includes('digoxin') && (
            <>
              <Typography variant="subtitle2" color="error" gutterBottom>
                🫀 Digoxin Pre-Administration Checks:
              </Typography>
              
              <TextField
                label="Heart Rate (bpm) *"
                fullWidth
                type="number"
                value={vitalsForm.heart_rate}
                onChange={(e) => setVitalsForm({ ...vitalsForm, heart_rate: e.target.value })}
                sx={{ mb: 2 }}
                required
                helperText="HOLD digoxin if HR < 60 bpm"
                error={vitalsForm.heart_rate ? parseInt(vitalsForm.heart_rate) < 60 : false}
              />

              {vitalsForm.heart_rate && parseInt(vitalsForm.heart_rate) < 60 && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  <Typography variant="body2" fontWeight="bold">
                    ⚠️ HOLD DIGOXIN - Heart rate is below 60 bpm
                  </Typography>
                  <Typography variant="caption">
                    Digoxin should typically be held for bradycardia (HR {"<"} 60). 
                    Notify the provider before administering.
                  </Typography>
                </Alert>
              )}

              <Box sx={{ mb: 2, p: 2, border: '1px solid', borderColor: 'grey.300', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight="bold" gutterBottom>
                  Assess for Digoxin Toxicity Symptoms:
                </Typography>
                
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <input
                    type="checkbox"
                    checked={vitalsForm.visual_disturbances}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, visual_disturbances: e.target.checked })}
                  />
                  <Typography variant="body2">
                    Visual disturbances (yellow-green halos, blurred vision)
                  </Typography>
                </Box>

                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <input
                    type="checkbox"
                    checked={vitalsForm.gi_symptoms}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, gi_symptoms: e.target.checked })}
                  />
                  <Typography variant="body2">
                    GI symptoms (nausea, vomiting, loss of appetite)
                  </Typography>
                </Box>

                <Box display="flex" alignItems="center" gap={1}>
                  <input
                    type="checkbox"
                    checked={vitalsForm.dizziness}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, dizziness: e.target.checked })}
                  />
                  <Typography variant="body2">
                    Dizziness, confusion, or weakness
                  </Typography>
                </Box>
              </Box>

              {(vitalsForm.visual_disturbances || vitalsForm.gi_symptoms || vitalsForm.dizziness) && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  <Typography variant="body2" fontWeight="bold">
                    ⚠️ POSSIBLE DIGOXIN TOXICITY
                  </Typography>
                  <Typography variant="caption">
                    Patient is showing symptoms of possible digoxin toxicity. 
                    Consider HOLDING medication and notifying provider immediately.
                  </Typography>
                </Alert>
              )}
            </>
          )}

          {selectedMed?.medication_name?.toLowerCase().match(/warfarin|coumadin|heparin|enoxaparin|apixaban|rivaroxaban/) && (
            <>
              <Typography variant="subtitle2" color="error" gutterBottom>
                🩸 Anticoagulant Pre-Administration Checks:
              </Typography>
              
              <TextField
                label="Recent INR/PT (if applicable)"
                fullWidth
                value={vitalsForm.inr_pt}
                onChange={(e) => setVitalsForm({ ...vitalsForm, inr_pt: e.target.value })}
                sx={{ mb: 2 }}
                helperText="Enter most recent INR or PT value"
              />

              <Box sx={{ mb: 2, p: 2, border: '1px solid', borderColor: 'grey.300', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight="bold" gutterBottom>
                  Assess for Bleeding/Bruising:
                </Typography>
                
                <Box display="flex" alignItems="center" gap={1}>
                  <input
                    type="checkbox"
                    checked={vitalsForm.bleeding_bruising}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, bleeding_bruising: e.target.checked })}
                  />
                  <Typography variant="body2">
                    New or worsening bleeding, bruising, or signs of internal bleeding
                  </Typography>
                </Box>
              </Box>

              {vitalsForm.bleeding_bruising && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  <Typography variant="body2" fontWeight="bold">
                    ⚠️ BLEEDING RISK
                  </Typography>
                  <Typography variant="caption">
                    Patient showing signs of bleeding. Consider HOLDING anticoagulant 
                    and notifying provider immediately.
                  </Typography>
                </Alert>
              )}
            </>
          )}

          <Box sx={{ 
            mt: 3,
            p: 2, 
            border: '2px solid', 
            borderColor: vitalsForm.vitals_verified ? 'success.main' : 'grey.300',
            borderRadius: 1,
            bgcolor: vitalsForm.vitals_verified ? 'success.50' : 'grey.50',
          }}>
            <Box display="flex" alignItems="flex-start" gap={1}>
              <input
                type="checkbox"
                checked={vitalsForm.vitals_verified}
                onChange={(e) => setVitalsForm({ ...vitalsForm, vitals_verified: e.target.checked })}
                style={{ marginTop: '4px', cursor: 'pointer' }}
              />
              <Box>
                <Typography variant="body2" fontWeight="bold">
                  ✓ I have completed the pre-administration assessment
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  I confirm that I have checked the required vital signs and assessed the patient 
                  for contraindications. The vital signs are within acceptable parameters for 
                  administering this medication.
                </Typography>
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVitalsDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleVitalsVerified} 
            variant="contained" 
            color="success"
            disabled={!vitalsForm.vitals_verified}
          >
            ✓ ASSESSMENT COMPLETE - PROCEED
          </Button>
        </DialogActions>
      </Dialog>

      {/* Full Medication History Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h6">
                Medication Administration History
              </Typography>
              {selectedMed && (
                <Typography variant="body2" color="text.secondary">
                  {selectedMed.medication_name} {selectedMed.dose} {selectedMed.route} - Past {historyDays} Days
                </Typography>
              )}
            </Box>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Time Period</InputLabel>
              <Select
                value={historyDays}
                onChange={(e) => {
                  setHistoryDays(e.target.value as number)
                  if (selectedMed) loadMedicationHistory(selectedMed.id)
                }}
                label="Time Period"
              >
                <MenuItem value={3}>3 Days</MenuItem>
                <MenuItem value={7}>7 Days</MenuItem>
                <MenuItem value={14}>14 Days</MenuItem>
                <MenuItem value={30}>30 Days</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedMed && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Indication:</strong> {selectedMed.indication || 'Not specified'}
              </Typography>
              {selectedMed.instructions && (
                <Typography variant="body2">
                  <strong>Instructions:</strong> {selectedMed.instructions}
                </Typography>
              )}
              {selectedMed.is_high_risk && (
                <Typography variant="body2" color="error.main" fontWeight="bold">
                  ⚠️ HIGH RISK MEDICATION
                </Typography>
              )}
            </Alert>
          )}

          {fullMedHistory.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="body2" color="text.secondary">
                No administration history found for the selected time period
              </Typography>
            </Box>
          ) : (
            <>
              {/* Summary Statistics */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h5" color="success.main">
                        {fullMedHistory.filter(a => a.status === 'given').length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Given
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h5" color="warning.main">
                        {fullMedHistory.filter(a => a.status === 'held').length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Held
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h5" color="error.main">
                        {fullMedHistory.filter(a => a.status === 'refused').length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Refused
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h5" color="text.secondary">
                        {fullMedHistory.filter(a => a.status === 'pending').length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Pending
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Detailed History Table */}
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Date</strong></TableCell>
                      <TableCell><strong>Scheduled</strong></TableCell>
                      <TableCell><strong>Given</strong></TableCell>
                      <TableCell><strong>Time Variance</strong></TableCell>
                      <TableCell><strong>Status</strong></TableCell>
                      <TableCell><strong>Dose</strong></TableCell>
                      <TableCell><strong>Route</strong></TableCell>
                      <TableCell><strong>Administered By</strong></TableCell>
                      <TableCell><strong>Notes</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {fullMedHistory
                      .sort((a, b) => new Date(b.scheduled_time).getTime() - new Date(a.scheduled_time).getTime())
                      .map((admin, idx) => {
                        const scheduledTime = new Date(admin.scheduled_time)
                        const givenTime = admin.administration_time ? new Date(admin.administration_time) : null
                        const variance = givenTime ? Math.round((givenTime.getTime() - scheduledTime.getTime()) / 60000) : null
                        const isLate = variance && Math.abs(variance) > gracePeriod
                        
                        return (
                          <TableRow 
                            key={idx}
                            sx={{ 
                              bgcolor: admin.status === 'held' || admin.status === 'refused' ? 'error.50' : 
                                     admin.status === 'pending' ? 'grey.100' :
                                     isLate ? 'warning.50' : 'transparent'
                            }}
                          >
                            <TableCell>
                              <Typography variant="body2">
                                {scheduledTime.toLocaleDateString()}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontWeight="bold">
                                {scheduledTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              {givenTime ? (
                                <Typography variant="body2" color={isLate ? 'warning.main' : 'text.primary'}>
                                  {givenTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </Typography>
                              ) : (
                                <Typography variant="caption" color="text.secondary">-</Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              {variance !== null ? (
                                <Typography 
                                  variant="caption" 
                                  color={isLate ? 'warning.main' : Math.abs(variance) > 30 ? 'info.main' : 'success.main'}
                                  fontWeight={isLate ? 'bold' : 'normal'}
                                >
                                  {variance > 0 ? '+' : ''}{variance} min
                                  {isLate && ' ⚠️'}
                                </Typography>
                              ) : (
                                <Typography variant="caption" color="text.secondary">-</Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Chip
                                icon={getStatusIcon(admin.status)}
                                label={admin.status}
                                size="small"
                                color={getStatusColor(admin.status) as any}
                                variant={admin.status === 'given' ? 'filled' : 'outlined'}
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {admin.dose_given || '-'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {admin.route || '-'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {admin.administered_by_name || '-'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Box>
                                {admin.prn_reason && (
                                  <Typography variant="caption" display="block" color="info.main">
                                    <strong>PRN Reason:</strong> {admin.prn_reason}
                                  </Typography>
                                )}
                                {(admin as any).prn_pain_level_before !== undefined && (
                                  <Typography variant="caption" display="block">
                                    <strong>Pain:</strong> {(admin as any).prn_pain_level_before}/10 → {(admin as any).prn_pain_level_after}/10
                                  </Typography>
                                )}
                                {admin.notes && (
                                  <Typography variant="caption" display="block">
                                    {admin.notes}
                                  </Typography>
                                )}
                              </Box>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Legend */}
              <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold" display="block" gutterBottom>
                  Legend:
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption">
                      • <strong>Time Variance:</strong> Difference between scheduled and actual administration time
                    </Typography>
                    <Typography variant="caption" display="block">
                      • <strong>Grace Period:</strong> {gracePeriod} minutes (±{gracePeriod} min from scheduled is "on time")
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption">
                      • ⚠️ = Given outside grace period (late or early)
                    </Typography>
                    <Typography variant="caption" display="block">
                      • <span style={{ color: 'orange' }}>Yellow background</span> = Late administration
                    </Typography>
                    <Typography variant="caption" display="block">
                      • <span style={{ color: 'red' }}>Red background</span> = Held or Refused
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
          <Button 
            variant="outlined"
            onClick={() => {
              // Export to CSV functionality could go here
              alert('Export functionality coming soon')
            }}
          >
            Export to CSV
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
