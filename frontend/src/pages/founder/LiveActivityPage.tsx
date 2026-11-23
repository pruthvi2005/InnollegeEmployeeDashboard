import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, RefreshCw } from 'lucide-react';
import { activityApi } from '@/lib/api';
import { formatRelativeTime } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export const LiveActivityPage: React.FC = () => {
  const activity = useQuery({
    queryKey: ['activity', 'recent'],
    queryFn: () => activityApi.recent(),
    refetchInterval: 15000,
  });

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-amber-700">Operations feed</p>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-slate-950">Live Activity</h1>
          <p className="mt-1 text-sm text-slate-500">Recent platform activity refreshes automatically.</p>
        </div>
        <Button variant="outline" onClick={() => activity.refetch()} disabled={activity.isFetching}>
          <RefreshCw className={`mr-2 h-4 w-4 ${activity.isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>
      <Card className="overflow-hidden border-slate-200 shadow-sm">
        <CardHeader className="border-b border-slate-100 bg-gradient-to-r from-white to-amber-50/60">
          <CardTitle className="flex items-center gap-2 font-bold"><Activity className="h-5 w-5 text-amber-700" />Recent events</CardTitle>
          <CardDescription>Activity records across your company workspace.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {activity.isLoading ? (
            <p className="p-8 text-center text-sm text-slate-500">Loading activity...</p>
          ) : activity.isError ? (
            <p role="alert" className="p-8 text-center text-sm text-rose-700">Activity could not be loaded. Please try again.</p>
          ) : activity.data?.length ? (
            <ul className="divide-y divide-slate-100">
              {activity.data.map((event) => (
                <li key={event.id} className="flex items-start gap-4 px-5 py-5">
                  <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-800"><Activity className="h-5 w-5" /></span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-slate-900">{event.actor_name}</p>
                    <p className="mt-1 text-sm text-slate-600">{event.event_type.replace(/[_-]/g, ' ')}</p>
                    <p className="mt-1 text-xs text-slate-400">{formatRelativeTime(event.created_at)}</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-6 py-14 text-center">
              <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400"><Activity className="h-6 w-6" /></span>
              <p className="mt-4 font-semibold text-slate-800">No activity recorded yet</p>
              <p className="mt-1 text-sm text-slate-500">New account and employee activity will appear here as it is recorded.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LiveActivityPage;
