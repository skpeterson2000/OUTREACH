import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
} from '@mui/material'
import { authApi } from '../services/api'
import { useAuthStore } from '../store/authStore'

export default function Login() {
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authApi.login({ username, password })
      const { access_token, user } = response.data
      login(access_token, user)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.message || err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography component="h1" variant="h4" align="center" gutterBottom>
            OUTREACH EHR
          </Typography>
          <Typography variant="subtitle1" align="center" color="text.secondary" gutterBottom>
            Multi-Care Electronic Health Record
          </Typography>
          <Typography variant="caption" align="center" display="block" color="text.secondary" sx={{ mb: 2 }}>
            Home Health • ALF • Memory Care • SNF
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </Box>

          <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
              Demo Credentials (All use password: password123)
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, fontSize: '0.75rem' }}>
              <Box>
                <Typography variant="caption" display="block" sx={{ fontWeight: 600 }}>
                  Licensed Staff:
                </Typography>
                <Typography variant="caption" display="block">
                  • RN: <strong>nurse.jane</strong>
                </Typography>
                <Typography variant="caption" display="block">
                  • LPN: <strong>nurse.bob</strong>
                </Typography>
                <Typography variant="caption" display="block">
                  • Pharmacist: <strong>pharm.sarah</strong>
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" display="block" sx={{ fontWeight: 600 }}>
                  Delegated & Support:
                </Typography>
                <Typography variant="caption" display="block">
                  • Admin: <strong>admin.mike</strong>
                </Typography>
                <Typography variant="caption" display="block">
                  • TMA: <strong>tma.lisa</strong> 🩺
                </Typography>
                <Typography variant="caption" display="block">
                  • CNA: <strong>cna.maria</strong>
                </Typography>
                <Typography variant="caption" display="block">
                  • HHA: <strong>hha.david</strong>
                </Typography>
              </Box>
            </Box>
            <Typography variant="caption" display="block" sx={{ mt: 1, fontStyle: 'italic', color: 'text.secondary' }}>
              🩺 TMA (Trained Medication Assistant) = CNA with delegated medication administration privileges
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}
