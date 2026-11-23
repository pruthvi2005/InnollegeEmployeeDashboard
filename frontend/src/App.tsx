import React from 'react';
import { AppRoutes } from '@/router';
import { useMe } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';
import { BrandLogo } from '@/components/shared/BrandLogo';

export const App: React.FC = () => {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);

  // Initialize and validate session on boot if token exists
  const { isLoading } = useMe();

  // If restoring auth session from persisted token
  if (accessToken && !user && isLoading) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-surface">
        <div className="flex flex-col items-center space-y-4">
        <BrandLogo
          orientation="vertical"
          className="h-40 w-40 rounded-lg object-contain shadow-md"
        />
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <p className="text-xs font-medium text-muted-foreground">
            Initializing Jyohar Platform...
          </p>
        </div>
      </div>
    );
  }

  return <AppRoutes />;
};

export default App;
