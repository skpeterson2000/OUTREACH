import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import PatientList from './pages/PatientList'
import PatientDetail from './pages/PatientDetail'
import ADRAlerts from './pages/ADRAlerts'
import MAR from './pages/MAR'
import MAROverview from './pages/MAROverview'
import OverdueMedications from './pages/OverdueMedications'
import Layout from './components/Layout'
import { LockScreen } from './components/LockScreen'
import { useAuthStore } from './store/authStore'
import { useIdleDetector } from './hooks/useIdleDetector'
import { useEffect } from 'react'

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isLocked = useAuthStore((state) => state.isLocked)
  const lock = useAuthStore((state) => state.lock)
  const location = useLocation()

  // Setup idle detection - 4 minutes of inactivity
  useIdleDetector({
    idleTime: 4 * 60 * 1000, // 4 minutes
    onIdle: () => {
      if (isAuthenticated && !isLocked) {
        lock(location.pathname + location.search)
      }
    },
    enabled: isAuthenticated && !isLocked,
  })

  return isAuthenticated ? <Layout>{children}</Layout> : <Navigate to="/login" />
}

function App() {
  const isLocked = useAuthStore((state) => state.isLocked)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const lockedAt = useAuthStore((state) => state.lockedAt)
  const savedLocation = useAuthStore((state) => state.savedLocation)
  const unlock = useAuthStore((state) => state.unlock)

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        {/* Show lock screen if session is locked */}
        {isLocked && isAuthenticated && user && lockedAt && (
          <LockScreen
            lockedUser={{
              id: user.id,
              username: user.username,
              firstName: user.first_name,
              lastName: user.last_name,
              role: user.role,
            }}
            lockedAt={new Date(lockedAt)}
            onUnlock={(token) => {
              unlock(token)
              // Navigate to saved location
              if (savedLocation) {
                window.location.href = savedLocation
              }
            }}
          />
        )}
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients"
            element={
              <ProtectedRoute>
                <PatientList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:id"
            element={
              <ProtectedRoute>
                <PatientDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/adr"
            element={
              <ProtectedRoute>
                <ADRAlerts />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mar"
            element={
              <ProtectedRoute>
                <MAROverview />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:id/mar"
            element={
              <ProtectedRoute>
                <MAR />
              </ProtectedRoute>
            }
          />
          <Route
            path="/overdue"
            element={
              <ProtectedRoute>
                <OverdueMedications />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
