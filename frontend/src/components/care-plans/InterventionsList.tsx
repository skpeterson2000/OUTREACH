import { useState } from 'react'
import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Alert,
} from '@mui/material'
import {
  Add as AddIcon,
  CheckCircle as CompleteIcon,
  Edit as EditIcon,
  History as HistoryIcon,
} from '@mui/icons-material'
import { interventionsApi } from '../../services/carePlans'
import { useAuthStore } from '../../store/authStore'
import { canManageCarePlans, canCompleteNursingIntervention } from '../../utils/permissions'
import type { NursingIntervention, CompleteInterventionRequest } from '../../types/carePlan'

interface Props {
  carePlanId: number
  interventions: NursingIntervention[]
  onRefresh: () => void
}

export default function InterventionsList({ carePlanId, interventions, onRefresh }: Props) {
  const { user } = useAuthStore()
  const [completeDialog, setCompleteDialog] = useState<{ open: boolean; intervention: NursingIntervention | null }>({
    open: false,
    intervention: null,
  })
  const [completionData, setCompletionData] = useState<CompleteInterventionRequest>({
    status: 'completed',
    completion_notes: '',
    patient_response: '',
    outcome_achieved: '',
    requires_follow_up: false,
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleCompleteIntervention = async () => {
    if (!completeDialog.intervention) return

    try {
      setSubmitting(true)
      setError('')
      await interventionsApi.complete(completeDialog.intervention.id, completionData)
      setCompleteDialog({ open: false, intervention: null })
      setCompletionData({
        status: 'completed',
        completion_notes: '',
        patient_response: '',
        outcome_achieved: '',
        requires_follow_up: false,
      })
      onRefresh()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to complete intervention')
    } finally {
      setSubmitting(false)
    }
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

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'stat':
        return 'error'
      case 'urgent':
        return 'warning'
      case 'routine':
        return 'default'
      default:
        return 'default'
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Nursing Interventions</Typography>
        {user && canManageCarePlans(user.role) && (
          <Button startIcon={<AddIcon />} variant="contained" size="small">
            Add Intervention
          </Button>
        )}
      </Box>

      {/* Interventions Table */}
      {interventions.length === 0 ? (
        <Alert severity="info">No interventions added yet.</Alert>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Assigned</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {interventions.map((intervention) => (
                <TableRow key={intervention.id}>
                  <TableCell>
                    <Chip label={intervention.status} color={getStatusColor(intervention.status)} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip label={intervention.priority} color={getPriorityColor(intervention.priority)} size="small" />
                  </TableCell>
                  <TableCell>{intervention.intervention_type}</TableCell>
                  <TableCell>
                    <Typography variant="body2">{intervention.intervention_name}</Typography>
                    {intervention.requires_rn && (
                      <Chip label="RN Required" size="small" color="primary" sx={{ mt: 0.5 }} />
                    )}
                  </TableCell>
                  <TableCell>{intervention.frequency || 'As needed'}</TableCell>
                  <TableCell>{intervention.assigned_role || 'Unassigned'}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {user && 
                        canCompleteNursingIntervention(user.role, intervention.requires_rn) &&
                        intervention.status === 'active' && (
                        <IconButton
                          size="small"
                          onClick={() => {
                            setCompleteDialog({ open: true, intervention })
                            setCompletionData({
                              status: 'completed',
                              completion_notes: '',
                              patient_response: '',
                              outcome_achieved: '',
                              requires_follow_up: false,
                            })
                          }}
                          title="Complete"
                        >
                          <CompleteIcon />
                        </IconButton>
                      )}
                      <IconButton size="small" title="View History">
                        <HistoryIcon />
                      </IconButton>
                      {user && canManageCarePlans(user.role) && (
                        <IconButton size="small" title="Edit">
                          <EditIcon />
                        </IconButton>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Complete Intervention Dialog */}
      <Dialog 
        open={completeDialog.open} 
        onClose={() => !submitting && setCompleteDialog({ open: false, intervention: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Complete Intervention</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          {completeDialog.intervention && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                {completeDialog.intervention.intervention_name}
              </Typography>
              <Typography variant="body2">{completeDialog.intervention.description}</Typography>
            </Box>
          )}

          <TextField
            select
            fullWidth
            label="Status"
            value={completionData.status}
            onChange={(e) => setCompletionData({ ...completionData, status: e.target.value as any })}
            sx={{ mb: 2 }}
          >
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="partially_completed">Partially Completed</MenuItem>
            <MenuItem value="not_done">Not Done</MenuItem>
            <MenuItem value="refused">Refused</MenuItem>
          </TextField>

          <TextField
            fullWidth
            multiline
            rows={3}
            label="Completion Notes"
            value={completionData.completion_notes}
            onChange={(e) => setCompletionData({ ...completionData, completion_notes: e.target.value })}
            required
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            multiline
            rows={2}
            label="Patient Response"
            value={completionData.patient_response}
            onChange={(e) => setCompletionData({ ...completionData, patient_response: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            multiline
            rows={2}
            label="Outcome Achieved"
            value={completionData.outcome_achieved}
            onChange={(e) => setCompletionData({ ...completionData, outcome_achieved: e.target.value })}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={completionData.requires_follow_up}
                onChange={(e) => setCompletionData({ ...completionData, requires_follow_up: e.target.checked })}
              />
            }
            label="Requires Follow-up"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompleteDialog({ open: false, intervention: null })} disabled={submitting}>
            Cancel
          </Button>
          <Button 
            onClick={handleCompleteIntervention} 
            variant="contained" 
            disabled={submitting || !completionData.completion_notes}
          >
            {submitting ? 'Saving...' : 'Complete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
