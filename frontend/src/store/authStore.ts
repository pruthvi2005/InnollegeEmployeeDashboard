import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface EmployeeProfile {
  id: string;
  full_name: string;
  employee_id: string;
  email: string;
  phone?: string | null;
  is_active: boolean;
  profile_photo_url?: string | null;
  designation?: string;
  department_id?: string;
  department?: {
    id: string;
    name: string;
  };
}

export interface User {
  id: string;
  email: string;
  phone?: string | null;
  role: 'founder' | 'employee';
  is_active: boolean;
  employee?: EmployeeProfile | null;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setAccessToken: (token: string | null) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: true,
      setUser: (user) =>
        set((state) => ({
          user,
          isAuthenticated: !!user && !!state.accessToken,
          isLoading: false,
        })),
      setAccessToken: (accessToken) =>
        set((state) => ({
          accessToken,
          isAuthenticated: !!accessToken && !!state.user,
        })),
      clearAuth: () =>
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isLoading: false,
        }),
      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: 'jyohar_auth_token',
      storage: createJSONStorage(() => localStorage),
      // Only persist the token, do not store sensitive user data in localStorage
      partialize: (state) => ({ accessToken: state.accessToken }),
    }
  )
);
