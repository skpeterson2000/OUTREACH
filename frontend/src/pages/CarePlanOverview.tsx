import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  AssignmentTurnedIn as CarePlanIcon,
  Person as PersonIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material'
import { carePlansApi } from '../services/carePlans'
import { useAuthStore } from '../store/authStore'
import { canManageCarePlans } from '../utils/permissions'
import type { CarePlan } from '../types/carePlan'

export default function CarePlanOverview() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [carePlans, setCarePlans] = useState<CarePlan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('active')

  useEffect(() => {
    loadCarePlans()
  }, [statusFilter])

  const loadCarePlans = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await carePlansApi.getAll({ 
        status: statusFilter === 'all' ? undefined : statusFilter 
      })
      setCarePlans(response.data.data || [])
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load care plans')
    } finally {
      setLoading(false)
    }
  }

  const filteredPlans = carePlans.filter((plan) => {
    const query = searchQuery.toLowerCase()
    return (
      plan.plan_name?.toLowerCase().includes(query) ||
      plan.plan_type?.toLowerCase().includes(query) ||
      plan.care_goals?.toLowerCase().includes(query)
    )
  })

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

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString()
  }

  const isOverdueForReview = (reviewDate?: string) => {
    if (!reviewDate) return false
    return new Date(reviewDate) < new Date()
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CarePlanIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Typography variant="h4" component="h1">
              Care Plans
            </Typography>
          </Box>
          {user && canManageCarePlans(user.role) && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate('/care-plans/new')}
            >
              Create Care Plan
            </Button>
          )}
        </Box>

        {/* Filters */}
        <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search care plans..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ flex: 1, minWidth: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              label="Status"
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="discontinued">Discontinued</MenuItem>
              <MenuItem value="all">All</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Loading State */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Error State */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Care Plans Grid */}
        {!loading && !error && (
          <>
            {filteredPlans.length === 0 ? (
              <Alert severity="info">
                No care plans found. {user && canManageCarePlans(user.role) && 'Click "Create Care Plan" to get started.'}
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {filteredPlans.map((plan) => (
                  <Grid item xs={12} md={6} lg={4} key={plan.id}>
                    <Card 
                      sx={{ 
                        height: '100%', 
                        display: 'flex', 
                        flexDirection: 'column',
                        border: isOverdueForReview(plan.next_review_date) ? 2 : 0,
                        borderColor: 'warning.main',
                      }}
                    >
                      <CardContent sx={{ flexGrow: 1 }}>
                        {/* Status & Type */}
                        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                          <Chip
                            label={plan.status}
                            color={getStatusColor(plan.status)}
                            size="small"
                          />
                          <Chip
                            label={plan.plan_type}
                            variant="outlined"
                            size="small"
                          />
                          {isOverdueForReview(plan.next_review_date) && (
                            <Chip
                              label="Review Due"
                              color="warning"
                              size="small"
                            />
                          )}
                        </Box>

                        {/* Plan Name */}
                        <Typography variant="h6" gutterBottom>
                          {plan.plan_name}
                        </Typography>

                        {/* Patient Info */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <PersonIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            Patient ID: {plan.patient_id}
                          </Typography>
                        </Box>

                        {/* Care Goals */}
                        <Typography 
                          variant="body2" 
                          color="text.secondary"
                          sx={{ 
                            mb: 2,
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                          }}
                        >
                          {plan.care_goals}
                        </Typography>

                        {/* Dates */}
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <CalendarIcon fontSize="small" color="action" />
                            <Typography variant="caption" color="text.secondary">
                              Start: {formatDate(plan.start_date)}
                            </Typography>
                          </Box>
                          {plan.next_review_date && (
                            <Typography 
                              variant="caption" 
                              color={isOverdueForReview(plan.next_review_date) ? 'warning.main' : 'text.secondary'}
                              sx={{ ml: 4 }}
                            >
                              Next Review: {formatDate(plan.next_review_date)}
                            </Typography>
                          )}
                        </Box>

                        {/* Physician */}
                        {plan.ordering_physician && (
                          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                            Physician: {plan.ordering_physician}
                          </Typography>
                        )}
                      </CardContent>

                      <CardActions>
                        <Button
                          size="small"
                          onClick={() => navigate(`/care-plans/${plan.id}`)}
                        >
                          View Details
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </>
        )}
      </Box>
    </Container>
  )
}
