import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Menu, Calendar } from 'lucide-react';
import { EmployeeSidebar } from './EmployeeSidebar';
import { NotificationBell } from '@/components/shared/NotificationBell';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useAuthStore } from '@/store/authStore';
import { getInitials } from '@/lib/utils';
import { format } from 'date-fns';

const employeeRouteTitles: Record<string, string> = {
  '/employee/dashboard': 'My Dashboard',
  '/employee/projects': 'My Projects',
  '/employee/tasks': 'My Tasks',
  '/employee/attendance': 'My Attendance',
  '/employee/reports': 'Daily Reports',
  '/employee/leaves': 'Leave Requests',
  '/employee/notifications': 'Notifications',
  '/employee/profile': 'My Profile',
};

export const EmployeeLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const [istTime, setIstTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const timeStr = new Intl.DateTimeFormat('en-IN', {
        timeZone: 'Asia/Kolkata',
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      }).format(now);
      setIstTime(timeStr);
    };

    updateTime();
    const interval = setInterval(updateTime, 30000);
    return () => clearInterval(interval);
  }, []);

  const pageTitle = employeeRouteTitles[location.pathname] || 'Employee Portal';

  return (
    <div className="flex min-h-screen bg-surface">
      {/* Employee Sidebar */}
      <EmployeeSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Body */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header Bar */}
        <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-border bg-white/95 px-4 sm:px-6 backdrop-blur">
          {/* Left: Mobile menu & Page Title */}
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden focus:outline-none focus:ring-2 focus:ring-accent"
              aria-label="Open navigation menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-foreground tracking-tight sm:text-xl">
                {pageTitle}
              </h1>
            </div>
          </div>

          {/* Right: Date, Notification Bell, User Avatar */}
          <div className="flex items-center space-x-3 sm:space-x-5">
            {/* IST Date/Time badge */}
            <div className="hidden md:flex items-center space-x-1.5 rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">
              <Calendar className="h-3.5 w-3.5 text-slate-500" />
              <span>{istTime || format(new Date(), 'EEE, dd MMM yyyy')} (IST)</span>
            </div>

            {/* Notification Bell */}
            <NotificationBell />

            {/* User Profile Badge */}
            <div className="flex items-center space-x-2 pl-1 sm:pl-2 border-l border-border">
              <Avatar className="h-8 w-8 sm:h-9 sm:w-9 border border-border">
                <AvatarImage src={user?.employee?.profile_photo_url || ''} />
                <AvatarFallback className="bg-primary text-white text-xs font-bold">
                  {getInitials(user?.employee?.full_name || user?.email || 'User')}
                </AvatarFallback>
              </Avatar>
              <div className="hidden xl:block text-left">
                <p className="text-xs font-semibold leading-tight text-foreground truncate max-w-[120px]">
                  {user?.employee?.full_name || 'Team Member'}
                </p>
                <p className="text-[10px] text-muted-foreground truncate max-w-[120px]">
                  {user?.employee?.designation || 'Employee'}
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Content Outlet */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default EmployeeLayout;
