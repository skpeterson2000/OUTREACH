import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Tabs,
  Tab,
  Chip,
  CircularProgress,
  Alert,
  Grid,
  Divider,
  IconButton,
} from '@mui/material'
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
} from '@mui/icons-material'
import { carePlansApi } from '../services/carePlans'
import { useAuthStore } from '../store/authStore'
import { canManageCarePlans } from '../utils/permissions'
import type { CarePlan } from '../types/carePlan'
import InterventionsList from '../components/care-plans/InterventionsList'
import OrdersList from '../components/care-plans/OrdersList'
import TasksList from '../components/care-plans/TasksList'

interface TabPanelProps {
  children?: React.ReactNode
  value: number
  index: number
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index} style={{ paddingTop: 24 }}>
      {value === index && children}
    </div>
  )
}

export default function CarePlanDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [carePlan, setCarePlan] = useState<CarePlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState(0)

  useEffect(() => {
    if (id) {
      loadCarePlan()
    }
  }, [id])

  const loadCarePlan = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await carePlansApi.getById(parseInt(id!))
      setCarePlan(response.data.data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load care plan')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success'
      case 'completed':
        return 'default'
      case 'discontinued':
        return 'error'
      default:
        return 'default'
    }
  }

  if (loading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    )
  }

  if (error || !carePlan) {
    return (
      <Container>
        <Box sx={{ py: 4 }}>
          <Alert severity="error">{error || 'Care plan not found'}</Alert>
          <Button
            startIcon={<BackIcon />}
            onClick={() => navigate('/care-plans')}
            sx={{ mt: 2 }}
          >
            Back to Care Plans
          </Button>
        </Box>
      </Container>
    )
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
          <Box sx={{ flex: 1 }}>
            <Button
              startIcon={<BackIcon />}
              onClick={() => navigate('/care-plans')}
              sx={{ mb: 2 }}
            >
              Back to Care Plans
            </Button>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Typography variant="h4">{carePlan.plan_name}</Typography>
              <Chip label={carePlan.status} color={getStatusColor(carePlan.status)} />
              <Chip label={carePlan.plan_type} variant="outlined" />
            </Box>
          </Box>
          {user && canManageCarePlans(user.role) && carePlan.status === 'active' && (
            <IconButton onClick={() => navigate(`/care-plans/${id}/edit`)}>
              <EditIcon />
            </IconButton>
          )}
        </Box>

        {/* Care Plan Details */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3}>
            {/* Care Goals */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Care Goals
              </Typography>
              <Typography variant="body1">{carePlan.care_goals}</Typography>
            </Grid>

            {/* Clinical Summary */}
            {carePlan.clinical_summary && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Clinical Summary
                </Typography>
                <Typography variant="body2">{carePlan.clinical_summary}</Typography>
              </Grid>
            )}

            <Grid item xs={12}>
              <Divider />
            </Grid>

            {/* Dates */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Start Date</Typography>
              <Typography>{formatDate(carePlan.start_date)}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Expected End Date</Typography>
              <Typography>{formatDate(carePlan.expected_end_date)}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Last Review</Typography>
              <Typography>{formatDate(carePlan.last_review_date)}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Next Review</Typography>
              <Typography>{formatDate(carePlan.next_review_date)}</Typography>
            </Grid>

            {/* Physician Info */}
            {carePlan.ordering_physician && (
              <>
                <Grid item xs={12}>
                  <Divider />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" color="text.secondary">Ordering Physician</Typography>
                  <Typography>{carePlan.ordering_physician}</Typography>
                </Grid>
                {carePlan.physician_npi && (
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="text.secondary">NPI</Typography>
                    <Typography>{carePlan.physician_npi}</Typography>
                  </Grid>
                )}
                {carePlan.physician_phone && (
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="text.secondary">Phone</Typography>
                    <Typography>{carePlan.physician_phone}</Typography>
                  </Grid>
                )}
              </>
            )}

            {/* Discharge Plan */}
            {carePlan.discharge_plan && (
              <>
                <Grid item xs={12}>
                  <Divider />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Discharge Plan
                  </Typography>
                  <Typography variant="body2">{carePlan.discharge_plan}</Typography>
                </Grid>
              </>
            )}
          </Grid>
        </Paper>

        {/* Tabs for Interventions, Orders, Tasks */}
        <Paper>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            <Tab 
              label={`Interventions ${carePlan.interventions ? `(${carePlan.interventions.length})` : ''}`} 
            />
            <Tab 
              label={`Physician Orders ${carePlan.orders ? `(${carePlan.orders.length})` : ''}`} 
            />
            <Tab 
              label={`Assistance Tasks ${carePlan.tasks ? `(${carePlan.tasks.length})` : ''}`} 
            />
          </Tabs>

          <TabPanel value={activeTab} index={0}>
            <InterventionsList 
              carePlanId={carePlan.id} 
              interventions={carePlan.interventions || []}
              onRefresh={loadCarePlan}
            />
          </TabPanel>

          <TabPanel value={activeTab} index={1}>
            <OrdersList 
              carePlanId={carePlan.id} 
              orders={carePlan.orders || []}
              onRefresh={loadCarePlan}
            />
          </TabPanel>

          <TabPanel value={activeTab} index={2}>
            <TasksList 
              carePlanId={carePlan.id} 
              tasks={carePlan.tasks || []}
              onRefresh={loadCarePlan}
            />
          </TabPanel>
        </Paper>
      </Box>
    </Container>
  )
}
