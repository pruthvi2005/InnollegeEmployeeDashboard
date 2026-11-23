import React from 'react';
import { LucideIcon, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { StatCardSkeleton } from './LoadingSkeleton';

export interface StatCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  iconColor?: string;
  iconBgColor?: string;
  titleClassName?: string;
  valueClassName?: string;
  trend?: {
    value: number;
    label: string;
    positive: boolean;
  };
  loading?: boolean;
  onClick?: () => void;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  iconColor = 'text-accent',
  iconBgColor = 'bg-blue-50',
  titleClassName,
  valueClassName,
  trend,
  loading = false,
  onClick,
  className,
}) => {
  if (loading) {
    return <StatCardSkeleton />;
  }

  const isClickable = Boolean(onClick);

  return (
    <div
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => e.key === 'Enter' && onClick?.() : undefined}
      className={cn(
        'group relative overflow-hidden rounded-xl border border-border bg-card p-6 shadow-sm transition-all duration-200',
        isClickable && 'cursor-pointer hover:border-slate-300 hover:shadow-md active:scale-[0.99]',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className={cn('text-xs font-medium uppercase tracking-wider text-muted-foreground', titleClassName)}>
            {title}
          </p>
          <p className={cn('text-3xl font-bold tracking-tight text-foreground', valueClassName)}>
            {value}
          </p>
        </div>
        <div
          className={cn(
            'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-105',
            iconBgColor
          )}
        >
          <Icon className={cn('h-6 w-6', iconColor)} />
        </div>
      </div>

      {trend && (
        <div className="mt-4 flex items-center space-x-1.5 text-xs">
          <span
            className={cn(
              'inline-flex items-center font-semibold',
              trend.positive ? 'text-success' : 'text-danger'
            )}
          >
            {trend.positive ? (
              <ArrowUpRight className="mr-0.5 h-3.5 w-3.5" />
            ) : (
              <ArrowDownRight className="mr-0.5 h-3.5 w-3.5" />
            )}
            {Math.abs(trend.value)}%
          </span>
          <span className="text-muted-foreground">{trend.label}</span>
        </div>
      )}
    </div>
  );
};

export default StatCard;
