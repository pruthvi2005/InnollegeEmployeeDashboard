import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const location = useLocation();
  const { isAuthenticated, accessToken, isLoading } = useAuthStore();

  // If initial auth token check / useMe is in flight
  if (isLoading && accessToken) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-surface">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-accent border-t-transparent" />
          <p className="text-sm font-medium text-muted">Authenticating session...</p>
        </div>
      </div>
    );
  }

  // If no token or explicitly unauthenticated
  if (!isAuthenticated && !accessToken) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
