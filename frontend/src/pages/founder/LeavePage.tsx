import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { leavesApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export const LeavePage: React.FC = () => {
  const queryClient = useQueryClient();
  const leaves = useQuery({ queryKey: ['leaves'], queryFn: leavesApi.list });
  const decide = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'approved' | 'rejected' }) => leavesApi.decide(id, action),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['leaves'] }); toast.success('Leave request updated.'); },
    onError: (error) => toast.error(axios.isAxiosError(error) ? String(error.response?.data?.detail || 'Request failed.') : 'Request failed.'),
  });
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><Calendar className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">Leave Management</h1><p className="text-sm text-muted-foreground">Approve or reject employee leave requests.</p></div></div>
      <Card><CardHeader><CardTitle>Leave requests</CardTitle></CardHeader><CardContent>
        {leaves.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : leaves.isError ? <p role="alert" className="text-sm text-danger">Could not load leave requests.</p> : leaves.data?.length ? <div className="space-y-3">{leaves.data.map((leave) => <div key={leave.id} className="flex flex-col gap-4 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><div className="flex items-center gap-2"><h3 className="font-semibold">{leave.employee_name}</h3><Badge variant={leave.status === 'approved' ? 'success' : leave.status === 'rejected' ? 'destructive' : 'secondary'}>{leave.status}</Badge></div><p className="mt-1 text-sm">{leave.leave_type_name}: {leave.start_date} to {leave.end_date} ({leave.total_days} days)</p><p className="mt-1 text-sm text-muted-foreground">{leave.reason}</p></div>{leave.status === 'pending' && <div className="flex gap-2"><Button variant="outline" disabled={decide.isPending} onClick={() => decide.mutate({ id: leave.id, action: 'rejected' })}>Reject</Button><Button disabled={decide.isPending} onClick={() => decide.mutate({ id: leave.id, action: 'approved' })}>Approve</Button></div>}</div>)}</div> : <p className="py-8 text-center text-sm text-muted-foreground">No leave requests yet.</p>}
      </CardContent></Card>
    </div>
  );
};

export default LeavePage;
