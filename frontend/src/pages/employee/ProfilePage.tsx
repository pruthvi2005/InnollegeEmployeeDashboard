import React, { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { attendanceApi, employeesApi } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'sonner';
import { User } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.user);
  const profile = useQuery({ queryKey: ['profile', 'me'], queryFn: employeesApi.getMe });
  const attendance = useQuery({ queryKey: ['attendance', 'today'], queryFn: attendanceApi.todayStatus });

  useEffect(() => {
    if (profile.data) {
      setFullName(profile.data.full_name || '');
      setPhone(profile.data.phone || '');
    }
  }, [profile.data]);

  const update = useMutation({
    mutationFn: () => employeesApi.updateMe({ full_name: fullName.trim(), phone: phone.trim() || undefined }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['profile', 'me'] }),
        queryClient.invalidateQueries({ queryKey: ['auth', 'me'] }),
      ]);
      toast.success('Profile updated.');
    },
    onError: (error) => toast.error(axios.isAxiosError(error) ? String(error.response?.data?.detail || 'Update failed.') : 'Update failed.'),
  });

  const attendanceStatus = attendance.data?.status;
  const attendanceLabel = attendanceStatus === 'present'
    ? 'Present'
    : attendanceStatus === 'on_leave'
      ? 'On leave'
      : attendanceStatus === 'absent' || attendanceStatus === 'not_checked_in'
        ? 'Absent'
        : 'Unknown';
  const attendanceVariant = attendanceStatus === 'present' ? 'success' : attendanceStatus === 'on_leave' ? 'warning' : 'secondary';

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><User className="h-5 w-5" /></div>
        <div><h1 className="text-2xl font-bold">My Profile</h1><p className="text-sm text-muted-foreground">Your account details and today’s attendance.</p></div>
      </div>
      <Card className="border-slate-200 shadow-sm">
        <CardHeader><CardTitle>Account overview</CardTitle><CardDescription>Your sign-in details, role, and current attendance status.</CardDescription></CardHeader>
        <CardContent>
          {profile.isLoading ? <p className="text-sm text-muted-foreground">Loading profile...</p> : profile.isError ? (
            <p role="alert" className="text-sm text-danger">Could not load your profile. Please refresh the page.</p>
          ) : profile.data ? (
            <div className="grid gap-5 sm:grid-cols-2">
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Name</p><p className="mt-1 font-semibold text-slate-900">{profile.data.full_name}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Email</p><p className="mt-1 break-all font-semibold text-slate-900">{profile.data.email || currentUser?.email || '—'}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Phone</p><p className="mt-1 font-semibold text-slate-900">{profile.data.phone || 'Not provided'}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Role</p><Badge variant="accent" className="mt-1">Employee</Badge></div>
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Today</p>
                {attendance.isLoading ? <p className="mt-1 text-sm text-slate-500">Checking attendance...</p> : attendance.isError ? (
                  <p role="alert" className="mt-1 text-sm text-danger">Attendance status unavailable.</p>
                ) : <Badge variant={attendanceVariant} className="mt-1">{attendanceLabel}</Badge>}
              </div>
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Designation</p><p className="mt-1 font-semibold text-slate-900">{profile.data.designation || '—'}</p></div>
            </div>
          ) : <p className="text-sm text-muted-foreground">Profile not available.</p>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Edit contact details</CardTitle><CardDescription>Email and account role cannot be changed here.</CardDescription></CardHeader>
        <CardContent>
          {profile.data && (
            <form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); update.mutate(); }}>
              <label className="space-y-1 text-sm font-medium">Full name<Input required minLength={2} maxLength={255} value={fullName} onChange={(e) => setFullName(e.target.value)} /></label>
              <label className="space-y-1 text-sm font-medium">Phone<Input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} /></label>
              <div className="sm:col-span-2"><Button disabled={update.isPending}>{update.isPending ? 'Saving...' : 'Save profile'}</Button></div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ProfilePage;
