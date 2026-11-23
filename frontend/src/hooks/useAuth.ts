import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi, LoginResponse, OtpRequestResponse } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'sonner';

export const useAuth = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, accessToken, isAuthenticated, isLoading, setUser, setAccessToken, clearAuth, setLoading } =
    useAuthStore();

  // Query: me (fetches user profile if token is present)
  const meQuery = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      try {
        const currentUser = await authApi.me();
        setUser(currentUser);
        return currentUser;
      } catch (error) {
        clearAuth();
        throw error;
      } finally {
        setLoading(false);
      }
    },
    enabled: !!accessToken && !user,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  // Helper to redirect to dashboard based on role
  const navigateToDashboard = (role: 'founder' | 'employee') => {
    if (role === 'founder') {
      navigate('/founder/overview', { replace: true });
    } else {
      navigate('/employee/dashboard', { replace: true });
    }
  };

  // Mutation: Email Login
  const loginMutation = useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      return await authApi.login(email, password);
    },
    onSuccess: async (data: LoginResponse) => {
      setAccessToken(data.access_token);
      try {
        const currentUser = data.user || await authApi.me();
        setUser(currentUser);
        queryClient.setQueryData(['auth', 'me'], currentUser);
        toast.success(`Welcome back, ${currentUser.employee?.full_name || currentUser.email}!`);
        navigateToDashboard(currentUser.role);
      } catch {
        clearAuth();
        toast.error('Login succeeded, but the user profile could not be loaded.');
      }
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || error.response?.data?.message || 'Login failed. Please check your credentials.';
      toast.error(msg);
    },
  });

  // Mutation: Request OTP
  const otpRequestMutation = useMutation({
    mutationFn: async (phone: string) => {
      return await authApi.requestOtp(phone);
    },
    onSuccess: (data: OtpRequestResponse) => {
      if (data.otp_sent || data.development_otp) {
        toast.success(data.message);
      } else {
        toast.error(data.message || 'No active account is registered with this phone number.');
      }
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || error.response?.data?.message || 'Failed to send OTP. Please try again.';
      toast.error(msg);
    },
  });

  // Mutation: Verify OTP
  const otpVerifyMutation = useMutation({
    mutationFn: async ({ phone, otp }: { phone: string; otp: string }) => {
      return await authApi.verifyOtp(phone, otp);
    },
    onSuccess: async (data: LoginResponse) => {
      setAccessToken(data.access_token);
      try {
        const currentUser = data.user || await authApi.me();
        setUser(currentUser);
        queryClient.setQueryData(['auth', 'me'], currentUser);
        toast.success(`Welcome back, ${currentUser.employee?.full_name || currentUser.email}!`);
        navigateToDashboard(currentUser.role);
      } catch {
        clearAuth();
        toast.error('Login succeeded, but the user profile could not be loaded.');
      }
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || error.response?.data?.message || 'Invalid OTP code. Please try again.';
      toast.error(msg);
    },
  });

  // Mutation: Logout
  const logoutMutation = useMutation({
    mutationFn: async () => {
      try {
        await authApi.logout();
      } catch {
        // Continue clearing even if server call fails
      }
    },
    onSettled: () => {
      clearAuth();
      queryClient.clear();
      toast.info('You have been signed out.');
      navigate('/login', { replace: true });
    },
  });

  return {
    user,
    accessToken,
    isAuthenticated,
    isLoading: isLoading || (!!accessToken && !user && meQuery.isLoading),
    useMe: () => meQuery,
    useLoginMutation: () => loginMutation,
    useOtpRequestMutation: () => otpRequestMutation,
    useOtpVerifyMutation: () => otpVerifyMutation,
    useLogoutMutation: () => logoutMutation,
    loginMutation,
    otpRequestMutation,
    otpVerifyMutation,
    logoutMutation,
  };
};

export const useMe = () => {
  const { useMe: getMe } = useAuth();
  return getMe();
};

export const useLoginMutation = () => {
  const { loginMutation } = useAuth();
  return loginMutation;
};

export const useOtpRequestMutation = () => {
  const { otpRequestMutation } = useAuth();
  return otpRequestMutation;
};

export const useOtpVerifyMutation = () => {
  const { otpVerifyMutation } = useAuth();
  return otpVerifyMutation;
};

export const useLogoutMutation = () => {
  const { logoutMutation } = useAuth();
  return logoutMutation;
};
