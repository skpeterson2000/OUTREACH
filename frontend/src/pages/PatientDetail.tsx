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
  const [patient, setPatient] = useState<Patient | null>(null)
  const [medications, setMedications] = useState<Medication[]>([])
  const [visits, setVisits] = useState<Visit[]>([])
  const [alerts, setAlerts] = useState<ADRAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tabValue, setTabValue] = useState(0)

  useEffect(() => {
    console.log('PatientDetail mounted, id:', id)
    if (id) {
      loadPatientData(parseInt(id))
    }
  }, [id])

  const loadPatientData = async (patientId: number) => {
    try {
      console.log('Loading patient data for ID:', patientId)
      setLoading(true)
      setError('')
      
      const [patientRes, medsRes, alertsRes] = await Promise.all([
        patientsApi.getById(patientId),
        medicationsApi.getByPatient(patientId),
        adrApi.getActiveAlerts({ patient_id: patientId }),
      ])

      console.log('Patient data loaded:', patientRes.data)
      setPatient(patientRes.data.data)
      // Medications endpoint returns { status, data, count } directly
      setMedications(Array.isArray(medsRes.data.data) ? medsRes.data.data : (medsRes.data as any) || [])
      setAlerts(alertsRes.data.data || alertsRes.data || [])
    } catch (err: any) {
      console.error('Error loading patient data:', err)
      setError(err.response?.data?.message || 'Failed to load patient data')
    } finally {
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

      {/* Active Alerts Banner */}
      {alerts.length > 0 && (
        <Alert severity="error" icon={<WarningIcon />} sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight="medium">
            ⚠️ {alerts.length} medication safety alert{alerts.length > 1 ? 's' : ''} requiring attention - 
            <Button size="small" color="inherit" onClick={() => setTabValue(2)} sx={{ ml: 1 }}>
              View Details
            </Button>
          </Typography>
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
              {patient.secondary_diagnoses && patient.secondary_diagnoses.length > 0
                ? patient.secondary_diagnoses.join(', ')
                : 'None'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="caption" color="text.secondary">
              Allergies
            </Typography>
            <Typography variant="body2" color={patient.allergies && patient.allergies.length > 0 ? 'error.main' : 'text.primary'}>
              {patient.allergies && patient.allergies.length > 0
                ? patient.allergies.join(', ')
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
                    <Button variant="outlined" size="small">
                      Acknowledge
                    </Button>
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
    </Container>
  )
}
