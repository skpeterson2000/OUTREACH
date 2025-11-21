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
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Grid,
} from '@mui/material'
import {
  Medication as MedicationIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { patientsApi } from '../services/api'
import type { Patient } from '../types'

export default function MAROverview() {
  const navigate = useNavigate()
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadPatients()
  }, [])

  const loadPatients = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await patientsApi.getAll({ status: 'active' })
      setPatients(response.data.data || [])
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load patients')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Medication Administration Records (MAR)
        </Typography>
        <Typography variant="body2" color="text.secondary">
          View and manage medication administration for all active patients
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="primary">
                {patients.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Patients
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="success.main">
                {patients.reduce((sum, p) => sum + (p.active_medications_count || 0), 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Active Medications
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="warning.main">
                {patients.filter(p => p.is_hospice).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Hospice Patients (Special Considerations)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Patient MAR Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Patient</TableCell>
              <TableCell>MRN</TableCell>
              <TableCell>Active Medications</TableCell>
              <TableCell>Special Considerations</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {patients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography variant="body2" color="text.secondary" py={3}>
                    No active patients found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              patients.map((patient) => (
                <TableRow key={patient.id} hover>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <PersonIcon fontSize="small" color="action" />
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {patient.full_name || `${patient.first_name} ${patient.last_name}`}
                        </Typography>
                        {patient.primary_diagnosis && (
                          <Typography variant="caption" color="text.secondary">
                            {patient.primary_diagnosis}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {patient.medical_record_number}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={<MedicationIcon />}
                      label={`${patient.active_medications_count || 0} Active`}
                      size="small"
                      color={patient.active_medications_count ? 'primary' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {patient.is_hospice && (
                        <Chip label="Hospice" size="small" color="info" />
                      )}
                      {patient.fall_risk && (
                        <Chip icon={<WarningIcon />} label="Fall Risk" size="small" color="warning" />
                      )}
                      {patient.allergies && patient.allergies.length > 0 && patient.allergies[0] !== 'NKDA' && (
                        <Chip icon={<WarningIcon />} label="Allergies" size="small" color="error" />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<MedicationIcon />}
                      onClick={() => navigate(`/patients/${patient.id}/mar`)}
                    >
                      Open MAR
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  )
}
