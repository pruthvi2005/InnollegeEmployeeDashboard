import React, { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { FileText, Save, Send } from 'lucide-react';
import { toast } from 'sonner';
import { reportsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const getErrorMessage = (detail: unknown): string => {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((issue: unknown) => {
      if (typeof issue === 'object' && issue !== null && 'msg' in issue) {
        const message = String(issue.msg);
        const location = 'loc' in issue && Array.isArray(issue.loc)
          ? issue.loc.filter((part: unknown) => part !== 'body').join(' → ')
          : '';
        return location ? `${location}: ${message}` : message;
      }
      return String(issue);
    }).join('; ');
  }
  return 'Request failed.';
};

export const ReportsPage: React.FC = () => {
  const dateParts = new Intl.DateTimeFormat('en', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const today = `${dateParts.find((part) => part.type === 'year')?.value}-${dateParts.find((part) => part.type === 'month')?.value}-${dateParts.find((part) => part.type === 'day')?.value}`;
  const [form, setForm] = useState({ completed_work: '', pending_work: '', challenges: '', tomorrow_plan: '', total_hours_worked: '' });
  const queryClient = useQueryClient();
  const reports = useQuery({ queryKey: ['reports'], queryFn: () => reportsApi.list() });
  const todayReport = reports.data?.find((report) => report.report_date === today);
  const isLocked = todayReport?.status === 'submitted' || todayReport?.status === 'reviewed';
  useEffect(() => {
    if (todayReport?.status === 'draft') {
      setForm({
        completed_work: todayReport.completed_work || '',
        pending_work: todayReport.pending_work || '',
        challenges: todayReport.challenges || '',
        tomorrow_plan: todayReport.tomorrow_plan || '',
        total_hours_worked: todayReport.total_hours_worked?.toString() || '',
      });
    }
  }, [todayReport]);
  const submit = useMutation({
    mutationFn: (status: 'draft' | 'submitted') => reportsApi.submit({
      report_date: today,
      completed_work: form.completed_work,
      pending_work: form.pending_work,
      challenges: form.challenges,
      tomorrow_plan: form.tomorrow_plan,
      total_hours_worked: form.total_hours_worked ? Number(form.total_hours_worked) : undefined,
      task_items: [],
      status,
    }),
    onSuccess: async (_, status) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['reports'] }),
        queryClient.invalidateQueries({ queryKey: ['reports', 'today'] }),
      ]);
      toast.success(status === 'draft' ? 'Draft saved.' : 'Daily report submitted.');
    },
    onError: (error) => toast.error(axios.isAxiosError(error) ? getErrorMessage(error.response?.data?.detail) : 'Request failed.'),
  });
  const submitReport = (status: 'draft' | 'submitted') => {
    const hours = form.total_hours_worked.trim();
    if (hours && (!Number.isFinite(Number(hours)) || Number(hours) < 0 || Number(hours) > 24)) {
      toast.error('Total hours worked must be between 0 and 24.');
      return;
    }
    submit.mutate(status);
  };
  const update = (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm((current) => ({ ...current, [field]: event.target.value }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><FileText className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">Daily Reports</h1><p className="text-sm text-muted-foreground">Submit your work summary and track founder feedback.</p></div></div>
      <Card><CardHeader><CardTitle>Today's report · {today}</CardTitle></CardHeader><CardContent>
        {isLocked && <p className="mb-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">Today's report has been submitted and cannot be changed.</p>}
        <div className="grid gap-4 sm:grid-cols-2">
        {(['completed_work', 'pending_work', 'challenges', 'tomorrow_plan'] as const).map((field) => <label key={field} className="space-y-1 text-sm font-medium">{field.replace('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())}<textarea disabled={isLocked} className="min-h-24 w-full rounded-md border px-3 py-2 text-sm disabled:bg-slate-50" value={form[field]} onChange={update(field)} /></label>)}
        <label className="space-y-1 text-sm font-medium">Total hours worked<Input disabled={isLocked} type="number" min="0" max="24" step="0.25" value={form.total_hours_worked} onChange={update('total_hours_worked')} /></label>
      </div><div className="mt-5 flex gap-3"><Button variant="outline" disabled={submit.isPending || isLocked} onClick={() => submitReport('draft')}><Save className="mr-2 h-4 w-4" />Save draft</Button><Button disabled={submit.isPending || isLocked} onClick={() => submitReport('submitted')}><Send className="mr-2 h-4 w-4" />Submit report</Button></div></CardContent></Card>
      <Card><CardHeader><CardTitle>My reports</CardTitle></CardHeader><CardContent>{reports.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : reports.isError ? <p role="alert" className="text-sm text-danger">Could not load reports.</p> : reports.data?.length ? <div className="space-y-3">{reports.data.map((report) => <div key={report.id} className="rounded-xl border p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">{report.report_date}</h3><Badge variant={report.status === 'reviewed' ? 'success' : 'secondary'}>{report.status}</Badge></div><p className="mt-2 text-sm">{report.completed_work || 'No completed work entered.'}</p>{report.founder_feedback && <p className="mt-2 rounded-md bg-slate-50 p-3 text-sm"><strong>Founder feedback:</strong> {report.founder_feedback}</p>}</div>)}</div> : <p className="py-8 text-center text-sm text-muted-foreground">No reports submitted yet.</p>}</CardContent></Card>
    </div>
  );
};

export default ReportsPage;
