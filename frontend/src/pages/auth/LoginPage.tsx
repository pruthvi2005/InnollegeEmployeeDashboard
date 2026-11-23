import React, { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  Phone,
  Users,
  FolderKanban,
  BarChart3,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLoginMutation, useOtpRequestMutation, useOtpVerifyMutation } from '@/hooks/useAuth';
import { BrandLogo } from '@/components/shared/BrandLogo';
import { toast } from 'sonner';

// Zod Validation Schemas
const emailSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

const phoneSchema = z.object({
  phone: z
    .string()
    .min(10, 'Phone number must be 10 digits')
    .max(10, 'Phone number must be 10 digits')
    .regex(/^[6-9]\d{9}$/, 'Enter a valid 10-digit Indian mobile number'),
});

type EmailFormValues = z.infer<typeof emailSchema>;
type PhoneFormValues = z.infer<typeof phoneSchema>;

export const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [developmentOtp, setDevelopmentOtp] = useState<string | null>(null);
  const [phoneSubmitted, setPhoneSubmitted] = useState('');
  const [otpValues, setOtpValues] = useState<string[]>(['', '', '', '', '', '']);
  const [resendTimer, setResendTimer] = useState(0);

  const otpInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Auth Mutations
  const loginMutation = useLoginMutation();
  const otpRequestMutation = useOtpRequestMutation();
  const otpVerifyMutation = useOtpVerifyMutation();

  // Email form
  const {
    register: registerEmail,
    handleSubmit: handleEmailSubmit,
    formState: { errors: emailErrors },
  } = useForm<EmailFormValues>({
    resolver: zodResolver(emailSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  // Phone form
  const {
    register: registerPhone,
    handleSubmit: handlePhoneSubmit,
    formState: { errors: phoneErrors },
  } = useForm<PhoneFormValues>({
    resolver: zodResolver(phoneSchema),
    defaultValues: {
      phone: '',
    },
  });

  // Resend Countdown Timer
  useEffect(() => {
    if (resendTimer > 0) {
      const interval = setInterval(() => {
        setResendTimer((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [resendTimer]);

  // Handle email submission
  const onEmailSubmit = (values: EmailFormValues) => {
    loginMutation.mutate({
      email: values.email.trim(),
      password: values.password,
    });
  };

  // Handle sending OTP
  const onSendOtp = (values: PhoneFormValues) => {
    const formattedPhone = `+91${values.phone.trim()}`;
    setPhoneSubmitted(formattedPhone);
    otpRequestMutation.mutate(formattedPhone, {
      onSuccess: (data) => {
        const otpSent = data.otp_sent || Boolean(data.development_otp);
        if (!otpSent) {
          setOtpSent(false);
          setDevelopmentOtp(null);
          return;
        }
        setOtpSent(otpSent);
        setDevelopmentOtp(data.development_otp ?? null);
        setResendTimer(60);
        setTimeout(() => otpInputRefs.current[0]?.focus(), 100);
      },
    });
  };

  // Handle OTP digit box change
  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otpValues];
    // Take the last digit entered
    newOtp[index] = value.slice(-1);
    setOtpValues(newOtp);

    // Auto-advance
    if (value && index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpValues[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;

    const newOtp = [...otpValues];
    for (let i = 0; i < 6; i++) {
      newOtp[i] = pasted[i] || '';
    }
    setOtpValues(newOtp);
    const nextIdx = Math.min(pasted.length, 5);
    otpInputRefs.current[nextIdx]?.focus();
  };

  // Handle verifying OTP
  const handleVerifyOtp = (e: React.FormEvent) => {
    e.preventDefault();
    const otpCode = otpValues.join('');
    if (otpCode.length !== 6) {
      toast.error('Please enter a complete 6-digit verification code.');
      return;
    }
    otpVerifyMutation.mutate({
      phone: phoneSubmitted,
      otp: otpCode,
    });
  };

  const handleResendOtp = () => {
    if (resendTimer > 0 || !phoneSubmitted) return;
    otpRequestMutation.mutate(phoneSubmitted, {
      onSuccess: (data) => {
        const otpSent = data.otp_sent || Boolean(data.development_otp);
        if (!otpSent) {
          setOtpSent(false);
          setDevelopmentOtp(null);
          return;
        }
        setResendTimer(60);
        setDevelopmentOtp(data.development_otp ?? null);
        setOtpValues(['', '', '', '', '', '']);
        otpInputRefs.current[0]?.focus();
      },
    });
  };

  return (
    <div className="flex min-h-screen w-full flex-col lg:flex-row bg-surface">
      {/* LEFT HALF: Brand Showcase Panel */}
      <div className="relative flex flex-col justify-between overflow-hidden bg-gradient-to-br from-[#061B43] via-[#0A377B] to-[#1053B6] p-8 text-white lg:w-1/2 lg:p-14">
        {/* Subtle decorative glow circles */}
        <div className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-accent/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 -left-24 h-96 w-96 rounded-full bg-blue-400/10 blur-3xl" />

        {/* Top Header Logo */}
        <div className="relative z-10 flex items-center space-x-3.5">
          <BrandLogo
            className="h-12 w-48 shrink-0 object-contain brightness-0 invert"
          />
          <div>
            <p className="text-sm font-semibold text-white">
              Company Management
            </p>
            <p className="text-xs font-medium text-slate-300">
              Platform
            </p>
          </div>
        </div>

        {/* Middle Feature Highlights */}
        <div className="relative z-10 my-10 hidden space-y-6 lg:block">
          <div className="space-y-2">
            <span className="inline-flex items-center rounded-full bg-accent/20 px-3 py-1 text-xs font-semibold text-blue-200 border border-blue-400/20">
              <ShieldCheck className="mr-1.5 h-3.5 w-3.5 text-accent" />
              Unified Enterprise Workspace
            </span>
            <h2 className="text-3xl font-bold leading-tight text-white xl:text-4xl">
              Streamline operations, attendance & projects in one place.
            </h2>
            <p className="text-sm text-slate-300 max-w-md">
              Designed specifically for agile software engineering teams, rapid task tracking, and transparent daily reporting.
            </p>
          </div>

          <div className="space-y-4 pt-4">
            <div className="flex items-center space-x-4 rounded-xl bg-white/5 p-3.5 border border-white/10 backdrop-blur-sm">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-500/20 text-blue-300">
                <Users className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Manage Teams</p>
                <p className="text-xs text-slate-300">
                  Track employee attendance, leaves, and daily reports seamlessly.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4 rounded-xl bg-white/5 p-3.5 border border-white/10 backdrop-blur-sm">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-500/20 text-amber-300">
                <FolderKanban className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Track Projects & Tasks</p>
                <p className="text-xs text-slate-300">
                  Sprint management, real-time status updates, and priority queues.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4 rounded-xl bg-white/5 p-3.5 border border-white/10 backdrop-blur-sm">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-300">
                <BarChart3 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Executive Analytics</p>
                <p className="text-xs text-slate-300">
                  High-level company overview for founders and leadership.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Footer Note */}
        <div className="relative z-10 text-xs text-slate-400">
          © {new Date().getFullYear()} Jyohar Tech. All rights reserved.
        </div>
      </div>

      {/* RIGHT HALF: Authentication Panel */}
      <div className="flex flex-1 flex-col justify-center px-6 py-12 sm:px-12 lg:px-16 xl:px-24">
        <div className="mx-auto w-full max-w-md space-y-6">
          {/* Header */}
          <div className="space-y-1.5 text-left">
            <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Welcome back
            </h2>
            <p className="text-sm text-muted-foreground">
              Sign in to access your dashboard and workspace
            </p>
          </div>

          {/* Form Tabs */}
          <Tabs defaultValue="email" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="email">Email & Password</TabsTrigger>
              <TabsTrigger value="otp">Phone OTP</TabsTrigger>
            </TabsList>

            {/* TAB 1: Email & Password */}
            <TabsContent value="email">
              <form onSubmit={handleEmailSubmit(onEmailSubmit)} className="space-y-4">
                {/* Email Input */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground" htmlFor="email-input">
                    Email address
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                      <Mail className="h-4 w-4" />
                    </div>
                    <Input
                      id="email-input"
                      type="email"
                      placeholder="name@jyohar.com"
                      className="pl-10"
                      autoComplete="email"
                      {...registerEmail('email')}
                    />
                  </div>
                  {emailErrors.email && (
                    <p className="text-xs text-danger">{emailErrors.email.message}</p>
                  )}
                </div>

                {/* Password Input */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-foreground" htmlFor="password-input">
                      Password
                    </label>
                    <button
                      type="button"
                      onClick={() =>
                        toast.info('Password reset is managed by platform administration. Contact your admin.')
                      }
                      className="text-xs font-medium text-accent hover:underline"
                    >
                      Forgot password?
                    </button>
                  </div>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                      <Lock className="h-4 w-4" />
                    </div>
                    <Input
                      id="password-input"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      className="pl-10 pr-10"
                      autoComplete="current-password"
                      {...registerEmail('password')}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600 focus:outline-none"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {emailErrors.password && (
                    <p className="text-xs text-danger">{emailErrors.password.message}</p>
                  )}
                </div>

                {/* Sign In Button */}
                <Button
                  type="submit"
                  disabled={loginMutation.isPending}
                  className="w-full bg-primary hover:bg-navy-light text-white font-semibold h-11 transition-all"
                >
                  {loginMutation.isPending ? (
                    <span className="flex items-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Signing in...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      Sign In
                      <ArrowRight className="h-4 w-4" />
                    </span>
                  )}
                </Button>
              </form>
            </TabsContent>

            {/* TAB 2: Phone OTP */}
            <TabsContent value="otp">
              {!otpSent ? (
                /* Step 1: Phone Number Input */
                <form onSubmit={handlePhoneSubmit(onSendOtp)} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground" htmlFor="phone-input">
                      Mobile Number
                    </label>
                    <div className="relative flex items-center">
                      <div className="flex h-10 items-center justify-center rounded-l-lg border border-r-0 border-border bg-slate-50 px-3 text-xs font-medium text-slate-600">
                        🇮🇳 +91
                      </div>
                      <Input
                        id="phone-input"
                        type="tel"
                        maxLength={10}
                        placeholder="9876543210"
                        className="rounded-l-none"
                        {...registerPhone('phone')}
                      />
                    </div>
                    {phoneErrors.phone && (
                      <p className="text-xs text-danger">{phoneErrors.phone.message}</p>
                    )}
                  </div>

                  <Button
                    type="submit"
                    disabled={otpRequestMutation.isPending}
                    className="w-full bg-primary hover:bg-navy-light text-white font-semibold h-11 transition-all"
                  >
                    {otpRequestMutation.isPending ? (
                      <span className="flex items-center gap-2">
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        Sending code...
                      </span>
                    ) : (
                      <span className="flex items-center justify-center gap-2">
                        <Phone className="h-4 w-4" />
                        Send OTP
                      </span>
                    )}
                  </Button>
                </form>
              ) : (
                /* Step 2: 6-Digit OTP Verification */
                <form onSubmit={handleVerifyOtp} className="space-y-5 animate-fade-in">
                  <div className="text-center space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Enter the 6-digit verification code sent to{' '}
                      <span className="font-semibold text-foreground">{phoneSubmitted}</span>
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        setOtpSent(false);
                        setDevelopmentOtp(null);
                        setOtpValues(['', '', '', '', '', '']);
                      }}
                      className="text-xs text-accent hover:underline font-medium"
                    >
                      Change phone number
                    </button>
                  </div>

                  {developmentOtp && (
                    <div
                      role="status"
                      className="rounded-xl border border-[#008FFF]/40 bg-[#eff7ff] p-3 text-center"
                    >
                      <p className="text-xs font-bold uppercase tracking-wide text-[#0A377B]">
                        Development OTP
                      </p>
                      <p className="mt-1 font-mono text-2xl font-extrabold tracking-[0.3em] text-[#061B43]">
                        {developmentOtp}
                      </p>
                      <p className="mt-1 text-[11px] text-[#0A377B]">
                        SMS is not configured; enter this code to continue.
                      </p>
                    </div>
                  )}

                  {/* 6 Digit Inputs */}
                  <div className="flex justify-between gap-2" onPaste={handleOtpPaste}>
                    {otpValues.map((digit, index) => (
                      <input
                        key={index}
                        ref={(el) => (otpInputRefs.current[index] = el)}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleOtpChange(index, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(index, e)}
                        className="h-12 w-12 text-center text-xl font-bold rounded-lg border border-border bg-white text-foreground shadow-sm focus:border-accent focus:ring-2 focus:ring-accent focus:outline-none transition-colors"
                      />
                    ))}
                  </div>

                  {/* Resend Timer */}
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Didn't receive code?</span>
                    {resendTimer > 0 ? (
                      <span className="text-slate-400 font-mono">
                        Resend in {resendTimer}s
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={handleResendOtp}
                        disabled={otpRequestMutation.isPending}
                        className="inline-flex items-center text-accent hover:underline font-medium"
                      >
                        <RotateCcw className="mr-1 h-3 w-3" />
                        Resend OTP
                      </button>
                    )}
                  </div>

                  <Button
                    type="submit"
                    disabled={otpVerifyMutation.isPending || otpValues.join('').length !== 6}
                    className="w-full bg-accent hover:bg-accent-hover text-white font-semibold h-11 transition-all"
                  >
                    {otpVerifyMutation.isPending ? (
                      <span className="flex items-center gap-2">
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        Verifying...
                      </span>
                    ) : (
                      'Verify & Sign In'
                    )}
                  </Button>
                </form>
              )}
            </TabsContent>
          </Tabs>

          {/* Quick Demo Credentials Tip */}
          <div className="rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5 text-xs text-muted-foreground">
            <p className="font-semibold text-slate-700">Platform Credentials:</p>
            <p className="mt-0.5">Founder: <code className="text-primary font-mono font-medium">founder@jyohartech.com</code></p>
            <p className="mt-0.5">Employee accounts are created by the founder.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
