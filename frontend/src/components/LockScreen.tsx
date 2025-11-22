import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Avatar,
  Alert,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Lock as LockIcon,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

interface LockScreenProps {
  lockedUser: {
    id: number;
    username: string;
    firstName: string;
    lastName: string;
    role: string;
  };
  lockedAt: Date;
  onUnlock: (token: string) => void;
}

export const LockScreen: React.FC<LockScreenProps> = ({
  lockedUser,
  lockedAt,
  onUnlock,
}) => {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [lockedDuration, setLockedDuration] = useState('');
  const passwordInputRef = useRef<HTMLInputElement>(null);

  // Focus password input on mount
  useEffect(() => {
    passwordInputRef.current?.focus();
  }, []);

  // Update locked duration every second
  useEffect(() => {
    const updateDuration = () => {
      const now = new Date();
      const diff = Math.floor((now.getTime() - lockedAt.getTime()) / 1000);
      
      if (diff < 60) {
        setLockedDuration(`${diff} second${diff !== 1 ? 's' : ''} ago`);
      } else if (diff < 3600) {
        const minutes = Math.floor(diff / 60);
        setLockedDuration(`${minutes} minute${minutes !== 1 ? 's' : ''} ago`);
      } else {
        const hours = Math.floor(diff / 3600);
        setLockedDuration(`${hours} hour${hours !== 1 ? 's' : ''} ago`);
      }
    };

    updateDuration();
    const interval = setInterval(updateDuration, 1000);
    return () => clearInterval(interval);
  }, [lockedAt]);

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!password) {
      setError('Please enter your password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/auth/login', {
        username: lockedUser.username,
        password: password,
      });

      if (response.data.access_token) {
        onUnlock(response.data.access_token);
      }
    } catch (err: any) {
      console.error('Unlock error:', err);
      setError(
        err.response?.data?.error || 
        'Invalid password. Please try again.'
      );
      setPassword('');
      passwordInputRef.current?.focus();
    } finally {
      setLoading(false);
    }
  };

  const getInitials = () => {
    return `${lockedUser.firstName[0]}${lockedUser.lastName[0]}`.toUpperCase();
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
      }}
    >
      <Card
        sx={{
          minWidth: 400,
          maxWidth: 500,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        }}
      >
        <CardContent
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3,
            padding: 4,
          }}
        >
          {/* Lock Icon */}
          <Box
            sx={{
              backgroundColor: 'error.main',
              borderRadius: '50%',
              padding: 2,
              marginBottom: 1,
            }}
          >
            <LockIcon sx={{ fontSize: 48, color: 'white' }} />
          </Box>

          {/* Title */}
          <Typography variant="h5" fontWeight="bold" textAlign="center">
            Session Locked
          </Typography>

          {/* User Info */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <Avatar
              sx={{
                width: 80,
                height: 80,
                backgroundColor: 'primary.main',
                fontSize: '2rem',
              }}
            >
              {getInitials()}
            </Avatar>
            <Typography variant="h6">
              {lockedUser.firstName} {lockedUser.lastName}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {lockedUser.role} • @{lockedUser.username}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Locked {lockedDuration}
            </Typography>
          </Box>

          {/* Unlock Form */}
          <Box
            component="form"
            onSubmit={handleUnlock}
            sx={{ width: '100%', marginTop: 2 }}
          >
            {error && (
              <Alert severity="error" sx={{ marginBottom: 2 }}>
                {error}
              </Alert>
            )}

            <TextField
              inputRef={passwordInputRef}
              fullWidth
              type={showPassword ? 'text' : 'password'}
              label="Enter Password to Unlock"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ marginBottom: 2 }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading || !password}
              sx={{
                paddingY: 1.5,
                fontWeight: 'bold',
                textTransform: 'none',
                fontSize: '1rem',
              }}
            >
              {loading ? 'Unlocking...' : 'Unlock Session'}
            </Button>
          </Box>

          {/* Security Notice */}
          <Typography
            variant="caption"
            color="text.secondary"
            textAlign="center"
            sx={{ marginTop: 2 }}
          >
            Your session is protected. Enter your password to continue where
            you left off.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};
