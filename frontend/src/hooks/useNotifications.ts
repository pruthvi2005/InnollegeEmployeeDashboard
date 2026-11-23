import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '@/lib/api';
import { useNotificationStore } from '@/store/notificationStore';
import { useEffect } from 'react';

export const useNotifications = (params?: { page?: number; page_size?: number }) => {
  const setNotifications = useNotificationStore((s) => s.setNotifications);

  const query = useQuery({
    queryKey: ['notifications', params],
    queryFn: async () => {
      return await notificationsApi.list(params);
    },
    refetchInterval: 30000, // Poll every 30s
    staleTime: 10000,
  });

  useEffect(() => {
    if (query.data?.items) {
      setNotifications(query.data.items, query.data.unread_count);
    }
  }, [query.data, setNotifications]);

  return query;
};

export const useMarkReadMutation = () => {
  const queryClient = useQueryClient();
  const markReadInStore = useNotificationStore((s) => s.markRead);

  return useMutation({
    mutationFn: async (id: string) => {
      return await notificationsApi.markRead(id);
    },
    onMutate: (id) => {
      markReadInStore(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
};

export const useMarkAllReadMutation = () => {
  const queryClient = useQueryClient();
  const markAllReadInStore = useNotificationStore((s) => s.markAllRead);

  return useMutation({
    mutationFn: async () => {
      return await notificationsApi.markAllRead();
    },
    onMutate: () => {
      markAllReadInStore();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
};
