import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// SECURITY: Clear any old localStorage auth data on app startup
// Auth now uses sessionStorage which clears on close, but this removes old data
if (localStorage.getItem('auth-storage')) {
  localStorage.removeItem('auth-storage')
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
