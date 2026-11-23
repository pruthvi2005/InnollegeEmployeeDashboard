import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Clock,
  LogIn,
  LogOut,
  CheckSquare,
  FileCheck2,
  Calendar,
  Hourglass,
  CheckCircle2,
  Bell,
  Send,
} from 'lucide-react';
import { format } from 'date-fns';
import { useAuthStore } from '@/store/authStore';
import { attendanceApi, tasksApi, reportsApi } from '@/lib/api';
import { useNotifications } from '@/hooks/useNotifications';
import { StatCard } from '@/components/shared/StatCard';
import { StatCardSkeleton } from '@/components/shared/LoadingSkeleton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  formatWorkingHours,
  getPriorityColor,
  getStatusColor,
  getAttendanceStatusColor,
  formatRelativeTime,
} from '@/lib/utils';
import { toast } from 'sonner';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);

  // Time and Greeting
  const currentHour = new Date().getHours();
  const greeting =
    currentHour < 12 ? 'Good morning' : currentHour < 17 ? 'Good afternoon' : 'Good evening';
  const todayFormatted = format(new Date(), 'EEEE, dd MMMM yyyy');

  // Query: Attendance status today
  const attendanceQuery = useQuery({
    queryKey: ['attendance', 'today'],
    queryFn: attendanceApi.todayStatus,
    staleTime: 30000,
  });

  // Query: Tasks today
  const tasksQuery = useQuery({
    queryKey: ['tasks', 'myToday'],
    queryFn: tasksApi.myTodayTasks,
    staleTime: 30000,
  });

  // Query: Daily report today
  const reportQuery = useQuery({
    queryKey: ['reports', 'today'],
    queryFn: reportsApi.todayStatus,
    staleTime: 30000,
  });

  // Query: Notifications (top 5)
  const { data: notificationsData, isLoading: notificationsLoading, isError: notificationsError } = useNotifications({ page: 1, page_size: 5 });

  // Mutation: Check in
  const checkInMutation = useMutation({
    mutationFn: async () => {
      return await attendanceApi.checkIn();
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['attendance', 'today'], data);
      void queryClient.invalidateQueries({ queryKey: ['attendance', 'me'] });
      toast.success('Check-in recorded successfully. Have a productive day!');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to record check-in.');
    },
  });

  // Mutation: Check out
  const checkOutMutation = useMutation({
    mutationFn: async () => {
      return await attendanceApi.checkOut();
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['attendance', 'today'], data);
      void queryClient.invalidateQueries({ queryKey: ['attendance', 'me'] });
      toast.info('Check-out recorded successfully. Great work today!');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to record check-out.');
    },
  });

  const attendance = attendanceQuery.data;
  const isCheckedIn = Boolean(attendance?.check_in_time);
  const isCheckedOut = Boolean(attendance?.check_out_time);
  const taskCounts = tasksQuery.data?.counts || { assigned: 0, pending: 0, in_progress: 0, completed_today: 0 };
  const todayTasks = tasksQuery.data?.items || [];
  const reportStatus = reportQuery.data?.status || 'not_submitted';

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {(attendanceQuery.isError || tasksQuery.isError || reportQuery.isError || notificationsError) && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          Some dashboard information could not be loaded.
          {attendanceQuery.isError && <p>Attendance is unavailable. Use the Attendance page to retry.</p>}
          {tasksQuery.isError && <p>Tasks are unavailable. Use My Tasks to retry.</p>}
          {reportQuery.isError && <p>Daily report status is unavailable. Use Daily Reports to retry.</p>}
          {notificationsError && <p>Notifications are unavailable.</p>}
        </div>
      )}
      {/* 1. Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#061B43] via-[#0A377B] to-[#1053B6] p-6 sm:p-8 text-white shadow-xl shadow-blue-900/10">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl text-white">
              {greeting}, {user?.employee?.full_name || 'Team Member'}
            </h1>
            <p className="text-xs sm:text-sm text-slate-200 flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <span>{todayFormatted} (IST)</span>
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-300">Status:</span>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${
                isCheckedIn
                  ? 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/30'
                  : 'bg-amber-500/20 text-amber-200 border border-amber-400/30'
              }`}
            >
              <span
                className={`mr-1.5 h-2 w-2 rounded-full ${
                  isCheckedIn ? 'bg-emerald-400' : 'bg-amber-400'
                }`}
              />
              {isCheckedIn ? 'Checked In' : 'Not Checked In'}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Attendance Control Card */}
      <Card className="border-2 border-[#1053B6]/30 bg-[#eff7ff] shadow-lg shadow-blue-900/10">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-[#0675E5]" />
                <h2 className="text-base font-extrabold text-[#061B43]">
                  Today's Attendance Control
                </h2>
                <Badge
                  variant="outline"
                  className={getAttendanceStatusColor(attendance?.status || 'not_checked_in')}
                >
                  {attendance?.status === 'present'
                    ? 'Present'
                    : attendance?.status === 'leave'
                    ? 'On Leave'
                    : 'Not Checked In'}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-6 text-xs text-[#0A377B] pt-1">
                <div>
                  <span className="font-bold text-[#0A377B]">Check-in: </span>
                  <span className="font-mono text-foreground font-semibold">
                    {attendance?.check_in_time || '--:--'}
                  </span>
                </div>
                <div>
                  <span className="font-bold text-[#0A377B]">Check-out: </span>
                  <span className="font-mono text-foreground font-semibold">
                    {attendance?.check_out_time || '--:--'}
                  </span>
                </div>
                <div>
                  <span className="font-bold text-[#0A377B]">Hours Recorded: </span>
                  <span className="font-extrabold text-[#0675E5]">
                    {formatWorkingHours(attendance?.working_hours ?? 0)}
                  </span>
                </div>
              </div>
            </div>

            {/* Check-in / Check-out Action Button */}
            <div className="shrink-0">
              {isCheckedIn && !isCheckedOut ? (
                <Button
                  onClick={() => checkOutMutation.mutate()}
                  disabled={checkOutMutation.isPending}
                  className="w-full sm:w-auto bg-[#061B43] hover:bg-[#0A377B] text-white font-bold px-6 h-11"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  {checkOutMutation.isPending ? 'Recording Check-out...' : 'Check Out Now'}
                </Button>
              ) : !isCheckedIn ? (
                <Button
                  onClick={() => checkInMutation.mutate()}
                  disabled={checkInMutation.isPending}
                  className="w-full sm:w-auto bg-[#0675E5] hover:bg-[#1053B6] text-white font-bold px-6 h-11"
                >
                  <LogIn className="mr-2 h-4 w-4" />
                  {checkInMutation.isPending ? 'Recording Check-in...' : 'Check In Now'}
                </Button>
              ) : <Badge variant="success">Checked out for today</Badge>}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3. Task Stats Row (4 cards) */}
      <div>
        <h3 className="text-xs font-extrabold uppercase tracking-wider text-[#0A377B] mb-3">
          My Task Progress
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          {tasksQuery.isLoading ? (
            Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <StatCard
                title="Assigned Tasks"
                value={taskCounts.assigned}
                icon={CheckSquare}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="border-[#061B43] bg-[#061B43] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/employee/tasks')}
              />
              <StatCard
                title="Pending Tasks"
                value={taskCounts.pending}
                icon={Hourglass}
                iconColor="text-[#061B43]"
                iconBgColor="bg-white/70"
                titleClassName="font-bold text-[#061B43]"
                valueClassName="text-[#061B43]"
                className="border-[#008FFF] bg-[#008FFF] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/employee/tasks')}
              />
              <StatCard
                title="In Progress"
                value={taskCounts.in_progress}
                icon={Clock}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="border-[#1053B6] bg-[#1053B6] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/employee/tasks')}
              />
              <StatCard
                title="Completed Today"
                value={taskCounts.completed_today}
                icon={CheckCircle2}
                iconColor="text-white"
                iconBgColor="bg-white/15"
                titleClassName="font-bold text-blue-100"
                valueClassName="text-white"
                className="border-[#0A377B] bg-[#0A377B] shadow-lg shadow-blue-950/15"
                onClick={() => navigate('/employee/tasks')}
              />
            </>
          )}
        </div>
      </div>

      {/* 4. Two-Column Grid: Today's Tasks & Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Today's Tasks */}
        <Card className="overflow-hidden border-2 border-[#1053B6]/30 shadow-lg shadow-blue-900/10">
          <CardHeader className="flex flex-row items-center justify-between bg-[#0A377B] pb-3 text-white">
            <div>
              <CardTitle className="text-base font-extrabold text-white">
                Today's Tasks
              </CardTitle>
              <p className="text-xs text-blue-100 mt-0.5">
                Tasks scheduled or due for completion today
              </p>
            </div>
            <CheckSquare className="h-5 w-5 text-[#008FFF]" />
          </CardHeader>
          <CardContent>
            {tasksQuery.isLoading ? (
              <div className="space-y-3 py-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-16 rounded-lg bg-slate-100 animate-pulse" />
                ))}
              </div>
            ) : todayTasks.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                  <CheckCircle2 className="h-6 w-6" />
                </div>
                <p className="mt-3 text-sm font-semibold text-foreground">
                  No tasks assigned for today
                </p>
                <p className="text-xs text-muted-foreground max-w-xs mt-1">
                  Enjoy your day or consult with your project lead for upcoming work items.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {todayTasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => navigate('/employee/tasks')}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') navigate('/employee/tasks');
                    }}
                    role="button"
                    tabIndex={0}
                    className="flex cursor-pointer items-center justify-between rounded-xl border-l-4 border-l-[#0675E5] border-y border-r border-[#b9dfff] bg-[#eff7ff] p-3.5 transition-all hover:border-[#008FFF] hover:bg-[#dbeeff]"
                  >
                    <div className="space-y-1 truncate pr-3">
                      <p className="text-sm font-semibold text-foreground truncate">
                        {task.title}
                      </p>
                      <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                        {task.project_name && <span>{task.project_name}</span>}
                        {task.due_date && <span>• Due {format(new Date(task.due_date), 'dd MMM')}</span>}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 shrink-0">
                      <Badge variant="outline" className={getPriorityColor(task.priority)}>
                        {task.priority}
                      </Badge>
                      <Badge variant="outline" className={getStatusColor(task.status)}>
                        {task.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right: Notifications */}
        <Card className="overflow-hidden border-2 border-[#008FFF]/40 shadow-lg shadow-blue-900/10">
          <CardHeader className="flex flex-row items-center justify-between bg-[#1053B6] pb-3 text-white">
            <div>
              <CardTitle className="text-base font-extrabold text-white">
                Recent Notifications
              </CardTitle>
              <p className="text-xs text-blue-100 mt-0.5">
                Latest company broadcasts and team alerts
              </p>
            </div>
            <Bell className="h-5 w-5 text-[#8bd5ff]" />
          </CardHeader>
          <CardContent>
            {notificationsLoading ? (
              <div className="space-y-3 py-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-14 rounded-lg bg-slate-100 animate-pulse" />
                ))}
              </div>
            ) : notificationsError ? (
              <p role="alert" className="py-6 text-center text-sm text-danger">Could not load notifications.</p>
            ) : !notificationsData?.items || notificationsData.items.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                  <Bell className="h-6 w-6" />
                </div>
                <p className="mt-3 text-sm font-semibold text-foreground">
                  No notifications yet
                </p>
                <p className="text-xs text-muted-foreground max-w-xs mt-1">
                  System notices and task assignments will appear here.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-[#b9dfff]">
                {notificationsData.items.slice(0, 5).map((n) => (
                  <div key={n.id} className="my-1 rounded-lg border-l-4 border-[#008FFF] bg-[#eff7ff] px-3 py-3 first:mt-0 last:mb-0">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold text-foreground truncate max-w-[200px]">
                        {n.title}
                      </p>
                      <span className="text-[10px] text-muted-foreground">
                        {formatRelativeTime(n.created_at)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                      {n.message}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 5. Daily Report Status Card */}
      <Card className="border-2 border-[#0A377B] bg-[#0A377B] text-white shadow-xl shadow-blue-950/15">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-start space-x-3.5">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15 text-[#8bd5ff]">
                <FileCheck2 className="h-6 w-6" />
              </div>
              <div>
                <h4 className="text-sm font-extrabold text-white">
                  Daily Work Report Status
                </h4>
                <p className="text-xs text-blue-100 mt-0.5">
                  Every team member submits an end-of-day summary of accomplishments and blockers.
                </p>
                <div className="mt-2 flex items-center space-x-2">
                  <span className="text-xs font-bold text-white">Today's Status:</span>
                  <Badge
                    variant="outline"
                    className={
                      reportStatus === 'submitted'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : reportStatus === 'draft'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    }
                  >
                    {reportStatus === 'submitted'
                      ? 'Submitted'
                      : reportStatus === 'draft'
                      ? 'Draft in Progress'
                      : 'Not Submitted'}
                  </Badge>
                </div>
              </div>
            </div>

            <Button
              onClick={() => navigate('/employee/reports')}
              className="bg-[#008FFF] hover:bg-[#0675E5] text-[#061B43] text-xs font-extrabold h-10 px-5 shrink-0"
            >
              <Send className="mr-2 h-4 w-4" />
              {reportStatus === 'submitted' ? 'View Submitted Report' : 'Submit Today’s Report'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardPage;
