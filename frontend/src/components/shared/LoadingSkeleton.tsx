import React from 'react';
import { cn } from '@/lib/utils';

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('animate-pulse rounded-md bg-slate-200/80', className)} {...props} />;
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-10 w-10 rounded-full" />
      </div>
      <div className="mt-4">
        <Skeleton className="h-8 w-20" />
      </div>
      <div className="mt-3 flex items-center space-x-2">
        <Skeleton className="h-3 w-12" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  );
}

export function TableRowSkeleton({ columns = 5 }: { columns?: number }) {
  return (
    <tr className="border-b border-border">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="py-4 px-4">
          <Skeleton className="h-4 w-full max-w-[120px]" />
        </td>
      ))}
    </tr>
  );
}

export function SidebarSkeleton() {
  return (
    <aside className="w-64 bg-primary text-white h-screen p-4 flex flex-col justify-between">
      <div className="space-y-6">
        <div className="flex items-center space-x-3 px-2">
          <Skeleton className="h-8 w-8 rounded-lg bg-white/20" />
          <Skeleton className="h-6 w-32 bg-white/20" />
        </div>
        <div className="space-y-3 pt-4">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full rounded-lg bg-white/10" />
          ))}
        </div>
      </div>
      <div className="border-t border-white/10 pt-4">
        <div className="flex items-center space-x-3">
          <Skeleton className="h-10 w-10 rounded-full bg-white/20" />
          <div className="space-y-1">
            <Skeleton className="h-4 w-24 bg-white/20" />
            <Skeleton className="h-3 w-16 bg-white/15" />
          </div>
        </div>
      </div>
    </aside>
  );
}

export function PageSkeleton() {
  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
        <Skeleton className="h-10 w-32 rounded-lg" />
      </div>

      {/* Stats Grid Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>

      {/* Main Content Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-border bg-white p-6 space-y-4">
          <Skeleton className="h-6 w-36" />
          <Skeleton className="h-64 w-full rounded-lg" />
        </div>
        <div className="rounded-xl border border-border bg-white p-6 space-y-4">
          <Skeleton className="h-6 w-28" />
          <div className="space-y-3">
            <Skeleton className="h-14 w-full rounded-lg" />
            <Skeleton className="h-14 w-full rounded-lg" />
            <Skeleton className="h-14 w-full rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}
