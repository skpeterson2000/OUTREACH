import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  LocalHospital as HospiceIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { patientsApi } from '../services/api'
import type { Patient } from '../types'

export default function PatientList() {
  const navigate = useNavigate()
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('active')

  useEffect(() => {
    loadPatients()
  }, [statusFilter])

  const loadPatients = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await patientsApi.getAll({ status: statusFilter })
      // Backend returns { status, data, count } structure
      setPatients(response.data.data || [])
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load patients')
    } finally {
      setLoading(false)
    }
  }

  const filteredPatients = patients.filter((patient) => {
    const query = searchQuery.toLowerCase()
    return (
      patient.first_name?.toLowerCase().includes(query) ||
      patient.last_name?.toLowerCase().includes(query) ||
      patient.medical_record_number?.toLowerCase().includes(query) ||
      patient.primary_diagnosis?.toLowerCase().includes(query)
    )
  })

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'success'
      case 'discharged':
        return 'default'
      case 'pending':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getRiskLevel = (patient: Patient) => {
    const fallRisk = patient.fall_risk_score || 0
    const bradenScore = patient.braden_score || 23
    
    if (fallRisk >= 8 || bradenScore <= 12) return { level: 'HIGH', color: 'error' }
    if (fallRisk >= 5 || bradenScore <= 18) return { level: 'MODERATE', color: 'warning' }
    return { level: 'LOW', color: 'success' }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Patient Management
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage patient records and view clinical information
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search by name, MRN, or diagnosis..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="discharged">Discharged</MenuItem>
                <MenuItem value="pending">Pending Admission</MenuItem>
                <MenuItem value="all">All</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="contained"
              onClick={() => navigate('/patients/new')}
              sx={{ height: '56px' }}
            >
              Add New Patient
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Patient List */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'grey.100' }}>
                <TableCell>MRN</TableCell>
                <TableCell>Patient Name</TableCell>
                <TableCell>Age</TableCell>
                <TableCell>Primary Diagnosis</TableCell>
                <TableCell>Admission Date</TableCell>
                <TableCell>Risk Level</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredPatients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 8 }}>
                    <Typography variant="body2" color="text.secondary">
                      No patients found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredPatients.map((patient) => {
                  const risk = getRiskLevel(patient)
                  return (
                    <TableRow
                      key={patient.id}
                      hover
                      sx={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/patients/${patient.id}`)}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {patient.medical_record_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2">
                            {patient.first_name} {patient.last_name}
                          </Typography>
                          {patient.is_hospice && (
                            <HospiceIcon fontSize="small" color="secondary" />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{patient.age || 'N/A'}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 250 }}>
                          {patient.primary_diagnosis || 'Not specified'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(patient.admission_date)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={risk.level}
                          color={risk.color as any}
                          size="small"
                          icon={
                            risk.level === 'HIGH' ? (
                              <WarningIcon fontSize="small" />
                            ) : undefined
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={patient.status}
                          color={getStatusColor(patient.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/patients/${patient.id}`)
                          }}
                        >
                          <ViewIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredPatients.length} of {patients.length} patients
        </Typography>
      </Box>
    </Container>
  )
}
