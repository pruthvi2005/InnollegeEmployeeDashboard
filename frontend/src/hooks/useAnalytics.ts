import { useQuery } from '@tanstack/react-query';
import { analyticsApi, OverviewStats } from '@/lib/api';

export const useOverviewStats = () => {
  return useQuery<OverviewStats>({
    queryKey: ['analytics', 'overview'],
    queryFn: async () => {
      return await analyticsApi.overview();
    },
    refetchInterval: 60000, // Refetch every 60 seconds
    staleTime: 30000,
  });
};
