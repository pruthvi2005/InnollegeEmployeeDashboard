import React from 'react';
import { Bell, CheckCheck, Info, CheckCircle2, AlertTriangle, AlertCircle, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useNotifications, useMarkReadMutation, useMarkAllReadMutation } from '@/hooks/useNotifications';
import { useAuthStore } from '@/store/authStore';
import { formatRelativeTime } from '@/lib/utils';
import { Notification } from '@/store/notificationStore';

const getNotificationIcon = (type: Notification['type']) => {
  switch (type) {
    case 'success':
      return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />;
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />;
    case 'alert':
      return <AlertCircle className="h-4 w-4 text-rose-500 shrink-0" />;
    case 'system':
      return <ShieldAlert className="h-4 w-4 text-blue-500 shrink-0" />;
    case 'info':
    default:
      return <Info className="h-4 w-4 text-accent shrink-0" />;
  }
};

export const NotificationBell: React.FC = () => {
  const { data, isLoading, isError } = useNotifications({ page: 1, page_size: 5 });
  const markReadMutation = useMarkReadMutation();
  const markAllReadMutation = useMarkAllReadMutation();
  const user = useAuthStore((s) => s.user);

  const notifications = data?.items || [];
  const unreadCount = data?.unread_count ?? notifications.filter((n) => !n.is_read).length;
  const notificationsLink = user?.role === 'founder' ? '/founder/notifications' : '/employee/notifications';

  const handleNotificationClick = (id: string, isRead: boolean) => {
    if (!isRead) {
      markReadMutation.mutate(id);
    }
  };

  const handleMarkAllRead = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (unreadCount > 0) {
      markAllReadMutation.mutate();
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="View notifications"
          className="relative rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-accent"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-danger px-1 text-[10px] font-bold text-white shadow-sm ring-2 ring-white animate-pulse">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-80 sm:w-96 p-0 shadow-xl border-border rounded-xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-slate-50/50">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-semibold text-foreground">Notifications</span>
            {unreadCount > 0 && (
              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[11px] font-medium text-accent">
                {unreadCount} new
              </span>
            )}
          </div>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={markAllReadMutation.isPending}
              className="inline-flex items-center text-xs font-medium text-accent hover:text-blue-700 transition-colors disabled:opacity-50"
            >
              <CheckCheck className="mr-1 h-3.5 w-3.5" />
              Mark all read
            </button>
          )}
        </div>

        <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
          {isLoading ? (
            <div className="p-6 text-center text-xs text-muted-foreground space-y-2">
              <div className="animate-spin h-5 w-5 border-2 border-accent border-t-transparent rounded-full mx-auto" />
              <p>Loading notifications...</p>
            </div>
          ) : isError ? (
            <div className="p-6 text-center text-xs text-danger">
              Could not load notifications. Please try again.
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                <Bell className="h-5 w-5" />
              </div>
              <p className="mt-2 text-sm font-medium text-foreground">No notifications</p>
              <p className="text-xs text-muted-foreground mt-0.5">You're all caught up!</p>
            </div>
          ) : (
            notifications.map((notification) => (
              <DropdownMenuItem
                key={notification.id}
                onClick={() => handleNotificationClick(notification.id, notification.is_read)}
                className="flex items-start gap-3 p-3.5 transition-colors cursor-pointer hover:bg-slate-50 focus:bg-slate-50"
              >
                <div className="mt-0.5">{getNotificationIcon(notification.type)}</div>
                <div className="flex-1 space-y-1 overflow-hidden">
                  <div className="flex items-center justify-between">
                    <p
                      className={`text-xs font-semibold leading-tight truncate ${
                        notification.is_read ? 'text-slate-700' : 'text-slate-900 font-bold'
                      }`}
                    >
                      {notification.title}
                    </p>
                    {!notification.is_read && (
                      <span className="ml-1.5 h-2 w-2 shrink-0 rounded-full bg-accent" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                    {notification.message}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    {formatRelativeTime(notification.created_at)}
                  </p>
                </div>
              </DropdownMenuItem>
            ))
          )}
        </div>

        <DropdownMenuSeparator className="m-0" />
        <div className="p-2 bg-slate-50/50 text-center">
          <Link
            to={notificationsLink}
            className="block w-full py-1.5 text-xs font-medium text-accent hover:text-blue-700 transition-colors"
          >
            View all notifications →
          </Link>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default NotificationBell;
