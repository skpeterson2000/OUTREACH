import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import {
  Typography,
  Button,
  Container,
  Grid,
  Paper,
  Card,
  CardContent,
  CardActions,
  Box,
  Alert,
  Chip,
  CircularProgress,
} from '@mui/material'
import {
  Error as ErrorIcon,
} from '@mui/icons-material'
import { useAuthStore } from '../store/authStore'
import { adrApi } from '../services/api'
import type { ADRAlert } from '../types'

export default function Dashboard() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [adrAlerts, setAdrAlerts] = useState<ADRAlert[]>([])
  const [loadingAlerts, setLoadingAlerts] = useState(true)

  useEffect(() => {
    loadADRAlerts()
  }, [])

  const loadADRAlerts = async () => {
    try {
      setLoadingAlerts(true)
      const response = await adrApi.getActiveAlerts({ status: 'NEW' })
      const alerts = response.data?.data || response.data || []
      setAdrAlerts(Array.isArray(alerts) ? alerts : [])
    } catch (err) {
      console.error('Failed to load ADR alerts:', err)
      setAdrAlerts([]) // Set empty array on error
    } finally {
      setLoadingAlerts(false)
    }
  }

  const modules = [
    { title: 'Patients', description: 'Manage patient records and demographics', path: '/patients', enabled: true },
    { title: 'MAR', description: 'Medication administration records', path: '/mar', enabled: true },
    { title: 'ADR Alerts', description: 'Medication safety alerts - what to watch for', path: '/adr', enabled: true },
    { title: 'Visits', description: 'Schedule and document visits', path: '/visits', enabled: false },
    { title: 'Reconciliation', description: 'Medication reconciliation', path: '/reconciliation', enabled: false },
    { title: 'Reports', description: 'Clinical reports and analytics', path: '/reports', enabled: false },
  ]

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Welcome, {user?.first_name}!
      </Typography>

      <Box sx={{ mb: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
        <Typography variant="body2" color="info.contrastText">
          💡 <strong>Quick Access:</strong> Click "Patients" in the navigation bar above to view all patients
        </Typography>
      </Box>

      {/* ADR Alerts Widget */}
      {loadingAlerts ? (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress size={24} />
            </Box>
          </CardContent>
        </Card>
      ) : adrAlerts.length > 0 && (
        <Alert 
          severity="error" 
          icon={<ErrorIcon />}
          sx={{ mb: 3 }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={() => navigate('/adr')}
              variant="outlined"
            >
              View All Alerts
            </Button>
          }
        >
          <Typography variant="subtitle2" gutterBottom>
            <strong>{adrAlerts.length} Unacknowledged ADR Alert{adrAlerts.length !== 1 ? 's' : ''} Requiring Attention</strong>
          </Typography>
          {adrAlerts.slice(0, 3).map((alert) => (
            <Box key={alert.id} sx={{ mt: 1, mb: 1 }}>
              <Typography variant="body2">
                <strong>{alert.patient?.full_name}</strong> - {alert.suspected_reaction}
                {alert.requires_immediate_action && (
                  <Chip label="URGENT" color="error" size="small" sx={{ ml: 1 }} />
                )}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {alert.alert_summary?.substring(0, 100)}...
              </Typography>
            </Box>
          ))}
          {adrAlerts.length > 3 && (
            <Typography variant="caption" color="text.secondary">
              ...and {adrAlerts.length - 3} more alert{adrAlerts.length - 3 !== 1 ? 's' : ''}
            </Typography>
          )}
        </Alert>
      )}

      <Grid container spacing={3}>
        {modules.map((module) => (
          <Grid item xs={12} sm={6} md={4} key={module.title}>
            <Card sx={{ opacity: module.enabled ? 1 : 0.6, height: '100%' }}>
              <CardContent>
                <Typography variant="h5" component="div" gutterBottom>
                  {module.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {module.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  size="small" 
                  onClick={() => navigate(module.path)}
                  disabled={!module.enabled}
                  variant={module.enabled ? 'contained' : 'outlined'}
                >
                  {module.enabled ? 'Open' : 'Coming Soon'}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 3, mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Quick Stats
        </Typography>
        <Typography variant="body1">
          • Active Patients: Coming soon
        </Typography>
        <Typography variant="body1">
          • Today's Visits: Coming soon
        </Typography>
        <Typography variant="body1">
          • Pending Medications: Coming soon
        </Typography>
      </Paper>
    </Container>
  )
}
