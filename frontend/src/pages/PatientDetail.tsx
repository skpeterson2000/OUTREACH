import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Chip,
  Button,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  IconButton,
  Alert,
  CircularProgress,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  LocalHospital as HospiceIcon,
  Warning as WarningIcon,
  Medication as MedicationIcon,
  Assignment as VisitIcon,
  Notifications as AlertIcon,
} from '@mui/icons-material'
import { patientsApi, medicationsApi, visitsApi, adrApi } from '../services/api'
import type { Patient, Medication, Visit, ADRAlert } from '../types'
import { useAuthStore } from '../store/authStore'
import { canAcknowledgeADRAlerts } from '../utils/permissions'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

export default function PatientDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  
  const [patient, setPatient] = useState<Patient | null>(null)
  const [medications, setMedications] = useState<Medication[]>([])
  const [visits, setVisits] = useState<Visit[]>([])
  const [alerts, setAlerts] = useState<ADRAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tabValue, setTabValue] = useState(0)
  const [acknowledgeDialogOpen, setAcknowledgeDialogOpen] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState<ADRAlert | null>(null)
  const [acknowledgmentForm, setAcknowledgmentForm] = useState({
    action: 'ACKNOWLEDGED' as 'ACKNOWLEDGED' | 'HOLD_MEDICATION',
    verified_reaction_awareness: false,
    verified_monitoring_parameters: false,
    verified_escalation_criteria: false,
    notes: '',
    monitoring_plan: '',
    hold_reason: '',
    hold_duration: '',
    provider_notified: false,
  })

  useEffect(() => {
    console.log('🚀 PatientDetail: Component mounted')
    console.log('🆔 PatientDetail: URL id parameter:', id)
    console.log('🌐 PatientDetail: Current URL:', window.location.href)
    
    if (!id) {
      console.error('❌ PatientDetail: No id parameter found in URL!')
      setError('Patient ID not found in URL')
      setLoading(false)
      return
    }
    
    const patientId = parseInt(id)
    if (isNaN(patientId)) {
      console.error('❌ PatientDetail: Invalid patient ID:', id)
      setError('Invalid patient ID')
      setLoading(false)
      return
    }
    
    console.log('✅ PatientDetail: Valid patient ID, loading data for:', patientId)
    loadPatientData(patientId)
  }, [id])

  const handleAcknowledgeAlert = (alert: ADRAlert) => {
    setSelectedAlert(alert)
    setAcknowledgmentForm({
      action: 'ACKNOWLEDGED',
      verified_reaction_awareness: false,
      verified_monitoring_parameters: false,
      verified_escalation_criteria: false,
      notes: '',
      monitoring_plan: '',
      hold_reason: '',
      hold_duration: '',
      provider_notified: false,
    })
    setAcknowledgeDialogOpen(true)
  }

  const handleAcknowledgeSubmit = async () => {
    console.log('🔔 ACKNOWLEDGE SUBMIT - Starting...')
    console.log('   Selected Alert:', selectedAlert)
    console.log('   Current User:', user)
    console.log('   Acknowledgment Form:', acknowledgmentForm)
    
    if (!selectedAlert) {
      console.error('❌ No alert selected')
      return
    }
    
    // Validate required checkboxes
    if (!acknowledgmentForm.verified_reaction_awareness || 
        !acknowledgmentForm.verified_monitoring_parameters || 
        !acknowledgmentForm.verified_escalation_criteria) {
      console.warn('⚠️ Not all safety verifications checked')
      alert('You must complete all three safety verifications before acknowledging this alert.')
      return
    }

    // Validate HOLD_MEDICATION specific fields
    if (acknowledgmentForm.action === 'HOLD_MEDICATION') {
      if (!acknowledgmentForm.hold_reason || !acknowledgmentForm.hold_duration) {
        alert('When holding a medication, you must provide a reason and duration.')
        return
      }
      if (!acknowledgmentForm.provider_notified) {
        alert('You must notify the provider when holding a medication due to an ADR alert.')
        return
      }
    }

    const payload = {
      action: acknowledgmentForm.action,
      verified_reaction_awareness: acknowledgmentForm.verified_reaction_awareness,
      verified_monitoring_parameters: acknowledgmentForm.verified_monitoring_parameters,
      verified_escalation_criteria: acknowledgmentForm.verified_escalation_criteria,
      notes: acknowledgmentForm.notes || `Acknowledged by ${user?.first_name} ${user?.last_name} (${user?.role})`,
      monitoring_plan: acknowledgmentForm.monitoring_plan || undefined,
      hold_reason: acknowledgmentForm.action === 'HOLD_MEDICATION' ? acknowledgmentForm.hold_reason : undefined,
      hold_duration: acknowledgmentForm.action === 'HOLD_MEDICATION' ? acknowledgmentForm.hold_duration : undefined,
      provider_notified: acknowledgmentForm.action === 'HOLD_MEDICATION' ? acknowledgmentForm.provider_notified : undefined,
    }
    console.log('📤 Sending acknowledgment payload:', payload)

    try {
      console.log('📡 Calling API: acknowledgeAlert(', selectedAlert.id, ')')
      const response = await adrApi.acknowledgeAlert(selectedAlert.id, payload)
      console.log('✅ API Response:', response)
      
      // Close dialog first to prevent UI blocking
      setAcknowledgeDialogOpen(false)
      
      // Show success message
      if (acknowledgmentForm.action === 'HOLD_MEDICATION') {
        alert(`✅ Alert acknowledged and medication HELD.\n\n⚠️ This medication is now on hold for ${acknowledgmentForm.hold_duration}.\n\nProvider has been notified. This acknowledgment is recorded in the patient's medical record.`)
      } else {
        alert(`✅ Alert acknowledged. This acknowledgment is recorded in the patient's medical record.\n\n⚠️ REMINDER: You must verify monitoring parameters before EACH medication administration.\n\n⏰ This acknowledgment expires after 12 hours (next shift).`)
      }
      
      // Refresh patient data
      console.log('🔄 Refreshing patient data...')
      if (id) {
        const patientId = parseInt(id)
        if (!isNaN(patientId)) {
          try {
            await loadPatientData(patientId)
            console.log('✅ Patient data refreshed successfully')
          } catch (refreshError) {
            console.error('❌ Failed to refresh patient data:', refreshError)
            // Don't show error to user since acknowledgment succeeded
          }
        }
      }
    } catch (error: any) {
      console.error('❌ ACKNOWLEDGE FAILED:')
      console.error('   Error:', error)
      console.error('   Response:', error.response)
      console.error('   Status:', error.response?.status)
      console.error('   Data:', error.response?.data)
      
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Failed to acknowledge alert'
      alert(`❌ Error: ${errorMsg}\n\nStatus: ${error.response?.status || 'unknown'}\nCheck console for details.`)
    }
  }

  const loadPatientData = async (patientId: number) => {
    try {
      console.log('🔍 PatientDetail: Loading patient data for ID:', patientId)
      setLoading(true)
      setError('')
      
      console.log('📡 PatientDetail: Fetching patient data...')
      const [patientRes, medsRes, alertsRes] = await Promise.all([
        patientsApi.getById(patientId),
        medicationsApi.getByPatient(patientId),
        adrApi.getActiveAlerts({ patient_id: patientId }),
      ])

      console.log('✅ PatientDetail: Raw patient response:', patientRes)
      console.log('✅ PatientDetail: Raw meds response:', medsRes)
      console.log('✅ PatientDetail: Raw alerts response:', alertsRes)
      
      const patientData = patientRes.data.data || patientRes.data
      console.log('👤 PatientDetail: Extracted patient data:', patientData)
      
      if (!patientData) {
        console.error('❌ PatientDetail: No patient data in response!')
        setError('Patient data not found')
        return
      }
      
      setPatient(patientData)
      // Medications endpoint returns { status, data, count } directly
      const medsData = Array.isArray(medsRes.data.data) ? medsRes.data.data : (medsRes.data as any) || []
      console.log('💊 PatientDetail: Setting medications:', medsData)
      setMedications(medsData)
      
      const alertsData = alertsRes.data.data || alertsRes.data || []
      console.log('⚠️ PatientDetail: Setting alerts:', alertsData)
      setAlerts(alertsData)
      
      console.log('✨ PatientDetail: All data loaded successfully')
    } catch (err: any) {
      console.error('❌ PatientDetail: Error loading patient data:', err)
      console.error('❌ PatientDetail: Error response:', err.response)
      console.error('❌ PatientDetail: Error message:', err.message)
      setError(err.response?.data?.message || err.message || 'Failed to load patient data')
    } finally {
      console.log('🏁 PatientDetail: Setting loading to false')
      setLoading(false)
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString()
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error || !patient) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error || 'Patient not found'}</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/patients')} sx={{ mt: 2 }}>
          Back to Patients
        </Button>
      </Container>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/patients')}>
            <BackIcon />
          </IconButton>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h4">
                {patient.first_name} {patient.last_name}
              </Typography>
              {patient.is_hospice && <HospiceIcon color="secondary" />}
            </Box>
            <Typography variant="body2" color="text.secondary">
              MRN: {patient.medical_record_number} • {patient.age} years old • {patient.gender}
            </Typography>
          </Box>
        </Box>
        <Button startIcon={<EditIcon />} variant="outlined">
          Edit Patient
        </Button>
      </Box>

      {/* Status Summary Card */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Today's Care Overview
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h4" color="primary">12</Typography>
                    <Typography variant="caption">Medications Due</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h4" color="success.main">8</Typography>
                    <Typography variant="caption">Given On Time</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h4" color="warning.main">2</Typography>
                    <Typography variant="caption">Due Soon</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h4" color="error.main">{alerts.length}</Typography>
                    <Typography variant="caption">Active Alerts</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            
            {/* Quick Status */}
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>Current Status</Typography>
              <Chip label={patient.status?.toUpperCase()} color={patient.status === 'active' ? 'success' : 'default'} size="small" sx={{ mr: 1 }} />
              {patient.is_hospice && <Chip label="HOSPICE CARE" color="secondary" size="small" sx={{ mr: 1 }} />}
              <Chip label={patient.code_status || 'Not Specified'} variant="outlined" size="small" />
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Button 
                variant="contained" 
                startIcon={<MedicationIcon />} 
                fullWidth
                onClick={() => navigate(`/patients/${id}/mar`)}
              >
                Open MAR
              </Button>
              <Button variant="outlined" startIcon={<VisitIcon />} fullWidth disabled>
                Document Visit (Coming Soon)
              </Button>
              <Button variant="outlined" startIcon={<AlertIcon />} fullWidth onClick={() => setTabValue(2)}>
                View ADR Alerts ({alerts.length})
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Active Alerts Banner - CRITICAL SAFETY WARNING */}
      {alerts.length > 0 && (
        <Alert 
          severity="error" 
          icon={<WarningIcon />} 
          sx={{ 
            mb: 3,
            border: '3px solid',
            borderColor: 'error.main',
            backgroundColor: 'error.light',
            '& .MuiAlert-message': { width: '100%' }
          }}
        >
          <Box>
            <Typography variant="h6" fontWeight="bold" color="error.dark" gutterBottom>
              🚨 MEDICATION SAFETY ALERT - ACTION REQUIRED
            </Typography>
            <Typography variant="body1" fontWeight="medium" gutterBottom>
              {alerts.length} active adverse drug reaction alert{alerts.length > 1 ? 's' : ''} for this patient
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>YOU MUST ACKNOWLEDGE ALL ALERTS BEFORE ADMINISTERING MEDICATIONS</strong>
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button 
                variant="contained" 
                color="error" 
                size="large"
                onClick={() => setTabValue(1)}
                sx={{ fontWeight: 'bold' }}
              >
                REVIEW & ACKNOWLEDGE ALERTS NOW
              </Button>
              <Typography variant="caption" sx={{ alignSelf: 'center', fontStyle: 'italic' }}>
                This is required at the start of each shift and before giving any medications to this patient
              </Typography>
            </Box>
          </Box>
        </Alert>
      )}

      {/* Demographics Card */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Demographics
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Date of Birth
            </Typography>
            <Typography variant="body2">{formatDate(patient.date_of_birth)}</Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Admission Date
            </Typography>
            <Typography variant="body2">{formatDate(patient.admission_date)}</Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Status
            </Typography>
            <Box sx={{ mt: 0.5 }}>
              <Chip label={patient.status} color="success" size="small" />
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Code Status
            </Typography>
            <Typography variant="body2">{patient.code_status || 'Not specified'}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="caption" color="text.secondary">
              Address
            </Typography>
            <Typography variant="body2">
              {patient.address_line1 ? (
                <>
                  {patient.address_line1}
                  <br />
                  {patient.city}, {patient.state} {patient.zip_code}
                </>
              ) : (
                'Not specified'
              )}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Phone
            </Typography>
            <Typography variant="body2">{patient.phone_primary || 'N/A'}</Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Emergency Contact
            </Typography>
            <Typography variant="body2">
              {patient.emergency_contact_name || 'N/A'}
              {patient.emergency_contact_phone && (
                <>
                  <br />
                  {patient.emergency_contact_phone}
                </>
              )}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Clinical Information */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Clinical Information
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="caption" color="text.secondary">
              Primary Diagnosis
            </Typography>
            <Typography variant="body2">{patient.primary_diagnosis || 'Not specified'}</Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="caption" color="text.secondary">
              Secondary Diagnoses
            </Typography>
            <Typography variant="body2">
              {patient.secondary_diagnoses && (Array.isArray(patient.secondary_diagnoses) ? patient.secondary_diagnoses.length > 0 : patient.secondary_diagnoses.length > 0)
                ? (Array.isArray(patient.secondary_diagnoses) ? patient.secondary_diagnoses.join(', ') : patient.secondary_diagnoses)
                : 'None'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="caption" color="text.secondary">
              Allergies
            </Typography>
            <Typography variant="body2" color={patient.allergies && patient.allergies !== 'NKDA' && patient.allergies.length > 0 ? 'error.main' : 'text.primary'}>
              {patient.allergies && patient.allergies !== 'NKDA' && patient.allergies.length > 0
                ? (Array.isArray(patient.allergies) ? patient.allergies.join(', ') : patient.allergies)
                : 'No known allergies'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Fall Risk Score
            </Typography>
            <Typography variant="body2">
              {patient.fall_risk_score || 'Not assessed'}{' '}
              {patient.fall_risk_score && patient.fall_risk_score >= 8 && (
                <Chip label="HIGH" color="error" size="small" />
              )}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Braden Score
            </Typography>
            <Typography variant="body2">
              {patient.braden_score || 'Not assessed'}{' '}
              {patient.braden_score && patient.braden_score <= 12 && (
                <Chip label="HIGH RISK" color="error" size="small" />
              )}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={`Medications (${medications.filter(m => m.is_active).length})`} icon={<MedicationIcon />} iconPosition="start" />
          <Tab label={`ADR Alerts (${alerts.length})`} icon={<AlertIcon />} iconPosition="start" />
          <Tab label="Visits" icon={<VisitIcon />} iconPosition="start" />
        </Tabs>

        {/* Medications Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Active Medications</Typography>
            <Button
              variant="contained"
              size="small"
              onClick={() => navigate(`/patients/${id}/mar`)}
            >
              View MAR
            </Button>
          </Box>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Medication</TableCell>
                  <TableCell>Dose</TableCell>
                  <TableCell>Route</TableCell>
                  <TableCell>Frequency</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Start Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {medications.filter(m => m.is_active).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No active medications
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  medications
                    .filter(m => m.is_active)
                    .map((med) => (
                      <TableRow key={med.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {med.medication_name}
                          </Typography>
                          {med.generic_name && (
                            <Typography variant="caption" color="text.secondary">
                              ({med.generic_name})
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>{med.dose}</TableCell>
                        <TableCell>{med.route}</TableCell>
                        <TableCell>{med.frequency}</TableCell>
                        <TableCell>
                          {med.is_prn ? (
                            <Chip label="PRN" color="warning" size="small" />
                          ) : (
                            <Chip label="Scheduled" size="small" />
                          )}
                          {med.is_controlled_substance && (
                            <Chip label="Controlled" color="error" size="small" sx={{ ml: 0.5 }} />
                          )}
                        </TableCell>
                        <TableCell>{formatDate(med.start_date)}</TableCell>
                      </TableRow>
                    ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* ADR Alerts Tab */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Active ADR Alerts
          </Typography>
          {alerts.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
              No active ADR alerts
            </Typography>
          ) : (
            alerts.map((alert) => (
              <Card key={alert.id} sx={{ mb: 2, border: '1px solid', borderColor: 'warning.main' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Box>
                      <Typography variant="h6" color="error">
                        {alert.suspected_reaction}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Alert ID: {alert.id} • Created {formatDateTime(alert.created_at)}
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Chip label={alert.confidence_level} color="warning" size="small" sx={{ mb: 0.5 }} />
                      <br />
                      <Chip label={alert.severity} color="error" size="small" />
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" gutterBottom>
                    {alert.alert_summary}
                  </Typography>

                  <Divider sx={{ my: 2 }} />

                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="caption" color="text.secondary">
                        Medication
                      </Typography>
                      <Typography variant="body2">
                        {alert.medication?.medication_name} {alert.medication?.dose}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="caption" color="text.secondary">
                        Correlation Score
                      </Typography>
                      <Typography variant="body2">{(alert.correlation_score * 100).toFixed(0)}%</Typography>
                    </Grid>
                  </Grid>

                  {alert.nursing_interventions.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        Recommended Nursing Interventions:
                      </Typography>
                      <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                        {alert.nursing_interventions.map((intervention, idx) => (
                          <li key={idx}>
                            <Typography variant="body2">{intervention}</Typography>
                          </li>
                        ))}
                      </ul>
                    </Box>
                  )}

                  <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => navigate(`/adr/alerts/${alert.id}`)}
                    >
                      View Details
                    </Button>
                    {canAcknowledgeADRAlerts(user?.role) && (
                      <Button 
                        variant="outlined" 
                        size="small"
                        color="warning"
                        onClick={() => handleAcknowledgeAlert(alert)}
                      >
                        Acknowledge
                      </Button>
                    )}
                  </Box>
                </CardContent>
              </Card>
            ))
          )}
        </TabPanel>

        {/* Visits Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Visit History
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Coming soon...
          </Typography>
        </TabPanel>
      </Paper>

      {/* ADR Alert Acknowledgment Dialog */}
      <Dialog open={acknowledgeDialogOpen} onClose={() => setAcknowledgeDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <WarningIcon color="error" />
            <Box>
              <Typography variant="h6">Acknowledge Medication Safety Alert</Typography>
              {selectedAlert && (
                <Typography variant="caption" color="text.secondary">
                  Alert #{selectedAlert.id}: {selectedAlert.suspected_reaction}
                </Typography>
              )}
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <>
              <Alert severity="error" sx={{ mb: 3 }}>
                <Typography variant="body2" fontWeight="bold">
                  ⚠️ PATIENT SAFETY REQUIREMENT
                </Typography>
                <Typography variant="caption">
                  This acknowledgment creates a legal record that you have read and understood this medication safety alert.
                  You must verify monitoring parameters before EACH medication administration.
                </Typography>
              </Alert>

              {/* Alert Summary */}
              <Paper sx={{ p: 2, mb: 3, bgcolor: 'error.50', border: '1px solid', borderColor: 'error.main' }}>
                <Typography variant="subtitle2" color="error" gutterBottom>
                  Medication Safety Alert Summary:
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Medication:</strong> {selectedAlert.medication?.medication_name} {selectedAlert.medication?.dose}
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Suspected Reaction:</strong> {selectedAlert.suspected_reaction}
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Severity:</strong> <Chip label={selectedAlert.severity} color="error" size="small" />
                </Typography>
                <Typography variant="body2">
                  {selectedAlert.alert_summary}
                </Typography>
              </Paper>

              {/* Monitoring Parameters */}
              {selectedAlert.monitoring_parameters && selectedAlert.monitoring_parameters.length > 0 && (
                <Paper sx={{ p: 2, mb: 3, bgcolor: 'warning.50' }}>
                  <Typography variant="subtitle2" color="warning.dark" gutterBottom>
                    📋 Required Monitoring Parameters:
                  </Typography>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    {selectedAlert.monitoring_parameters.map((param, idx) => (
                      <li key={idx}>
                        <Typography variant="body2">{param}</Typography>
                      </li>
                    ))}
                  </ul>
                </Paper>
              )}

              {/* Nursing Interventions */}
              {selectedAlert.nursing_interventions && selectedAlert.nursing_interventions.length > 0 && (
                <Paper sx={{ p: 2, mb: 3, bgcolor: 'info.50' }}>
                  <Typography variant="subtitle2" color="info.dark" gutterBottom>
                    🩺 Required Nursing Interventions:
                  </Typography>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    {selectedAlert.nursing_interventions.map((intervention, idx) => (
                      <li key={idx}>
                        <Typography variant="body2">{intervention}</Typography>
                      </li>
                    ))}
                  </ul>
                </Paper>
              )}

              <Divider sx={{ my: 3 }} />

              {/* Action Selection */}
              <Typography variant="subtitle2" gutterBottom color="error">
                🔔 Select Your Action:
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Box 
                  sx={{ 
                    p: 2, 
                    mb: 1,
                    border: '2px solid', 
                    borderColor: acknowledgmentForm.action === 'ACKNOWLEDGED' ? 'primary.main' : 'grey.300',
                    borderRadius: 1,
                    bgcolor: acknowledgmentForm.action === 'ACKNOWLEDGED' ? 'primary.50' : 'background.paper',
                    cursor: 'pointer',
                  }}
                  onClick={() => setAcknowledgmentForm({ ...acknowledgmentForm, action: 'ACKNOWLEDGED' })}
                >
                  <Box display="flex" alignItems="center" gap={1}>
                    <input
                      type="radio"
                      checked={acknowledgmentForm.action === 'ACKNOWLEDGED'}
                      onChange={() => setAcknowledgmentForm({ ...acknowledgmentForm, action: 'ACKNOWLEDGED' })}
                      style={{ cursor: 'pointer' }}
                    />
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        ACKNOWLEDGE - Continue with Enhanced Monitoring
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        I will continue administering this medication with increased vigilance and monitoring
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                <Box 
                  sx={{ 
                    p: 2, 
                    border: '2px solid', 
                    borderColor: acknowledgmentForm.action === 'HOLD_MEDICATION' ? 'warning.main' : 'grey.300',
                    borderRadius: 1,
                    bgcolor: acknowledgmentForm.action === 'HOLD_MEDICATION' ? 'warning.50' : 'background.paper',
                    cursor: 'pointer',
                  }}
                  onClick={() => setAcknowledgmentForm({ ...acknowledgmentForm, action: 'HOLD_MEDICATION' })}
                >
                  <Box display="flex" alignItems="center" gap={1}>
                    <input
                      type="radio"
                      checked={acknowledgmentForm.action === 'HOLD_MEDICATION'}
                      onChange={() => setAcknowledgmentForm({ ...acknowledgmentForm, action: 'HOLD_MEDICATION' })}
                      style={{ cursor: 'pointer' }}
                    />
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        HOLD MEDICATION - Stop Administration
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        I will hold this medication and notify the provider immediately
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Box>

              {/* Hold Medication Fields */}
              {acknowledgmentForm.action === 'HOLD_MEDICATION' && (
                <Paper sx={{ p: 2, mb: 3, bgcolor: 'warning.50', border: '1px solid', borderColor: 'warning.main' }}>
                  <Typography variant="subtitle2" color="warning.dark" gutterBottom>
                    ⚠️ Hold Medication - Additional Information Required:
                  </Typography>
                  
                  <TextField
                    label="Reason for Holding Medication *"
                    fullWidth
                    multiline
                    rows={2}
                    value={acknowledgmentForm.hold_reason}
                    onChange={(e) => setAcknowledgmentForm({ ...acknowledgmentForm, hold_reason: e.target.value })}
                    placeholder="Explain why you are holding this medication (e.g., symptoms worsening, vital signs out of range)..."
                    sx={{ mt: 2 }}
                    required
                  />

                  <TextField
                    label="Hold Duration *"
                    fullWidth
                    value={acknowledgmentForm.hold_duration}
                    onChange={(e) => setAcknowledgmentForm({ ...acknowledgmentForm, hold_duration: e.target.value })}
                    placeholder="e.g., 24 hours, until provider assessment, pending lab results"
                    sx={{ mt: 2 }}
                    required
                  />

                  <Box sx={{ mt: 2, p: 1.5, border: '1px solid', borderColor: 'warning.main', borderRadius: 1 }}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <input
                        type="checkbox"
                        checked={acknowledgmentForm.provider_notified}
                        onChange={(e) => setAcknowledgmentForm({ ...acknowledgmentForm, provider_notified: e.target.checked })}
                        style={{ cursor: 'pointer' }}
                      />
                      <Typography variant="body2" fontWeight="bold">
                        I have notified (or will immediately notify) the provider about holding this medication *
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              )}

              {/* Required Safety Verifications */}
              <Typography variant="subtitle2" gutterBottom color="error">
                ✓ Required Safety Verifications (All Must Be Checked):
              </Typography>

              <Box sx={{ 
                p: 2, 
                mb: 2,
                border: '2px solid', 
                borderColor: acknowledgmentForm.verified_reaction_awareness ? 'success.main' : 'grey.300',
                borderRadius: 1,
                bgcolor: acknowledgmentForm.verified_reaction_awareness ? 'success.50' : 'grey.50',
              }}>
                <Box display="flex" alignItems="flex-start" gap={1}>
                  <input
                    type="checkbox"
                    checked={acknowledgmentForm.verified_reaction_awareness}
                    onChange={(e) => setAcknowledgmentForm({ ...acknowledgmentForm, verified_reaction_awareness: e.target.checked })}
                    style={{ marginTop: '4px', cursor: 'pointer' }}
                  />
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      I understand the suspected adverse drug reaction and its severity
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      I have carefully reviewed the suspected reaction ({selectedAlert?.suspected_reaction}), 
                      its severity level ({selectedAlert?.severity}), and patient-specific symptoms.
                    </Typography>
                  </Box>
                </Box>
              </Box>

              <Box sx={{ 
                p: 2, 
                mb: 2,
                border: '2px solid', 
                borderColor: acknowledgmentForm.verified_monitoring_parameters ? 'success.main' : 'grey.300',
                borderRadius: 1,
                bgcolor: acknowledgmentForm.verified_monitoring_parameters ? 'success.50' : 'grey.50',
              }}>
                <Box display="flex" alignItems="flex-start" gap={1}>
                  <input
                    type="checkbox"
                    checked={acknowledgmentForm.verified_monitoring_parameters}
                    onChange={(e) => setAcknowledgmentForm({ ...acknowledgmentForm, verified_monitoring_parameters: e.target.checked })}
                    style={{ marginTop: '4px', cursor: 'pointer' }}
                  />
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      I will verify ALL monitoring parameters before EACH medication administration
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      I understand that I must check the required monitoring parameters (vital signs, symptoms, labs) 
                      BEFORE giving this medication each time, not just once per shift.
                    </Typography>
                  </Box>
                </Box>
              </Box>

              <Box sx={{ 
                p: 2, 
                mb: 2,
                border: '2px solid', 
                borderColor: acknowledgmentForm.verified_escalation_criteria ? 'success.main' : 'grey.300',
                borderRadius: 1,
                bgcolor: acknowledgmentForm.verified_escalation_criteria ? 'success.50' : 'grey.50',
              }}>
                <Box display="flex" alignItems="flex-start" gap={1}>
                  <input
                    type="checkbox"
                    checked={acknowledgmentForm.verified_escalation_criteria}
                    onChange={(e) => setAcknowledgmentForm({ ...acknowledgmentForm, verified_escalation_criteria: e.target.checked })}
                    style={{ marginTop: '4px', cursor: 'pointer' }}
                  />
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      I know when to escalate concerns to the provider
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      I understand what changes in patient condition require immediate provider notification 
                      and will not hesitate to escalate if monitoring parameters are abnormal.
                    </Typography>
                  </Box>
                </Box>
              </Box>

              <TextField
                label="Monitoring Plan (Recommended)"
                fullWidth
                multiline
                rows={2}
                value={acknowledgmentForm.monitoring_plan}
                onChange={(e) => setAcknowledgmentForm({ ...acknowledgmentForm, monitoring_plan: e.target.value })}
                placeholder="Describe your specific plan for monitoring this patient (e.g., check vitals q4h, assess for symptoms before each dose)..."
                sx={{ mt: 2 }}
              />

              <TextField
                label="Additional Notes (Optional)"
                fullWidth
                multiline
                rows={2}
                value={acknowledgmentForm.notes}
                onChange={(e) => setAcknowledgmentForm({ ...acknowledgmentForm, notes: e.target.value })}
                placeholder="Document any additional concerns, questions, or actions you plan to take..."
                sx={{ mt: 2 }}
              />

              <Alert severity="warning" icon={<Info />} sx={{ mt: 3 }}>
                <Typography variant="caption">
                  <strong>Legal Notice:</strong> This acknowledgment is part of the patient's permanent medical record.
                  Your digital signature (username and timestamp) will be recorded. By clicking "I Acknowledge and Accept Responsibility",
                  you certify that you understand your obligations under this safety alert.
                </Typography>
              </Alert>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAcknowledgeDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleAcknowledgeSubmit} 
            variant="contained"
            color={acknowledgmentForm.action === 'HOLD_MEDICATION' ? 'warning' : 'error'}
            disabled={
              !acknowledgmentForm.verified_reaction_awareness || 
              !acknowledgmentForm.verified_monitoring_parameters || 
              !acknowledgmentForm.verified_escalation_criteria ||
              (acknowledgmentForm.action === 'HOLD_MEDICATION' && 
                (!acknowledgmentForm.hold_reason || !acknowledgmentForm.hold_duration || !acknowledgmentForm.provider_notified))
            }
          >
            {acknowledgmentForm.action === 'HOLD_MEDICATION' 
              ? '⚠️ HOLD MEDICATION AND NOTIFY PROVIDER' 
              : '✓ I ACKNOWLEDGE AND ACCEPT RESPONSIBILITY'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
