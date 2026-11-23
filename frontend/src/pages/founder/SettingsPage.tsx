import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ShieldCheck, UserRound } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const user = useAuthStore((state) => state.user);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-amber-700">Account & access</p>
        <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-slate-950">Founder Settings</h1>
        <p className="mt-1 text-sm text-slate-500">Review the administrator account and its access level.</p>
      </div>
      <Card className="overflow-hidden border-slate-200 shadow-sm">
        <CardHeader className="border-b border-slate-100 bg-gradient-to-r from-white to-amber-50/60">
          <CardTitle className="flex items-center gap-2 font-bold">
            <UserRound className="h-5 w-5 text-amber-700" />
            Founder profile
          </CardTitle>
          <CardDescription>Role and sign-in email are managed by the platform administrator.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5 p-6 sm:grid-cols-2">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Name</p>
            <p className="font-semibold text-slate-900">{user?.employee?.full_name || 'Admin'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Email</p>
            <p className="break-all font-semibold text-slate-900">{user?.email || '—'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Phone</p>
            <p className="font-semibold text-slate-900">{user?.phone || 'Not provided'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Role</p>
            <Badge variant="accent" className="mt-1 inline-flex items-center gap-1">
              <ShieldCheck className="h-3.5 w-3.5" /> Founder / Administrator
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Account status</p>
            <Badge variant={user?.is_active ? 'success' : 'destructive'}>{user?.is_active ? 'Active' : 'Inactive'}</Badge>
          </div>
          <p className="text-sm leading-6 text-slate-500 sm:col-span-2">
            The founder role is fixed and has administrator access. The phone number shown here is the number currently saved on the account.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;
