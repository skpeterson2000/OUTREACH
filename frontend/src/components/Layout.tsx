import { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Person as PersonIcon,
} from '@mui/icons-material'
import { useAuthStore } from '../store/authStore'
import { useState } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navItems = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Patients', path: '/patients' },
    { label: 'MAR', path: '/mar' },
    { label: 'Overdue', path: '/overdue' },
    { label: 'ADR Alerts', path: '/adr' },
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="sticky">
        <Toolbar>
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ cursor: 'pointer' }}
            onClick={() => navigate('/dashboard')}
          >
            Home Care EHR
          </Typography>
          
          <Box sx={{ flexGrow: 1, ml: 4, display: { xs: 'none', md: 'flex' }, gap: 2 }}>
            {navItems.map((item) => (
              <Button
                key={item.path}
                color="inherit"
                onClick={() => navigate(item.path)}
                sx={{
                  borderBottom: location.pathname.startsWith(item.path) ? '2px solid white' : 'none',
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ display: { xs: 'none', sm: 'block' } }}>
              {user?.full_name} ({user?.role})
            </Typography>
            <IconButton
              size="large"
              onClick={handleMenu}
              color="inherit"
            >
              <PersonIcon />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleClose}
            >
              <MenuItem disabled>
                <Typography variant="body2">
                  {user?.email}
                </Typography>
              </MenuItem>
              <MenuItem onClick={() => { handleClose(); navigate('/dashboard'); }}>
                Dashboard
              </MenuItem>
              <MenuItem onClick={() => { handleClose(); navigate('/patients'); }}>
                Patients
              </MenuItem>
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      <Box component="main" sx={{ flexGrow: 1, bgcolor: 'grey.50' }}>
        {children}
      </Box>
    </Box>
  )
}
