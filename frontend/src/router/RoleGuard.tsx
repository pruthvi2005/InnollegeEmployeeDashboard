import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

interface RoleGuardProps {
  role: 'founder' | 'employee';
  children?: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ role, children }) => {
  const user = useAuthStore((s) => s.user);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // If user role does not match required role
  if (user.role !== role) {
    const fallbackPath = user.role === 'founder' ? '/founder/overview' : '/employee/dashboard';
    return <Navigate to={fallbackPath} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default RoleGuard;
