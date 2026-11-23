import { create } from 'zustand';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'alert' | 'system';
  reference_id?: string | null;
  reference_type?: string | null;
  is_read: boolean;
  created_at: string;
  link?: string;
}

export interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (n: Notification) => void;
  setNotifications: (ns: Notification[], count?: number) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
}

export const useNotificationStore = create<NotificationState>()((set) => ({
  notifications: [],
  unreadCount: 0,
  addNotification: (notification) =>
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: notification.is_read ? state.unreadCount : state.unreadCount + 1,
    })),
  setNotifications: (notifications, count) =>
    set({
      notifications,
      unreadCount: count !== undefined ? count : notifications.filter((n) => !n.is_read).length,
    }),
  markRead: (id) =>
    set((state) => {
      const updated = state.notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n
      );
      return {
        notifications: updated,
        unreadCount: updated.filter((n) => !n.is_read).length,
      };
    }),
  markAllRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, is_read: true })),
      unreadCount: 0,
    })),
}));
