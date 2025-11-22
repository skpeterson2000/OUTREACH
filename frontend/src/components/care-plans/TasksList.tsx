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
  History as HistoryIcon,
} from '@mui/icons-material'
import { tasksApi } from '../../services/carePlans'
import { useAuthStore } from '../../store/authStore'
import { canManageCarePlans, canCompleteAssistanceTask } from '../../utils/permissions'
import type { AssistanceTask, CompleteTaskRequest } from '../../types/carePlan'

interface Props {
  carePlanId: number
  tasks: AssistanceTask[]
  onRefresh: () => void
}

export default function TasksList({ carePlanId, tasks, onRefresh }: Props) {
  const { user } = useAuthStore()
  const [completeDialog, setCompleteDialog] = useState<{ open: boolean; task: AssistanceTask | null }>({
    open: false,
    task: null,
  })
  const [completionData, setCompletionData] = useState<CompleteTaskRequest>({
    status: 'completed',
    completion_notes: '',
    patient_tolerance: 'well_tolerated',
    safety_incidents: false,
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleCompleteTask = async () => {
    if (!completeDialog.task) return

    try {
      setSubmitting(true)
      setError('')
      await tasksApi.complete(completeDialog.task.id, completionData)
      setCompleteDialog({ open: false, task: null })
      setCompletionData({
        status: 'completed',
        completion_notes: '',
        patient_tolerance: 'well_tolerated',
        safety_incidents: false,
      })
      onRefresh()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to complete task')
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

  const getCategoryColor = (category: string) => {
    const colors: Record<string, any> = {
      adl: 'primary',
      meal: 'secondary',
      hygiene: 'info',
      mobility: 'warning',
      comfort: 'success',
      safety: 'error',
    }
    return colors[category] || 'default'
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Assistance Tasks</Typography>
        {user && canManageCarePlans(user.role) && (
          <Button startIcon={<AddIcon />} variant="contained" size="small">
            Add Task
          </Button>
        )}
      </Box>

      {/* Tasks Table */}
      {tasks.length === 0 ? (
        <Alert severity="info">No assistance tasks added yet.</Alert>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Task</TableCell>
                <TableCell>Assistance Level</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Assigned</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>
                    <Chip label={task.status} color={getStatusColor(task.status)} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip label={task.task_category} color={getCategoryColor(task.task_category)} size="small" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{task.task_name}</Typography>
                    {task.requires_two_person_assist && (
                      <Chip label="2-Person Assist" size="small" color="warning" sx={{ mt: 0.5 }} />
                    )}
                    {task.fall_risk_precautions && (
                      <Chip label="Fall Risk" size="small" color="error" sx={{ mt: 0.5, ml: 0.5 }} />
                    )}
                  </TableCell>
                  <TableCell>{task.assistance_level || 'N/A'}</TableCell>
                  <TableCell>{task.frequency}</TableCell>
                  <TableCell>{task.assigned_role}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {user && 
                        canCompleteAssistanceTask(user.role) &&
                        task.status === 'active' && (
                        <IconButton
                          size="small"
                          onClick={() => {
                            setCompleteDialog({ open: true, task })
                            setCompletionData({
                              status: 'completed',
                              completion_notes: '',
                              patient_tolerance: 'well_tolerated',
                              safety_incidents: false,
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
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Complete Task Dialog */}
      <Dialog 
        open={completeDialog.open} 
        onClose={() => !submitting && setCompleteDialog({ open: false, task: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Complete Assistance Task</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          {completeDialog.task && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                {completeDialog.task.task_name}
              </Typography>
              <Typography variant="body2">{completeDialog.task.description}</Typography>
              {completeDialog.task.requires_two_person_assist && (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  This task requires two-person assist
                </Alert>
              )}
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
            select
            fullWidth
            label="Patient Tolerance"
            value={completionData.patient_tolerance}
            onChange={(e) => setCompletionData({ ...completionData, patient_tolerance: e.target.value })}
            sx={{ mb: 2 }}
          >
            <MenuItem value="well_tolerated">Well Tolerated</MenuItem>
            <MenuItem value="some_difficulty">Some Difficulty</MenuItem>
            <MenuItem value="poorly_tolerated">Poorly Tolerated</MenuItem>
          </TextField>

          <TextField
            fullWidth
            multiline
            rows={3}
            label="Completion Notes"
            value={completionData.completion_notes}
            onChange={(e) => setCompletionData({ ...completionData, completion_notes: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Patient Participation"
            value={completionData.patient_participation}
            onChange={(e) => setCompletionData({ ...completionData, patient_participation: e.target.value })}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={completionData.safety_incidents}
                onChange={(e) => setCompletionData({ ...completionData, safety_incidents: e.target.checked })}
              />
            }
            label="Safety Incident Occurred"
          />

          {completionData.safety_incidents && (
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Incident Details"
              value={completionData.incident_notes}
              onChange={(e) => setCompletionData({ ...completionData, incident_notes: e.target.value })}
              required
              sx={{ mt: 2 }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompleteDialog({ open: false, task: null })} disabled={submitting}>
            Cancel
          </Button>
          <Button 
            onClick={handleCompleteTask} 
            variant="contained" 
            disabled={submitting || (completionData.safety_incidents && !completionData.incident_notes)}
          >
            {submitting ? 'Saving...' : 'Complete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
