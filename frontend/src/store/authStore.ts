import { create } from 'zustand'
import { persist, PersistOptions } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLocked: boolean
  lockedAt: Date | null
  savedLocation: string | null
  login: (token: string, user: User) => void
  logout: () => void
  lock: (currentLocation: string) => void
  unlock: (token: string) => void
}

// Custom storage that uses sessionStorage instead of localStorage
// sessionStorage is cleared when browser/tab closes
const sessionStorageAPI = {
  getItem: (name: string) => {
    const value = sessionStorage.getItem(name)
    return value
  },
  setItem: (name: string, value: string) => {
    sessionStorage.setItem(name, value)
  },
  removeItem: (name: string) => {
    sessionStorage.removeItem(name)
  },
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLocked: false,
      lockedAt: null,
      savedLocation: null,
      login: (token, user) => set({ token, user, isAuthenticated: true, isLocked: false }),
      logout: () => set({ token: null, user: null, isAuthenticated: false, isLocked: false, lockedAt: null, savedLocation: null }),
      lock: (currentLocation) => set({ isLocked: true, lockedAt: new Date(), savedLocation: currentLocation }),
      unlock: (token) => set({ token, isLocked: false, lockedAt: null }),
    }),
    {
      name: 'auth-storage',
      // SECURITY: Use sessionStorage instead of localStorage
      // Session is cleared when browser/tab closes or app restarts
      storage: sessionStorageAPI,
    } as PersistOptions<AuthState>
  )
)
