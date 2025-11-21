import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  TextField,
  Alert,
  Card,
  CardContent,
  Grid,
  Button,
  CircularProgress,
} from '@mui/material'
import {
  AccessTime,
  Warning,
  Person as PersonIcon,
  Medication as MedicationIcon,
} from '@mui/icons-material'
import { medicationsApi } from '../services/api'

interface OverdueMedication {
  administration_id: number
  medication_id: number
  medication_name: string
  dose: string
  route: string
  patient_id: number
  patient_name: string
  patient_room?: string
  scheduled_time: string
  minutes_overdue: number
  is_high_risk: boolean
  is_controlled_substance: boolean
}

export default function OverdueMedications() {
  const navigate = useNavigate()
  const [overdueMeds, setOverdueMeds] = useState<OverdueMedication[]>([])
  const [loading, setLoading] = useState(true)
  const [gracePeriod, setGracePeriod] = useState(60)

  useEffect(() => {
    loadOverdueMeds()
    // Poll every 2 minutes
    const interval = setInterval(loadOverdueMeds, 2 * 60 * 1000)
    return () => clearInterval(interval)
  }, [gracePeriod])

  const loadOverdueMeds = async () => {
    try {
      setLoading(true)
      const response = await medicationsApi.getOverdueMedications({
        grace_period_minutes: gracePeriod,
      })
      setOverdueMeds(response.data.data || [])
    } catch (error) {
      console.error('Failed to load overdue medications:', error)
    } finally {
      setLoading(false)
    }
  }

  const highRiskCount = overdueMeds.filter(m => m.is_high_risk).length
  const controlledCount = overdueMeds.filter(m => m.is_controlled_substance).length
  const criticalCount = overdueMeds.filter(m => m.minutes_overdue > 120).length

  if (loading && overdueMeds.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Overdue Medications - Facility Wide
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Last updated: {new Date().toLocaleTimeString()}
          </Typography>
        </Box>
        <TextField
          label="Grace Period (minutes)"
          type="number"
          size="small"
          value={gracePeriod}
          onChange={(e) => setGracePeriod(parseInt(e.target.value) || 60)}
          sx={{ width: 180 }}
        />
      </Box>

      {overdueMeds.length === 0 ? (
        <Alert severity="success" icon={<AccessTime />}>
          <Typography variant="body2" fontWeight="bold">
            ✅ All medications administered on time!
          </Typography>
          <Typography variant="caption">
            No medications overdue (grace period: {gracePeriod} minutes)
          </Typography>
        </Alert>
      ) : (
        <>
          {/* Stats Cards */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={3}>
              <Card sx={{ bgcolor: 'error.light' }}>
                <CardContent>
                  <Typography variant="h4" color="error.dark">
                    {overdueMeds.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Overdue
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="h4" color="error.main">
                    {criticalCount}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Critical (&gt;2 hours)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="h4" color="warning.main">
                    {highRiskCount}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Risk Meds
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="h4" color="warning.main">
                    {controlledCount}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Controlled Substances
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Critical Alert */}
          {criticalCount > 0 && (
            <Alert severity="error" icon={<Warning />} sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="bold">
                🚨 {criticalCount} CRITICAL: Medications overdue by more than 2 hours
              </Typography>
            </Alert>
          )}

          {/* Overdue Table */}
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Patient</TableCell>
                  <TableCell>Medication</TableCell>
                  <TableCell>Scheduled Time</TableCell>
                  <TableCell>Overdue By</TableCell>
                  <TableCell>Risk Level</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {overdueMeds.map((med) => (
                  <TableRow 
                    key={med.administration_id}
                    sx={{ 
                      bgcolor: med.minutes_overdue > 120 ? 'error.light' : 'inherit',
                      '&:hover': { bgcolor: 'action.hover' }
                    }}
                  >
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <PersonIcon fontSize="small" color="action" />
                        <Box>
                          <Typography variant="body2" fontWeight="bold">
                            {med.patient_name}
                          </Typography>
                          {med.patient_room && (
                            <Typography variant="caption" color="text.secondary">
                              Room {med.patient_room}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <MedicationIcon fontSize="small" color="primary" />
                        <Box>
                          <Typography variant="body2" fontWeight="bold">
                            {med.medication_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {med.dose} {med.route}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(med.scheduled_time).toLocaleTimeString()}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(med.scheduled_time).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={`${med.minutes_overdue} minutes`}
                        size="small"
                        color={med.minutes_overdue > 120 ? 'error' : 'warning'}
                      />
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={0.5} flexWrap="wrap">
                        {med.is_high_risk && (
                          <Chip label="High Risk" size="small" color="error" variant="outlined" />
                        )}
                        {med.is_controlled_substance && (
                          <Chip label="Controlled" size="small" color="warning" variant="outlined" />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        size="small"
                        variant="contained"
                        onClick={() => navigate(`/patients/${med.patient_id}/mar`)}
                      >
                        Open MAR
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Container>
  )
}
