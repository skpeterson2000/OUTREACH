import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
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
import { useAuthStore } from './store/authStore'

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
  return isAuthenticated ? <Layout>{children}</Layout> : <Navigate to="/login" />
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
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
