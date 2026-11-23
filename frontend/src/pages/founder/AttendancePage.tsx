import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock } from 'lucide-react';
import { attendanceApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export const AttendancePage: React.FC = () => {
  const attendance = useQuery({ queryKey: ['attendance', 'all'], queryFn: () => attendanceApi.list() });
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><Clock className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">Attendance</h1><p className="text-sm text-muted-foreground">Monitor employee check-in and check-out records.</p></div></div>
      <Card><CardHeader><CardTitle>Attendance records</CardTitle></CardHeader><CardContent>
        {attendance.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : attendance.isError ? <p role="alert" className="text-sm text-danger">Could not load attendance records.</p> : attendance.data?.length ? <div className="overflow-x-auto"><table className="w-full min-w-[700px] text-left text-sm"><thead className="border-b text-xs uppercase text-muted-foreground"><tr><th className="p-3">Employee</th><th className="p-3">Date</th><th className="p-3">Check in</th><th className="p-3">Check out</th><th className="p-3">Hours</th><th className="p-3">Status</th></tr></thead><tbody className="divide-y">{attendance.data.map((record) => <tr key={record.id}><td className="p-3 font-medium">{record.employee_name}</td><td className="p-3">{record.work_date}</td><td className="p-3">{record.check_in_time || '—'}</td><td className="p-3">{record.check_out_time || '—'}</td><td className="p-3">{record.working_hours ?? '—'}</td><td className="p-3"><Badge variant={record.status === 'present' ? 'success' : 'secondary'}>{record.status}{record.is_late ? ' · late' : ''}</Badge></td></tr>)}</tbody></table></div> : <p className="py-8 text-center text-sm text-muted-foreground">No attendance records found.</p>}
      </CardContent></Card>
    </div>
  );
};

export default AttendancePage;
