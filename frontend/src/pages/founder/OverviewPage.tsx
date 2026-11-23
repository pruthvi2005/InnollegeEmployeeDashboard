import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  UserCheck,
  UserX,
  Plane,
  FolderKanban,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText,
  Calendar,
  PlusCircle,
  FolderPlus,
  CheckSquare,
  Activity,
  AlertTriangle,
  RotateCcw,
  BarChart2,
} from 'lucide-react';
import { format } from 'date-fns';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useOverviewStats } from '@/hooks/useAnalytics';
import { activityApi } from '@/lib/api';
import { StatCard } from '@/components/shared/StatCard';
import { StatCardSkeleton } from '@/components/shared/LoadingSkeleton';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatRelativeTime } from '@/lib/utils';

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch, isFetching } = useOverviewStats();
  const activityQuery = useQuery({
    queryKey: ['activity', 'recent'],
    queryFn: () => activityApi.recent(5),
    refetchInterval: 15000,
  });

  const todayDateFormatted = format(new Date(), 'EEEE, MMMM dd, yyyy');

  if (isError) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100 text-danger shadow-inner">
          <AlertTriangle className="h-8 w-8" />
        </div>
        <h2 className="mt-4 text-xl font-bold text-foreground">
          Failed to load overview data
        </h2>
        <p className="mt-1 text-sm text-muted-foreground max-w-md">
          {error instanceof Error ? error.message : 'An error occurred while communicating with the analytics service.'}
        </p>
        <Button
          onClick={() => refetch()}
          disabled={isFetching}
          className="mt-6 bg-primary hover:bg-navy-light"
        >
          <RotateCcw className="mr-2 h-4 w-4" />
          {isFetching ? 'Retrying...' : 'Retry'}
        </Button>
      </div>
    );
  }

  const attendanceData = data?.attendance_chart || [];
  const recentActivities = activityQuery.data || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Overview
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {todayDateFormatted}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="text-xs font-medium"
          >
            <RotateCcw className={`mr-1.5 h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            {isFetching ? 'Refreshing...' : 'Refresh Data'}
          </Button>
        </div>
      </div>

      {/* Row 1: Attendance Stats (4 cards) */}
      <div>
        <h2 className="text-xs font-extrabold uppercase tracking-wider text-[#0A377B] mb-3">
          Today's Workforce
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <StatCard
                title="Total Employees"
                value={data?.total_employees ?? 0}
                icon={Users}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="rounded-2xl border-[#061B43] bg-[#061B43] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/employees')}
              />
              <StatCard
                title="Present Today"
                value={data?.present_today ?? 0}
                icon={UserCheck}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="rounded-2xl border-[#0A377B] bg-[#0A377B] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/attendance')}
              />
              <StatCard
                title="Absent Today"
                value={data?.absent_today ?? 0}
                icon={UserX}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="rounded-2xl border-[#1053B6] bg-[#1053B6] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/attendance')}
              />
              <StatCard
                title="On Leave"
                value={data?.on_leave_today ?? 0}
                icon={Plane}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-white"
                valueClassName="text-white"
                className="rounded-2xl border-[#0675E5] bg-[#0675E5] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/leaves')}
              />
            </>
          )}
        </div>
      </div>

      {/* Row 2: Task & Project Stats (4 cards) */}
      <div>
        <h2 className="text-xs font-extrabold uppercase tracking-wider text-[#0A377B] mb-3">
          Projects & Execution
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <StatCard
                title="Active Projects"
                value={data?.active_projects ?? 0}
                icon={FolderKanban}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="rounded-2xl border-[#0A377B] bg-[#0A377B] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/projects')}
              />
              <StatCard
                title="In Progress Tasks"
                value={data?.in_progress_tasks ?? 0}
                icon={Clock}
                iconColor="text-[#061B43]"
                iconBgColor="bg-white/70"
                titleClassName="font-bold text-[#061B43]"
                valueClassName="text-[#061B43]"
                className="rounded-2xl border-[#008FFF] bg-[#008FFF] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/tasks')}
              />
              <StatCard
                title="Completed Tasks"
                value={data?.completed_tasks ?? 0}
                icon={CheckCircle}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="rounded-2xl border-[#1053B6] bg-[#1053B6] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/tasks')}
              />
              <StatCard
                title="Overdue Tasks"
                value={data?.overdue_tasks ?? 0}
                icon={AlertCircle}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="rounded-2xl border-[#061B43] bg-[#061B43] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/tasks')}
              />
            </>
          )}
        </div>
      </div>

      {/* Row 3: Approvals & Operations (2 cards) */}
      <div>
        <h2 className="text-xs font-extrabold uppercase tracking-wider text-[#0A377B] mb-3">
          Pending Approvals
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
          {isLoading ? (
            Array.from({ length: 2 }).map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <StatCard
                title="Pending Daily Reports"
                value={data?.pending_reports ?? 0}
                icon={FileText}
                iconColor="text-[#061B43]"
                iconBgColor="bg-white/70"
                titleClassName="font-bold text-[#061B43]"
                valueClassName="text-[#061B43]"
                className="rounded-2xl border-[#008FFF] bg-[#008FFF] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/reports')}
              />
              <StatCard
                title="Pending Leave Requests"
                value={data?.pending_leaves ?? 0}
                icon={Calendar}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="rounded-2xl border-[#0A377B] bg-[#0A377B] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/founder/leaves')}
              />
            </>
          )}
        </div>
      </div>

      {/* Row 4: 2-Column Grid (Recent Activity & Quick Actions) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Recent Activity (2 cols wide) */}
        <Card className="lg:col-span-2 overflow-hidden border-2 border-[#0A377B]/30 shadow-lg shadow-blue-900/10">
          <CardHeader className="flex flex-row items-center justify-between bg-[#0A377B] pb-3 text-white">
            <div>
              <CardTitle className="text-base font-extrabold text-white">
                Recent Activity
              </CardTitle>
              <p className="text-xs text-blue-100 mt-0.5">
                Latest updates across tasks, check-ins, and reports
              </p>
            </div>
            <button type="button" onClick={() => navigate('/founder/live-activity')} className="rounded-lg p-2 text-[#8bd5ff] hover:bg-white/10" aria-label="View all activity">
              <Activity className="h-5 w-5" />
            </button>
          </CardHeader>
          <CardContent>
            {activityQuery.isLoading ? (
              <div className="space-y-4 py-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-center space-x-3">
                    <div className="h-9 w-9 rounded-full bg-slate-200 animate-pulse shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 w-40 bg-slate-200 animate-pulse rounded" />
                      <div className="h-2.5 w-24 bg-slate-100 animate-pulse rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : activityQuery.isError ? (
              <p role="alert" className="py-8 text-center text-sm text-danger">Could not load recent activity.</p>
            ) : recentActivities.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                  <Activity className="h-6 w-6" />
                </div>
                <p className="mt-3 text-sm font-semibold text-foreground">No recent activity</p>
                <p className="text-xs text-muted-foreground max-w-xs mt-1">
                  Team activities such as clock-ins, daily reports, and task updates will show here.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {recentActivities.slice(0, 5).map((act) => (
                  <div key={act.id} className="flex items-start gap-3 rounded-xl border border-[#b9dfff] bg-[#eff7ff] p-3">
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#1053B6] text-white">
                      <Activity className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        <span className="font-extrabold text-[#1053B6]">{act.actor_name}</span>{' '}
                        {act.event_type.replace(/[_-]/g, ' ')}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {formatRelativeTime(act.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right: Quick Actions */}
        <Card className="overflow-hidden border-2 border-[#1053B6]/30 shadow-lg shadow-blue-900/10">
          <CardHeader className="bg-[#1053B6] pb-3 text-white">
            <CardTitle className="text-base font-extrabold text-white">
              Quick Actions
            </CardTitle>
            <p className="text-xs text-blue-100 mt-0.5">
              Rapid administrative shortcuts
            </p>
          </CardHeader>
          <CardContent className="space-y-3 pt-1">
            <Button
              onClick={() => navigate('/founder/employees')}
              className="w-full justify-start bg-[#061B43] hover:bg-[#0A377B] text-white text-xs font-extrabold h-11"
            >
              <PlusCircle className="mr-2.5 h-4 w-4 text-[#8bd5ff]" />
              Add New Employee
            </Button>
            <Button
              onClick={() => navigate('/founder/projects')}
              className="w-full justify-start bg-[#0A377B] hover:bg-[#1053B6] text-white text-xs font-extrabold h-11"
            >
              <FolderPlus className="mr-2.5 h-4 w-4 text-[#8bd5ff]" />
              Create Project
            </Button>
            <Button
              onClick={() => navigate('/founder/tasks')}
              className="w-full justify-start bg-[#1053B6] hover:bg-[#0675E5] text-white text-xs font-extrabold h-11"
            >
              <CheckSquare className="mr-2.5 h-4 w-4 text-white" />
              Create Task
            </Button>
            <Button
              onClick={() => navigate('/founder/reports')}
              className="w-full justify-start bg-[#0675E5] hover:bg-[#008FFF] text-white text-xs font-extrabold h-11"
            >
              <FileText className="mr-2.5 h-4 w-4 text-white" />
              Review Daily Reports
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Row 5: Full-Width Attendance Overview Chart */}
      <Card className="overflow-hidden border-2 border-[#061B43]/30 shadow-lg shadow-blue-900/10">
        <CardHeader className="flex flex-row items-center justify-between bg-[#061B43] text-white">
          <div>
            <CardTitle className="text-base font-extrabold text-white">
              Attendance Overview
            </CardTitle>
            <p className="text-xs text-blue-100 mt-0.5">
              Weekly team presence, absence, and approved leaves
            </p>
          </div>
          <BarChart2 className="h-5 w-5 text-[#8bd5ff]" />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin h-8 w-8 border-3 border-accent border-t-transparent rounded-full" />
            </div>
          ) : attendanceData.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-14 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                <BarChart2 className="h-6 w-6" />
              </div>
              <p className="mt-3 text-sm font-semibold text-foreground">
                No attendance records for this period
              </p>
              <p className="text-xs text-muted-foreground max-w-sm mt-1">
                Attendance logs will populate this chart as employees check in and record their work hours.
              </p>
            </div>
          ) : (
            <div className="h-72 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={attendanceData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                      fontSize: '12px',
                    }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ paddingTop: '12px', fontSize: '12px' }} />
                  <Bar dataKey="present" name="Present" fill="#1053B6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="absent" name="Absent" fill="#061B43" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="leave" name="On Leave" fill="#008FFF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default OverviewPage;
