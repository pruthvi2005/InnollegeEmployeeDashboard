import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { FolderKanban, Plus, Trash2, Users } from 'lucide-react';
import { toast } from 'sonner';
import { projectsApi, employeesApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const errorMessage = (error: unknown) =>
  axios.isAxiosError(error) ? String(error.response?.data?.detail || 'Request failed.') : 'Request failed.';

export const ProjectsPage: React.FC = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [memberProjectId, setMemberProjectId] = useState('');
  const [memberEmployeeId, setMemberEmployeeId] = useState('');
  const queryClient = useQueryClient();
  const projects = useQuery({ queryKey: ['projects'], queryFn: projectsApi.list });
  const employees = useQuery({ queryKey: ['employees'], queryFn: () => employeesApi.list({ page: 1, page_size: 100 }) });

  const createProject = useMutation({
    mutationFn: () => projectsApi.create({ name: name.trim(), description: description.trim() || undefined, status: 'planning' }),
    onSuccess: async () => {
      setName(''); setDescription('');
      await queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Project created.');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  const addMember = useMutation({
    mutationFn: () => projectsApi.addMember(memberProjectId, memberEmployeeId),
    onSuccess: async () => {
      setMemberProjectId(''); setMemberEmployeeId('');
      await queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Employee added to project.');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
  const deleteProject = useMutation({
    mutationFn: projectsApi.delete,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['projects'] }),
        queryClient.invalidateQueries({ queryKey: ['tasks'] }),
      ]);
      toast.success('Project deleted.');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><FolderKanban className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">Projects</h1><p className="text-sm text-muted-foreground">Create projects and assign employees.</p></div></div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card><CardHeader><CardTitle>Create project</CardTitle></CardHeader><CardContent>
          <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); createProject.mutate(); }}>
            <label className="space-y-1 text-sm font-medium">Project name<Input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Website redesign" /></label>
            <label className="space-y-1 text-sm font-medium">Description<Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Project summary" /></label>
            <Button disabled={createProject.isPending}><Plus className="mr-2 h-4 w-4" />{createProject.isPending ? 'Creating...' : 'Create project'}</Button>
          </form>
        </CardContent></Card>
        <Card><CardHeader><CardTitle>Add project member</CardTitle></CardHeader><CardContent>
          <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); addMember.mutate(); }}>
            <label className="space-y-1 text-sm font-medium">Project<select className="h-10 w-full rounded-md border px-3 text-sm" required value={memberProjectId} onChange={(e) => setMemberProjectId(e.target.value)}><option value="">Select project</option>{projects.data?.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label>
            <label className="space-y-1 text-sm font-medium">Employee<select className="h-10 w-full rounded-md border px-3 text-sm" required value={memberEmployeeId} onChange={(e) => setMemberEmployeeId(e.target.value)}><option value="">Select employee</option>{employees.data?.items.map((employee) => <option key={employee.id} value={employee.id}>{employee.full_name}</option>)}</select></label>
            <Button disabled={addMember.isPending || !memberProjectId || !memberEmployeeId}><Users className="mr-2 h-4 w-4" />Add member</Button>
          </form>
        </CardContent></Card>
      </div>
      <Card><CardHeader><CardTitle>All projects</CardTitle></CardHeader><CardContent>
        {projects.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : projects.isError ? <p role="alert" className="text-sm text-danger">Could not load projects.</p> : projects.data?.length ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{projects.data.map((project) => <div key={project.id} className="rounded-xl border p-4"><div className="flex items-center justify-between gap-2"><h3 className="font-semibold">{project.name}</h3><Badge variant="outline">{project.status}</Badge></div><p className="mt-2 text-sm text-muted-foreground">{project.description || 'No description'}</p><p className="mt-3 text-xs text-muted-foreground">{project.member_count} members · {project.task_count} tasks</p><Button className="mt-4" variant="destructive" size="sm" disabled={deleteProject.isPending} onClick={() => { if (window.confirm(`Delete project "${project.name}"? Its tasks will be kept without a project.`)) deleteProject.mutate(project.id); }}><Trash2 className="mr-2 h-4 w-4" />Delete project</Button></div>)}</div> : <p className="py-6 text-center text-sm text-muted-foreground">No projects created yet.</p>}
      </CardContent></Card>
    </div>
  );
};

export default ProjectsPage;
