import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Clock, LogIn, LogOut } from 'lucide-react';
import { toast } from 'sonner';
import { attendanceApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export const AttendancePage: React.FC = () => {
  const queryClient = useQueryClient();
  const today = useQuery({ queryKey: ['attendance', 'today'], queryFn: attendanceApi.todayStatus });
  const history = useQuery({ queryKey: ['attendance', 'me'], queryFn: () => attendanceApi.me({ page: 1, page_size: 100 }) });
  const checkIn = useMutation({ mutationFn: () => attendanceApi.checkIn(), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['attendance'] }); toast.success('Checked in successfully.'); }, onError: (error: any) => toast.error(error.response?.data?.detail || 'Check-in failed.') });
  const checkOut = useMutation({ mutationFn: () => attendanceApi.checkOut(), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['attendance'] }); toast.success('Checked out successfully.'); }, onError: (error: any) => toast.error(error.response?.data?.detail || 'Check-out failed.') });
  const checkedIn = Boolean(today.data?.check_in_time);
  const checkedOut = Boolean(today.data?.check_out_time);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><Clock className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">My Attendance</h1><p className="text-sm text-muted-foreground">Check in, check out, and view your attendance history.</p></div></div>
      <Card><CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div><div className="flex items-center gap-2"><span className="font-semibold">Today's status</span><Badge variant={checkedOut ? 'success' : checkedIn ? 'success' : 'secondary'}>{checkedOut ? 'Checked out' : checkedIn ? 'Checked in' : 'Not checked in'}</Badge></div><p className="mt-2 text-sm text-muted-foreground">Check in: {today.data?.check_in_time || '—'} · Check out: {today.data?.check_out_time || '—'}</p></div>
        {today.isError ? <p role="alert" className="text-sm text-danger">Could not load today's attendance.</p> : checkedIn && !checkedOut ? <Button variant="destructive" onClick={() => checkOut.mutate()} disabled={checkOut.isPending}><LogOut className="mr-2 h-4 w-4" />Check out</Button> : <Button onClick={() => checkIn.mutate()} disabled={checkIn.isPending || checkedIn}><LogIn className="mr-2 h-4 w-4" />Check in</Button>}
      </CardContent></Card>
      <Card><CardHeader><CardTitle>Attendance summary</CardTitle></CardHeader><CardContent>
        {history.data?.summary && <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-5">{Object.entries(history.data.summary).map(([key, value]) => <div key={key} className="rounded-lg bg-slate-50 p-3"><p className="text-xs text-muted-foreground">{key.replace('_', ' ')}</p><p className="mt-1 text-lg font-bold">{String(value)}</p></div>)}</div>}
        {history.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : history.isError ? <p role="alert" className="text-sm text-danger">Could not load your attendance history.</p> : history.data?.items?.length ? <div className="overflow-x-auto"><table className="w-full min-w-[600px] text-left text-sm"><thead className="border-b text-xs uppercase text-muted-foreground"><tr><th className="p-3">Date</th><th className="p-3">Check in</th><th className="p-3">Check out</th><th className="p-3">Hours</th><th className="p-3">Status</th></tr></thead><tbody className="divide-y">{history.data.items.map((record) => <tr key={record.id}><td className="p-3">{record.work_date}</td><td className="p-3">{record.check_in_time || '—'}</td><td className="p-3">{record.check_out_time || '—'}</td><td className="p-3">{record.working_hours ?? '—'}</td><td className="p-3"><Badge variant={record.status === 'present' ? 'success' : 'secondary'}>{record.status}</Badge></td></tr>)}</tbody></table></div> : <p className="py-6 text-center text-sm text-muted-foreground">No attendance history yet.</p>}
      </CardContent></Card>
    </div>
  );
};

export default AttendancePage;
