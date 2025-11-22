import { useState, useEffect } from 'react'
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material'
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Close as CloseIcon,
  Medication as MedicationIcon,
  LocalHospital as HospitalIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { adrApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import type { ADRAlert } from '../types'

export default function ADRAlerts() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [alerts, setAlerts] = useState<ADRAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedAlert, setSelectedAlert] = useState<ADRAlert | null>(null)
  const [acknowledgeNote, setAcknowledgeNote] = useState('')
  const [statusFilter, setStatusFilter] = useState<'NEW' | 'ACKNOWLEDGED' | 'all'>('NEW')

  useEffect(() => {
    loadAlerts()
  }, [statusFilter])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      setError('')
      const params = statusFilter === 'all' ? {} : { status: statusFilter }
      const response = await adrApi.getActiveAlerts(params)
      const alertData = response.data?.data || response.data || []
      setAlerts(Array.isArray(alertData) ? alertData : [])
    } catch (err: any) {
      console.error('ADR Alert Error:', err)
      setError(err.response?.data?.message || 'Failed to load ADR alerts')
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }

  const handleAcknowledge = async (alertId: number) => {
    try {
      await adrApi.acknowledgeAlert(alertId, { notes: acknowledgeNote })
      setSelectedAlert(null)
      setAcknowledgeNote('')
      loadAlerts()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to acknowledge alert')
    }
  }

  const getSeverityColor = (severity?: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'error'
      case 'major':
        return 'warning'
      case 'moderate':
        return 'info'
      case 'minor':
        return 'default'
      default:
        return 'default'
    }
  }

  const getSeverityIcon = (severity?: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return <ErrorIcon />
      case 'major':
        return <WarningIcon />
      case 'moderate':
        return <InfoIcon />
      case 'minor':
        return <CheckCircleIcon />
      default:
        return <InfoIcon />
    }
  }

  const getConfidenceColor = (confidence?: string) => {
    switch (confidence?.toLowerCase()) {
      case 'high':
        return 'error'
      case 'medium':
        return 'warning'
      case 'low':
        return 'info'
      default:
        return 'default'
    }
  }

  const getStatusColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'new':
        return 'error'
      case 'acknowledged':
        return 'success'
      case 'resolved':
        return 'default'
      default:
        return 'default'
    }
  }

  const filteredAlerts = alerts.filter((alert) => {
    if (statusFilter === 'all') return true
    return alert.status?.toUpperCase() === statusFilter
  })

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  const handleResetAcknowledgments = async () => {
    if (!confirm('⚠️ This will reset ALL acknowledgments and return all alerts to NEW status.\n\nAll staff will need to re-acknowledge alerts.\n\nContinue?')) {
      return
    }
    
    try {
      await adrApi.resetAcknowledgments()
      alert('✅ All acknowledgments have been reset')
      loadAlerts()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to reset acknowledgments')
    }
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Medication Safety Alerts
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Important: What to watch for when giving or seeing someone take medications
          </Typography>
        </Box>
        {user?.role === 'Admin' && (
          <Button
            variant="outlined"
            color="warning"
            size="small"
            onClick={handleResetAcknowledgments}
            sx={{ mt: 1 }}
          >
            Reset All Acknowledgments (Admin)
          </Button>
        )}
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>For everyone involved in patient care:</strong> These alerts help nurses, caregivers, and family members 
          know what symptoms or changes to watch for with each medication. If you notice any of these signs, 
          notify the nurse or healthcare provider immediately.
        </Typography>
      </Alert>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Status Filter Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={statusFilter} onChange={(_, v) => setStatusFilter(v)}>
          <Tab label={`Active (${alerts.filter(a => a.status === 'NEW').length})`} value="NEW" />
          <Tab label={`Reviewed (${alerts.filter(a => a.status === 'ACKNOWLEDGED').length})`} value="ACKNOWLEDGED" />
          <Tab label={`All (${alerts.length})`} value="all" />
        </Tabs>
      </Box>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: 'error.light' }}>
            <CardContent>
              <Typography variant="h4">{alerts.filter(a => a.severity === 'critical').length}</Typography>
              <Typography variant="body2">Critical</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: 'warning.light' }}>
            <CardContent>
              <Typography variant="h4">{alerts.filter(a => a.severity === 'major').length}</Typography>
              <Typography variant="body2">Major</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: 'info.light' }}>
            <CardContent>
              <Typography variant="h4">{alerts.filter(a => a.status === 'new').length}</Typography>
              <Typography variant="body2">Unacknowledged</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card sx={{ bgcolor: 'success.light' }}>
            <CardContent>
              <Typography variant="h4">{alerts.filter(a => a.requires_immediate_action).length}</Typography>
              <Typography variant="body2">Urgent Action</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alert Cards */}
      {filteredAlerts.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              No alerts found for the selected filter
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {filteredAlerts.map((alert) => (
            <Grid item xs={12} key={alert.id}>
              <Card 
                sx={{ 
                  borderLeft: 6, 
                  borderColor: alert.requires_immediate_action ? 'error.main' : 'warning.main',
                  '&:hover': { boxShadow: 6 }
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        {getSeverityIcon(alert.severity)}
                        <Typography variant="h6">
                          {alert.suspected_reaction}
                        </Typography>
                        {alert.requires_immediate_action && (
                          <Chip label="URGENT" color="error" size="small" />
                        )}
                        {alert.is_hospice_patient && (
                          <Chip icon={<HospitalIcon />} label="Hospice" size="small" />
                        )}
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Patient: <strong>{alert.patient_name || alert.patient?.full_name || 'N/A'}</strong> | 
                        MRN: <strong>{alert.patient?.medical_record_number || 'N/A'}</strong> | 
                        <Button 
                          size="small" 
                          onClick={() => navigate(`/patients/${alert.patient_id}`)}
                          sx={{ ml: 1 }}
                        >
                          View Chart
                        </Button>
                      </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      <Chip 
                        label={alert.severity?.toUpperCase() || 'UNKNOWN'} 
                        color={getSeverityColor(alert.severity) as any} 
                        size="small" 
                      />
                      <Chip 
                        label={`${alert.confidence_level?.toUpperCase() || 'UNKNOWN'} Confidence`} 
                        color={getConfidenceColor(alert.confidence_level) as any}
                        size="small" 
                      />
                      <Chip 
                        label={alert.status?.toUpperCase() || 'UNKNOWN'} 
                        color={getStatusColor(alert.status) as any}
                        size="small" 
                      />
                    </Box>
                  </Box>

                  <Alert severity={alert.requires_immediate_action ? 'error' : 'warning'} sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Alert Summary:</strong> {alert.alert_summary}
                    </Typography>
                  </Alert>

                  {alert.medication && (
                    <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        <MedicationIcon sx={{ fontSize: 16, verticalAlign: 'middle', mr: 0.5 }} />
                        Suspected Medication:
                      </Typography>
                      <Typography variant="body2">
                        {alert.medication.medication_name} - {alert.medication.dose} {alert.medication.route}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Started: {alert.days_since_medication_start || 0} days ago
                      </Typography>
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button 
                      variant="contained" 
                      onClick={() => setSelectedAlert(alert)}
                      size="small"
                    >
                      See What To Watch For
                    </Button>
                    <Button 
                      variant="outlined"
                      onClick={() => navigate(`/patients/${alert.patient_id}`)}
                      size="small"
                    >
                      View Patient Details
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Alert Detail Dialog */}
      <Dialog 
        open={!!selectedAlert} 
        onClose={() => setSelectedAlert(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedAlert && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">
                  {selectedAlert.suspected_reaction} - What To Watch For
                </Typography>
                <IconButton onClick={() => setSelectedAlert(null)} size="small">
                  <CloseIcon />
                </IconButton>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Important information for everyone involved in care
              </Typography>
            </DialogTitle>
            <DialogContent dividers>
              {/* Patient Info */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Patient Information</strong>
                </Typography>
                <Typography variant="body2">
                  {selectedAlert.patient?.full_name} (MRN: {selectedAlert.patient?.medical_record_number})
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Age: {selectedAlert.patient?.age} | Gender: {selectedAlert.patient?.gender}
                </Typography>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Alert Details */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Alert Details</strong>
                </Typography>
                <Alert severity={selectedAlert.requires_immediate_action ? 'error' : 'warning'} sx={{ mb: 2 }}>
                  {selectedAlert.alert_summary}
                </Alert>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Severity</Typography>
                    <Typography variant="body2">{selectedAlert.severity?.toUpperCase()}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Confidence Level</Typography>
                    <Typography variant="body2">{selectedAlert.confidence_level?.toUpperCase()} ({(selectedAlert.correlation_score || 0) * 100}%)</Typography>
                  </Grid>
                </Grid>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Clinical Findings */}
              {(selectedAlert.matching_symptoms?.length || selectedAlert.matching_vital_signs?.length) && (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      <strong>Clinical Findings</strong>
                    </Typography>
                    {selectedAlert.matching_symptoms && selectedAlert.matching_symptoms.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" color="text.secondary">Matching Symptoms:</Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                          {selectedAlert.matching_symptoms.map((symptom, idx) => (
                            <Chip key={idx} label={symptom.replace(/_/g, ' ')} size="small" color="warning" />
                          ))}
                        </Box>
                      </Box>
                    )}
                    {selectedAlert.matching_vital_signs && selectedAlert.matching_vital_signs.length > 0 && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">Vital Sign Changes:</Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                          {selectedAlert.matching_vital_signs.map((vital, idx) => (
                            <Chip key={idx} label={vital.replace(/_/g, ' ')} size="small" color="error" />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Box>
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {/* Nursing Interventions */}
              {selectedAlert.nursing_interventions && selectedAlert.nursing_interventions.length > 0 && (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        <strong>What To Do If You See These Signs</strong>
                      </Typography>
                      <Typography variant="caption">
                        Important actions - notify nurse or healthcare provider if you observe these symptoms
                      </Typography>
                    </Alert>
                    <List dense>
                      {selectedAlert.nursing_interventions.map((intervention, idx) => (
                        <ListItem key={idx}>
                          <ListItemText 
                            primary={`${idx + 1}. ${intervention}`}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {/* Provider Notification */}
              {selectedAlert.provider_notification_needed && (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Alert severity="error" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        <strong>{selectedAlert.provider_notification_urgency} Provider Notification Required</strong>
                      </Typography>
                    </Alert>
                    <Typography variant="body2" paragraph>
                      <strong>Notification Guidance:</strong>
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {selectedAlert.provider_notification_guidance}
                    </Typography>
                    {selectedAlert.suggested_provider_orders && selectedAlert.suggested_provider_orders.length > 0 && (
                      <>
                        <Typography variant="body2" gutterBottom>
                          <strong>Suggested Provider Orders:</strong>
                        </Typography>
                        <List dense>
                          {selectedAlert.suggested_provider_orders.map((order, idx) => (
                            <ListItem key={idx}>
                              <ListItemText 
                                primary={`• ${order}`}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}
                  </Box>
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {/* Hospice Considerations */}
              {selectedAlert.is_hospice_patient && selectedAlert.hospice_comfort_focus && (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Alert severity="info" icon={<HospitalIcon />} sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        <strong>Hospice Patient - Comfort-Focused Care</strong>
                      </Typography>
                    </Alert>
                    <Typography variant="body2">
                      {selectedAlert.hospice_comfort_focus}
                    </Typography>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                </>
              )}

              {/* Escalation Guidance */}
              {selectedAlert.escalation_guidance && (
                <Box sx={{ mb: 3 }}>
                  <Alert severity="warning">
                    <Typography variant="subtitle2" gutterBottom>
                      <strong>Escalation Guidance</strong>
                    </Typography>
                    <Typography variant="body2">
                      {selectedAlert.escalation_guidance}
                    </Typography>
                  </Alert>
                </Box>
              )}

              {/* Acknowledgment */}
              {selectedAlert.status === 'NEW' && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Acknowledge Alert (For Licensed Nurses Only)
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Nursing Notes (required)"
                    placeholder="Document what you observed, actions taken, and any provider notification..."
                    value={acknowledgeNote}
                    onChange={(e) => setAcknowledgeNote(e.target.value)}
                  />
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedAlert(null)}>Close</Button>
              {selectedAlert.status === 'NEW' && user?.role && ['RN', 'LPN', 'Nurse'].includes(user.role) && (
                <Button 
                  variant="contained" 
                  onClick={() => handleAcknowledge(selectedAlert.id)}
                  disabled={!acknowledgeNote.trim()}
                >
                  Acknowledge & Document (Nurse)
                </Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  )
}
