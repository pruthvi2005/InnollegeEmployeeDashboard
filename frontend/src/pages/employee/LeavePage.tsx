import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Calendar, Send } from 'lucide-react';
import { toast } from 'sonner';
import { leavesApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export const LeavePage: React.FC = () => {
  const [leaveTypeId, setLeaveTypeId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const queryClient = useQueryClient();
  const types = useQuery({ queryKey: ['leave-types'], queryFn: leavesApi.types });
  const leaves = useQuery({ queryKey: ['leaves'], queryFn: leavesApi.list });
  const submit = useMutation({
    mutationFn: () => leavesApi.create({ leave_type_id: leaveTypeId, start_date: startDate, end_date: endDate, reason: reason.trim() }),
    onSuccess: async () => { setLeaveTypeId(''); setStartDate(''); setEndDate(''); setReason(''); await queryClient.invalidateQueries({ queryKey: ['leaves'] }); toast.success('Leave request submitted.'); },
    onError: (error) => toast.error(axios.isAxiosError(error) ? String(error.response?.data?.detail || 'Request failed.') : 'Request failed.'),
  });
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><Calendar className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">Leave Requests</h1><p className="text-sm text-muted-foreground">Apply for leave and track request status.</p></div></div>
      <Card><CardHeader><CardTitle>Apply for leave</CardTitle></CardHeader><CardContent>{types.isError && <p role="alert" className="mb-3 text-sm text-danger">Could not load leave types. Please refresh the page.</p>}<form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); submit.mutate(); }}>
        <label className="space-y-1 text-sm font-medium">Leave type<select required className="h-10 w-full rounded-md border px-3 text-sm" value={leaveTypeId} onChange={(e) => setLeaveTypeId(e.target.value)}><option value="">Select leave type</option>{types.data?.map((type) => <option key={type.id} value={type.id}>{type.name}</option>)}</select></label>
        <div className="grid grid-cols-2 gap-3"><label className="space-y-1 text-sm font-medium">Start date<Input required type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></label><label className="space-y-1 text-sm font-medium">End date<Input required type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></label></div>
        <label className="space-y-1 text-sm font-medium sm:col-span-2">Reason<textarea required className="min-h-20 w-full rounded-md border px-3 py-2 text-sm" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason for leave" /></label>
        <div className="sm:col-span-2"><Button disabled={submit.isPending}><Send className="mr-2 h-4 w-4" />{submit.isPending ? 'Submitting...' : 'Submit request'}</Button></div>
      </form></CardContent></Card>
      <Card><CardHeader><CardTitle>My requests</CardTitle></CardHeader><CardContent>{leaves.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : leaves.isError ? <p role="alert" className="text-sm text-danger">Could not load your leave requests.</p> : leaves.data?.length ? <div className="space-y-3">{leaves.data.map((leave) => <div key={leave.id} className="flex items-center justify-between rounded-xl border p-4"><div><h3 className="font-semibold">{leave.leave_type_name}</h3><p className="mt-1 text-sm text-muted-foreground">{leave.start_date} to {leave.end_date} · {leave.total_days} days</p><p className="mt-1 text-sm">{leave.reason}</p></div><Badge variant={leave.status === 'approved' ? 'success' : leave.status === 'rejected' ? 'destructive' : 'secondary'}>{leave.status}</Badge></div>)}</div> : <p className="py-8 text-center text-sm text-muted-foreground">No leave requests yet.</p>}</CardContent></Card>
    </div>
  );
};

export default LeavePage;
