import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { FolderKanban } from 'lucide-react';
import { projectsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export const ProjectsPage: React.FC = () => {
  const projects = useQuery({ queryKey: ['projects'], queryFn: projectsApi.list });
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><FolderKanban className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">My Projects</h1><p className="text-sm text-muted-foreground">View projects assigned to you.</p></div></div>
      <Card><CardHeader><CardTitle>Assigned projects</CardTitle></CardHeader><CardContent>
        {projects.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : projects.isError ? <p role="alert" className="text-sm text-danger">Could not load your projects.</p> : projects.data?.length ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{projects.data.map((project) => <div key={project.id} className="rounded-xl border p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">{project.name}</h3><Badge variant="outline">{project.status}</Badge></div><p className="mt-2 text-sm text-muted-foreground">{project.description || 'No description'}</p><p className="mt-3 text-xs text-muted-foreground">{project.member_count} members · {project.task_count} tasks</p></div>)}</div> : <p className="py-8 text-center text-sm text-muted-foreground">No projects assigned to you.</p>}
      </CardContent></Card>
    </div>
  );
};

export default ProjectsPage;
