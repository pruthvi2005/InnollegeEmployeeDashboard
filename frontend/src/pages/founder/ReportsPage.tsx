import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { FileText } from 'lucide-react';
import { toast } from 'sonner';
import { reportsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export const ReportsPage: React.FC = () => {
  const [feedbackById, setFeedbackById] = useState<Record<string, string>>({});
  const queryClient = useQueryClient();
  const reports = useQuery({ queryKey: ['reports'], queryFn: () => reportsApi.list() });
  const review = useMutation({
    mutationFn: ({ id, feedback }: { id: string; feedback: string }) => reportsApi.review(id, feedback),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['reports'] }); toast.success('Report reviewed.'); },
    onError: (error) => toast.error(axios.isAxiosError(error) ? String(error.response?.data?.detail || 'Request failed.') : 'Request failed.'),
  });
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><FileText className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">Daily Reports</h1><p className="text-sm text-muted-foreground">Review employee work summaries and give feedback.</p></div></div>
      <Card><CardHeader><CardTitle>Submitted reports</CardTitle></CardHeader><CardContent>
        {reports.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : reports.isError ? <p role="alert" className="text-sm text-danger">Could not load daily reports.</p> : reports.data?.length ? <div className="space-y-4">{reports.data.map((report) => <div key={report.id} className="rounded-xl border p-4"><div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="font-semibold">{report.employee_name}</h3><p className="text-xs text-muted-foreground">{report.report_date} · {report.total_hours_worked ?? 0} hours</p></div><Badge variant={report.status === 'reviewed' ? 'success' : 'secondary'}>{report.status}</Badge></div><div className="mt-3 grid gap-3 text-sm sm:grid-cols-2"><p><strong>Completed:</strong> {report.completed_work || '—'}</p><p><strong>Pending:</strong> {report.pending_work || '—'}</p><p><strong>Challenges:</strong> {report.challenges || '—'}</p><p><strong>Tomorrow:</strong> {report.tomorrow_plan || '—'}</p></div>{report.status !== 'draft' && report.status !== 'reviewed' && <div className="mt-4 flex flex-col gap-2 sm:flex-row"><Input value={feedbackById[report.id] || ''} onChange={(e) => setFeedbackById((current) => ({ ...current, [report.id]: e.target.value }))} placeholder="Founder feedback" /><Button disabled={review.isPending} onClick={() => review.mutate({ id: report.id, feedback: feedbackById[report.id] || '' })}>Mark reviewed</Button></div>}</div>)}</div> : <p className="py-8 text-center text-sm text-muted-foreground">No daily reports submitted yet.</p>}
      </CardContent></Card>
    </div>
  );
};

export default ReportsPage;
