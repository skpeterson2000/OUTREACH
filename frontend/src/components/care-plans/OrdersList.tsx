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
  VerifiedUser as VerifyIcon,
} from '@mui/icons-material'
import { ordersApi } from '../../services/carePlans'
import { useAuthStore } from '../../store/authStore'
import { canManageCarePlans, canVerifyPhysicianOrders } from '../../utils/permissions'
import type { PhysicianOrder, CompleteOrderRequest } from '../../types/carePlan'

interface Props {
  carePlanId: number
  orders: PhysicianOrder[]
  onRefresh: () => void
}

export default function OrdersList({ carePlanId, orders, onRefresh }: Props) {
  const { user } = useAuthStore()
  const [completeDialog, setCompleteDialog] = useState<{ open: boolean; order: PhysicianOrder | null }>({
    open: false,
    order: null,
  })
  const [completionData, setCompletionData] = useState<CompleteOrderRequest>({
    status: 'completed',
    completion_notes: '',
    results: '',
    requires_follow_up: false,
    physician_notified: false,
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleVerifyOrder = async (orderId: number) => {
    try {
      await ordersApi.verify(orderId)
      onRefresh()
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to verify order')
    }
  }

  const handleCompleteOrder = async () => {
    if (!completeDialog.order) return

    try {
      setSubmitting(true)
      setError('')
      await ordersApi.complete(completeDialog.order.id, completionData)
      setCompleteDialog({ open: false, order: null })
      setCompletionData({
        status: 'completed',
        completion_notes: '',
        results: '',
        requires_follow_up: false,
        physician_notified: false,
      })
      onRefresh()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to complete order')
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
      case 'on_hold':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getVerificationColor = (status: string) => {
    switch (status) {
      case 'verified':
        return 'success'
      case 'pending':
        return 'warning'
      case 'clarification_needed':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Physician Orders</Typography>
        {user && canManageCarePlans(user.role) && (
          <Button startIcon={<AddIcon />} variant="contained" size="small">
            Add Order
          </Button>
        )}
      </Box>

      {/* Orders Table */}
      {orders.length === 0 ? (
        <Alert severity="info">No physician orders added yet.</Alert>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Verification</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Order</TableCell>
                <TableCell>Physician</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell>
                    <Chip label={order.status} color={getStatusColor(order.status)} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={order.verification_status} 
                      color={getVerificationColor(order.verification_status)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{order.order_type}</TableCell>
                  <TableCell>
                    <Typography variant="body2">{order.order_text}</Typography>
                    {order.frequency && (
                      <Typography variant="caption" color="text.secondary">
                        {order.frequency}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{order.ordering_physician}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {user && 
                        canVerifyPhysicianOrders(user.role) && 
                        order.verification_status === 'pending' && (
                        <IconButton
                          size="small"
                          onClick={() => handleVerifyOrder(order.id)}
                          title="Verify Order"
                        >
                          <VerifyIcon />
                        </IconButton>
                      )}
                      {order.verification_status === 'verified' && order.status === 'active' && (
                        <IconButton
                          size="small"
                          onClick={() => {
                            setCompleteDialog({ open: true, order })
                            setCompletionData({
                              status: 'completed',
                              completion_notes: '',
                              results: '',
                              requires_follow_up: false,
                              physician_notified: false,
                            })
                          }}
                          title="Complete"
                        >
                          <CompleteIcon />
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

      {/* Complete Order Dialog */}
      <Dialog 
        open={completeDialog.open} 
        onClose={() => !submitting && setCompleteDialog({ open: false, order: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Complete Physician Order</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          {completeDialog.order && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                {completeDialog.order.order_text}
              </Typography>
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
            <MenuItem value="in_progress">In Progress</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
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
            label="Results"
            value={completionData.results}
            onChange={(e) => setCompletionData({ ...completionData, results: e.target.value })}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={completionData.physician_notified}
                onChange={(e) => setCompletionData({ ...completionData, physician_notified: e.target.checked })}
              />
            }
            label="Physician Notified"
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
          <Button onClick={() => setCompleteDialog({ open: false, order: null })} disabled={submitting}>
            Cancel
          </Button>
          <Button 
            onClick={handleCompleteOrder} 
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
