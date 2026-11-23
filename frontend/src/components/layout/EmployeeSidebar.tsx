import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderKanban,
  CheckSquare,
  Clock,
  FileText,
  Calendar,
  Bell,
  User,
  LogOut,
  X,
  Briefcase,
} from 'lucide-react';
import { cn, getInitials } from '@/lib/utils';
import { useAuthStore } from '@/store/authStore';
import { useNotificationStore } from '@/store/notificationStore';
import { useLogoutMutation } from '@/hooks/useAuth';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { BrandLogo } from '@/components/shared/BrandLogo';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number | string;
}

interface EmployeeSidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const EmployeeSidebar: React.FC<EmployeeSidebarProps> = ({
  isOpen = false,
  onClose,
}) => {
  const user = useAuthStore((s) => s.user);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const logoutMutation = useLogoutMutation();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const navItems: NavItem[] = [
    { name: 'My Dashboard', href: '/employee/dashboard', icon: LayoutDashboard },
    { name: 'My Projects', href: '/employee/projects', icon: FolderKanban },
    { name: 'My Tasks', href: '/employee/tasks', icon: CheckSquare },
    { name: 'Attendance', href: '/employee/attendance', icon: Clock },
    { name: 'Daily Reports', href: '/employee/reports', icon: FileText },
    { name: 'Leave Requests', href: '/employee/leaves', icon: Calendar },
    {
      name: 'Notifications',
      href: '/employee/notifications',
      icon: Bell,
      badge: unreadCount > 0 ? unreadCount : undefined,
    },
    { name: 'My Profile', href: '/employee/profile', icon: User },
  ];

  const handleLogout = () => {
    logoutMutation.mutate();
    setShowLogoutConfirm(false);
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden transition-opacity duration-300"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-[#0A377B] text-white shadow-xl transition-transform duration-300 ease-in-out lg:static lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo and Brand Header */}
        <div className="flex h-16 shrink-0 items-center justify-between px-6 border-b border-white/10">
          <div className="flex items-center space-x-3">
            <BrandLogo className="h-9 w-20 shrink-0 object-contain brightness-0 invert" />
            <div className="flex flex-col">
              <span className="text-sm font-bold text-white tracking-tight">Employee Portal</span>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-slate-300 hover:bg-white/10 hover:text-white lg:hidden"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.href}
                to={item.href}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'group flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150',
                    isActive
                      ? 'bg-sidebar-active text-white shadow-sm'
                      : 'text-sidebar-text hover:bg-white/10 hover:text-white'
                  )
                }
              >
                <div className="flex items-center space-x-3">
                  <Icon className="h-4 w-4 shrink-0 transition-transform group-hover:scale-110" />
                  <span>{item.name}</span>
                </div>
                {item.badge !== undefined && (
                  <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-danger px-1.5 text-[10px] font-bold text-white">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Employee Profile Mini-Card & Logout */}
        <div className="shrink-0 border-t border-white/10 p-3 bg-black/15">
          <div className="flex items-center justify-between rounded-lg p-2 hover:bg-white/5 transition-colors">
            <div className="flex items-center space-x-3 truncate">
              <Avatar className="h-9 w-9 border border-white/20">
                <AvatarImage src={user?.employee?.profile_photo_url || ''} />
                <AvatarFallback className="bg-accent text-white text-xs font-semibold">
                  {getInitials(user?.employee?.full_name || user?.email || 'Employee')}
                </AvatarFallback>
              </Avatar>
              <div className="truncate">
                <div className="flex items-center space-x-1.5">
                  <p className="text-xs font-semibold text-white truncate max-w-[100px]">
                    {user?.employee?.full_name || 'Member'}
                  </p>
                  <Badge variant="secondary" className="h-4 px-1 text-[9px] font-medium bg-white/10 text-slate-300 border-0">
                    <Briefcase className="mr-0.5 h-2.5 w-2.5" /> Emp
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-400 truncate max-w-[130px]">
                  {user?.employee?.designation || user?.email}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowLogoutConfirm(true)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-danger transition-colors"
              title="Sign Out"
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Logout Confirmation Dialog */}
      <ConfirmDialog
        open={showLogoutConfirm}
        onOpenChange={setShowLogoutConfirm}
        title="Sign Out"
        description="Are you sure you want to end your session and sign out?"
        confirmLabel="Sign Out"
        variant="destructive"
        loading={logoutMutation.isPending}
        onConfirm={handleLogout}
      />
    </>
  );
};

export default EmployeeSidebar;
