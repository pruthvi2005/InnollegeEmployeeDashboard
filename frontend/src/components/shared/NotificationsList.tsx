import React from 'react';
import { AlertCircle, AlertTriangle, Bell, CheckCheck, CheckCircle2, Info, ShieldAlert } from 'lucide-react';
import { toast } from 'sonner';
import { useNotifications, useMarkReadMutation, useMarkAllReadMutation } from '@/hooks/useNotifications';
import { formatRelativeTime } from '@/lib/utils';
import { Notification } from '@/store/notificationStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const iconByType = (type: Notification['type']) => {
  switch (type) {
    case 'success':
      return <CheckCircle2 className="h-5 w-5 text-emerald-600" />;
    case 'warning':
      return <AlertTriangle className="h-5 w-5 text-amber-600" />;
    case 'alert':
      return <AlertCircle className="h-5 w-5 text-rose-600" />;
    case 'system':
      return <ShieldAlert className="h-5 w-5 text-indigo-600" />;
    default:
      return <Info className="h-5 w-5 text-blue-600" />;
  }
};

interface NotificationsListProps {
  audience: 'founder' | 'employee';
}

export const NotificationsList: React.FC<NotificationsListProps> = ({ audience }) => {
  const notifications = useNotifications({ page: 1, page_size: 100 });
  const markRead = useMarkReadMutation();
  const markAllRead = useMarkAllReadMutation();
  const items = notifications.data?.items ?? [];

  const handleMarkRead = (id: string) => {
    markRead.mutate(id, {
      onError: () => toast.error('Could not mark notification as read.'),
    });
  };

  const handleMarkAllRead = () => {
    markAllRead.mutate(undefined, {
      onError: () => toast.error('Could not mark notifications as read.'),
    });
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-amber-700">{audience} workspace</p>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-slate-950">Notifications</h1>
          <p className="mt-1 text-sm text-slate-500">Your latest updates and important notices.</p>
        </div>
        <Button
          variant="outline"
          disabled={!notifications.data?.unread_count || markAllRead.isPending}
          onClick={handleMarkAllRead}
        >
          <CheckCheck className="mr-2 h-4 w-4" />
          {markAllRead.isPending ? 'Updating...' : 'Mark all as read'}
        </Button>
      </div>

      <Card className="overflow-hidden border-slate-200 shadow-sm">
        <CardHeader className="border-b border-slate-100 bg-gradient-to-r from-white to-slate-50">
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Bell className="h-5 w-5 text-amber-600" />
            Inbox
            {!!notifications.data?.unread_count && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-800">
                {notifications.data.unread_count} unread
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {notifications.isLoading ? (
            <p className="p-8 text-center text-sm text-slate-500">Loading notifications...</p>
          ) : notifications.isError ? (
            <p role="alert" className="p-8 text-center text-sm text-rose-700">Notifications could not be loaded. Please try again.</p>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center px-6 py-14 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
                <Bell className="h-6 w-6" />
              </span>
              <p className="mt-4 font-semibold text-slate-800">You’re all caught up</p>
              <p className="mt-1 text-sm text-slate-500">New notices will appear here.</p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {items.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => !item.is_read && handleMarkRead(item.id)}
                    disabled={item.is_read || markRead.isPending}
                    className="flex w-full items-start gap-4 px-5 py-5 text-left transition-colors hover:bg-slate-50 disabled:cursor-default"
                  >
                    <span className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${item.is_read ? 'bg-slate-100' : 'bg-amber-50'}`}>
                      {iconByType(item.type)}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex flex-wrap items-center gap-2">
                        <span className={`font-semibold ${item.is_read ? 'text-slate-700' : 'text-slate-950'}`}>{item.title}</span>
                        {!item.is_read && <span className="h-2 w-2 rounded-full bg-amber-500" aria-label="Unread" />}
                      </span>
                      <span className="mt-1 block text-sm leading-6 text-slate-600">{item.message}</span>
                      <span className="mt-2 block text-xs text-slate-400">{formatRelativeTime(item.created_at)}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default NotificationsList;
