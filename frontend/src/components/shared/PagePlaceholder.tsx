import React from 'react';
import { LucideIcon, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';

export interface PagePlaceholderProps {
  title: string;
  description: string;
  icon: LucideIcon;
  comingSoon?: boolean;
  phase?: string;
}

export const PagePlaceholder: React.FC<PagePlaceholderProps> = ({
  title,
  description,
  icon: Icon,
  comingSoon = true,
  phase = 'Phase 2',
}) => {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center p-4">
      <Card className="w-full max-w-lg border border-dashed border-border bg-white text-center shadow-sm">
        <CardContent className="flex flex-col items-center p-8 sm:p-12">
          <div className="relative mb-6">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10 text-primary shadow-inner">
              <Icon className="h-10 w-10 text-primary" />
            </div>
            {comingSoon && (
              <span className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full bg-accent text-white shadow-md">
                <Sparkles className="h-4 w-4" />
              </span>
            )}
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {title}
          </h1>

          <p className="mt-2 text-sm text-muted-foreground sm:text-base max-w-sm">
            {description}
          </p>

          {comingSoon && (
            <div className="mt-6">
              <Badge variant="accent" className="px-3.5 py-1 text-xs font-semibold">
                Coming Soon in {phase}
              </Badge>
            </div>
          )}

          <div className="mt-8 rounded-lg bg-slate-50 border border-slate-100 p-4 text-xs text-muted-foreground max-w-md w-full text-center">
            This module is scheduled for implementation in the next release cycle.
            Core platform authentication, navigation, and live overview are active.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PagePlaceholder;
