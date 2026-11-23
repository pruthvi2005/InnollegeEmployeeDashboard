import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, CheckCircle2, Clock3, Target, Users } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { analyticsApi } from '@/lib/api';
import { StatCard } from '@/components/shared/StatCard';
import { StatCardSkeleton } from '@/components/shared/LoadingSkeleton';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const attendanceColors = ['#047857', '#be123c', '#d97706'];

export const AnalyticsPage: React.FC = () => {
  const attendance = useQuery({ queryKey: ['analytics', 'attendance'], queryFn: analyticsApi.attendance, refetchInterval: 60000 });
  const tasks = useQuery({ queryKey: ['analytics', 'tasks'], queryFn: analyticsApi.tasks, refetchInterval: 60000 });
  const attendanceData = attendance.data
    ? [
        { name: 'Present', value: attendance.data.total_present },
        { name: 'Absent', value: attendance.data.total_absent },
        { name: 'On leave', value: attendance.data.total_leaves },
      ]
    : [];
  const employeeTasks = tasks.data?.by_employee.filter((employee) => employee.assigned_count > 0) ?? [];

  return (
    <div className="mx-auto max-w-7xl space-y-7">
      <div className="border-b border-amber-200 pb-5">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-amber-700">Executive insights</p>
        <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-slate-950">Analytics</h1>
        <p className="mt-1 text-sm text-slate-500">Attendance and delivery performance across your organization.</p>
      </div>

      {attendance.isError || tasks.isError ? (
        <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          Some analytics could not be loaded. Please refresh the page or try again shortly.
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {attendance.isLoading || tasks.isLoading ? (
          Array.from({ length: 4 }, (_, index) => <StatCardSkeleton key={index} />)
        ) : (
          <>
            <StatCard title="Attendance rate" value={`${attendance.data?.average_attendance_rate ?? 0}%`} icon={Users} iconColor="text-emerald-800" iconBgColor="bg-emerald-100" className="border-emerald-200 bg-gradient-to-br from-emerald-50 to-white" />
            <StatCard title="Attendance records" value={attendance.data?.total_expected ?? 0} icon={Activity} iconColor="text-blue-800" iconBgColor="bg-blue-100" className="border-blue-200 bg-gradient-to-br from-blue-50 to-white" />
            <StatCard title="Task completion" value={`${tasks.data?.overall_completion_rate ?? 0}%`} icon={Target} iconColor="text-violet-800" iconBgColor="bg-violet-100" className="border-violet-200 bg-gradient-to-br from-violet-50 to-white" />
            <StatCard title="Completed assignments" value={tasks.data?.completed_assignments ?? 0} icon={CheckCircle2} iconColor="text-amber-800" iconBgColor="bg-amber-100" className="border-amber-200 bg-gradient-to-br from-amber-50 to-white" />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-bold">Attendance distribution</CardTitle>
            <CardDescription>{attendance.data ? `${attendance.data.start_date} – ${attendance.data.end_date}` : 'Current reporting period'}</CardDescription>
          </CardHeader>
          <CardContent>
            {attendance.isLoading ? <div className="h-64 animate-pulse rounded-xl bg-slate-100" /> : attendanceData.reduce((sum, item) => sum + item.value, 0) === 0 ? (
              <p className="py-20 text-center text-sm text-slate-500">Attendance records will appear here as your team checks in.</p>
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={attendanceData} dataKey="value" nameKey="name" innerRadius={65} outerRadius={100} paddingAngle={4}>
                      {attendanceData.map((item, index) => <Cell key={item.name} fill={attendanceColors[index]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-5 text-xs font-medium text-slate-600">
                  {attendanceData.map((item, index) => (
                    <span key={item.name} className="flex items-center gap-1.5">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: attendanceColors[index] }} />
                      {item.name}: {item.value}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-bold">Task completion by employee</CardTitle>
            <CardDescription>Completed assignments compared with each employee’s workload.</CardDescription>
          </CardHeader>
          <CardContent>
            {tasks.isLoading ? <div className="h-64 animate-pulse rounded-xl bg-slate-100" /> : employeeTasks.length === 0 ? (
              <p className="py-20 text-center text-sm text-slate-500">Task assignments will appear here when work is assigned.</p>
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={employeeTasks} margin={{ left: -18, right: 12, top: 8, bottom: 8 }}>
                    <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="employee_name" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="completed_count" name="Completed" fill="#047857" radius={[5, 5, 0, 0]} />
                    <Bar dataKey="assigned_count" name="Assigned" fill="#cbd5e1" radius={[5, 5, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {tasks.data && (
        <Card className="border-amber-200 bg-gradient-to-r from-amber-50 to-white shadow-sm">
          <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-100 text-amber-800"><Clock3 className="h-5 w-5" /></span>
              <div><p className="font-bold text-slate-900">On-time delivery</p><p className="text-sm text-slate-600">Completed assignments delivered on schedule</p></div>
            </div>
            <p className="text-3xl font-extrabold tracking-tight text-amber-800">{tasks.data.overall_on_time_rate}%</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AnalyticsPage;
