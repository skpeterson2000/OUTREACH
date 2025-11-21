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
  const patientId = parseInt(id || '0')

  const [medications, setMedications] = useState<MARMedication[]>([])
  const [adrAlerts, setAdrAlerts] = useState<ADRAlert[]>([])
  const [overdueMeds, setOverdueMeds] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedMed, setExpandedMed] = useState<number | null>(null)
  const [adminDialogOpen, setAdminDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedMed, setSelectedMed] = useState<MARMedication | null>(null)
  const [tabValue, setTabValue] = useState(0)
  const [gracePeriod, setGracePeriod] = useState(60) // Default 60 minutes
  const [editForm, setEditForm] = useState({
    time_of_day: '',
    special_instructions: '',
  })

  // Administration form state
  const [adminForm, setAdminForm] = useState({
    status: 'given',
    dose_given: '',
    route: '',
    notes: '',
    prn_reason: '',
  })

  useEffect(() => {
    loadMARData()
    loadADRAlerts()
    loadOverdueMeds()
    // Set up polling for overdue medications every 5 minutes
    const interval = setInterval(loadOverdueMeds, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [patientId])

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

  const handleAdministerClick = (med: MARMedication) => {
    setSelectedMed(med)
    setAdminForm({
      status: 'given',
      dose_given: med.dose || '',
      route: med.route || 'PO',
      notes: '',
      prn_reason: med.is_prn ? '' : 'N/A',
    })
    setAdminDialogOpen(true)
  }

  const handleAdministerSubmit = async () => {
    if (!selectedMed) return

    try {
      await medicationsApi.administerMedication(patientId, selectedMed.id, {
        ...adminForm,
        scheduled_time: new Date().toISOString(),
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

    return (
      <>
        <TableRow key={med.id} hover>
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
              {med.status === 'held' ? (
                <Button
                  size="small"
                  variant="outlined"
                  color="success"
                  onClick={() => handleResumeMedication(med.id)}
                >
                  Unhold
                </Button>
              ) : (
                <>
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<MedicationIcon />}
                    onClick={() => handleAdministerClick(med)}
                  >
                    Give Now
                  </Button>
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
                      <Typography variant="subtitle2" gutterBottom color="primary">
                        Today's Administration History
                      </Typography>
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
    </Box>
  )
}
