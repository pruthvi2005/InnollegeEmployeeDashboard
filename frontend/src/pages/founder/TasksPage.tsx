import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { CheckSquare, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { tasksApi, projectsApi, employeesApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const errorMessage = (error: unknown) => axios.isAxiosError(error) ? String(error.response?.data?.detail || 'Request failed.') : 'Request failed.';

export const TasksPage: React.FC = () => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [projectId, setProjectId] = useState('');
  const [employeeIds, setEmployeeIds] = useState<string[]>([]);
  const [priority, setPriority] = useState<'low' | 'medium' | 'high' | 'urgent'>('medium');
  const queryClient = useQueryClient();
  const tasks = useQuery({ queryKey: ['tasks'], queryFn: tasksApi.list });
  const projects = useQuery({ queryKey: ['projects'], queryFn: projectsApi.list });
  const employees = useQuery({ queryKey: ['employees'], queryFn: () => employeesApi.list({ page: 1, page_size: 100 }) });
  const createTask = useMutation({
    mutationFn: () => tasksApi.create({ title: title.trim(), description: description.trim() || undefined, project_id: projectId || undefined, priority, assigned_employee_ids: employeeIds }),
    onSuccess: async () => {
      setTitle(''); setDescription(''); setProjectId(''); setEmployeeIds([]); setPriority('medium');
      await queryClient.invalidateQueries({ queryKey: ['tasks'] });
      toast.success('Task created and assigned.');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
  const deleteTask = useMutation({
    mutationFn: tasksApi.delete,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['tasks'] }),
        queryClient.invalidateQueries({ queryKey: ['reports'] }),
      ]);
      toast.success('Task deleted.');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><CheckSquare className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">Task Management</h1><p className="text-sm text-muted-foreground">Create tasks and assign them to employees.</p></div></div>
      <Card><CardHeader><CardTitle>Create task</CardTitle></CardHeader><CardContent>
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); createTask.mutate(); }}>
          <label className="space-y-1 text-sm font-medium">Title<Input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Implement feature" /></label>
          <label className="space-y-1 text-sm font-medium">Priority<select className="h-10 w-full rounded-md border px-3 text-sm" value={priority} onChange={(e) => setPriority(e.target.value as typeof priority)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label>
          <label className="space-y-1 text-sm font-medium">Project<select className="h-10 w-full rounded-md border px-3 text-sm" value={projectId} onChange={(e) => setProjectId(e.target.value)}><option value="">No project</option>{projects.data?.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label>
          <label className="space-y-1 text-sm font-medium">Assign employees<select multiple className="min-h-24 w-full rounded-md border px-3 py-2 text-sm" value={employeeIds} onChange={(e) => setEmployeeIds(Array.from(e.target.selectedOptions).map((option) => option.value))}>{employees.data?.items.map((employee) => <option key={employee.id} value={employee.id}>{employee.full_name}</option>)}</select></label>
          <label className="space-y-1 text-sm font-medium sm:col-span-2">Description<textarea className="min-h-20 w-full rounded-md border px-3 py-2 text-sm" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Task details..." /></label>
          <div className="sm:col-span-2"><Button disabled={createTask.isPending}><Plus className="mr-2 h-4 w-4" />{createTask.isPending ? 'Creating...' : 'Create task'}</Button></div>
        </form>
      </CardContent></Card>
      <Card><CardHeader><CardTitle>All tasks</CardTitle></CardHeader><CardContent>
        {tasks.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : tasks.isError ? <p role="alert" className="text-sm text-danger">Could not load tasks.</p> : tasks.data?.length ? <div className="space-y-3">{tasks.data.map((task) => <div key={task.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><h3 className="font-semibold">{task.title}</h3><p className="mt-1 text-sm text-muted-foreground">{task.description || 'No description'}</p><p className="mt-2 text-xs text-muted-foreground">{task.assignments.length ? task.assignments.map((assignment) => assignment.employee_name).join(', ') : 'Unassigned'}</p></div><div className="flex items-center gap-3"><Badge variant="outline">{task.priority}</Badge><Button variant="destructive" size="sm" disabled={deleteTask.isPending} onClick={() => { if (window.confirm(`Delete task "${task.title}"?`)) deleteTask.mutate(task.id); }}><Trash2 className="mr-2 h-4 w-4" />Delete</Button></div></div>)}</div> : <p className="py-6 text-center text-sm text-muted-foreground">No tasks created yet.</p>}
      </CardContent></Card>
    </div>
  );
};

export default TasksPage;
