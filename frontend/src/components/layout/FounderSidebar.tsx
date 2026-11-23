import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Building2,
  FolderKanban,
  CheckSquare,
  Clock,
  FileText,
  Calendar,
  Activity,
  BarChart3,
  Bell,
  Settings,
  LogOut,
  X,
  Shield,
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

interface NavSection {
  title: string;
  items: NavItem[];
}

interface FounderSidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const FounderSidebar: React.FC<FounderSidebarProps> = ({
  isOpen = false,
  onClose,
}) => {
  const user = useAuthStore((s) => s.user);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const logoutMutation = useLogoutMutation();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const navSections: NavSection[] = [
    {
      title: 'Main',
      items: [{ name: 'Overview', href: '/founder/overview', icon: LayoutDashboard }],
    },
    {
      title: 'People',
      items: [
        { name: 'Employees', href: '/founder/employees', icon: Users },
        { name: 'Departments', href: '/founder/departments', icon: Building2 },
      ],
    },
    {
      title: 'Work',
      items: [
        { name: 'Projects', href: '/founder/projects', icon: FolderKanban },
        { name: 'Task Management', href: '/founder/tasks', icon: CheckSquare },
      ],
    },
    {
      title: 'Tracking',
      items: [
        { name: 'Attendance', href: '/founder/attendance', icon: Clock },
        { name: 'Daily Reports', href: '/founder/reports', icon: FileText },
        { name: 'Leave Management', href: '/founder/leaves', icon: Calendar },
      ],
    },
    {
      title: 'Insights',
      items: [
        { name: 'Live Activity', href: '/founder/live-activity', icon: Activity },
        { name: 'Analytics', href: '/founder/analytics', icon: BarChart3 },
      ],
    },
    {
      title: 'System',
      items: [
        {
          name: 'Notifications',
          href: '/founder/notifications',
          icon: Bell,
          badge: unreadCount > 0 ? unreadCount : undefined,
        },
        { name: 'Settings', href: '/founder/settings', icon: Settings },
      ],
    },
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
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-[#061B43] text-white shadow-xl transition-transform duration-300 ease-in-out lg:static lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo and Brand Header */}
        <div className="flex h-16 shrink-0 items-center justify-between px-6 border-b border-white/10">
          <div className="flex items-center space-x-3">
            <BrandLogo className="h-9 w-20 shrink-0 object-contain brightness-0 invert" />
            <div className="flex flex-col">
              <span className="text-sm font-bold text-white tracking-tight">Founder Portal</span>
            </div>
          </div>
          {/* Close button for mobile */}
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

        {/* Navigation Groups */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navSections.map((section) => (
            <div key={section.title} className="space-y-1">
              <h4 className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                {section.title}
              </h4>
              <div className="space-y-0.5 pt-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.href}
                      to={item.href}
                      onClick={onClose}
                      className={({ isActive }) =>
                        cn(
                          'group flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150',
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
              </div>
            </div>
          ))}
        </nav>

        {/* Founder Profile Mini-Card & Logout */}
        <div className="shrink-0 border-t border-white/10 p-3 bg-black/15">
          <div className="flex items-center justify-between rounded-lg p-2 hover:bg-white/5 transition-colors">
            <div className="flex items-center space-x-3 truncate">
              <Avatar className="h-9 w-9 border border-white/20">
                <AvatarImage src={user?.employee?.profile_photo_url || ''} />
                <AvatarFallback className="bg-accent text-white text-xs font-semibold">
                  {getInitials(user?.employee?.full_name || user?.email || 'Founder')}
                </AvatarFallback>
              </Avatar>
              <div className="truncate">
                <div className="flex items-center space-x-1.5">
                  <p className="text-xs font-semibold text-white truncate max-w-[100px]">
                    {user?.employee?.full_name || 'Admin'}
                  </p>
                  <Badge variant="accent" className="h-4 px-1 text-[9px] font-bold uppercase bg-blue-500/20 text-blue-300 border-0">
                    <Shield className="mr-0.5 h-2.5 w-2.5" /> Founder
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-400 truncate max-w-[130px]">
                  {user?.email}
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
        description="Are you sure you want to end your current session and sign out?"
        confirmLabel="Sign Out"
        variant="destructive"
        loading={logoutMutation.isPending}
        onConfirm={handleLogout}
      />
    </>
  );
};

export default FounderSidebar;
