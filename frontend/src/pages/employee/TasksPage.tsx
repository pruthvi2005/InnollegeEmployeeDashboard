import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckSquare } from 'lucide-react';
import { toast } from 'sonner';
import { tasksApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export const TasksPage: React.FC = () => {
  const queryClient = useQueryClient();
  const tasks = useQuery({ queryKey: ['tasks'], queryFn: tasksApi.list });
  const updateTask = useMutation({
    mutationFn: ({ assignmentId, status }: { assignmentId: string; status: string }) => tasksApi.updateAssignment(assignmentId, { status }),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ['tasks'] }); toast.success('Task status updated.'); },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><CheckSquare className="h-5 w-5" /></div><div><h1 className="text-2xl font-bold">My Tasks</h1><p className="text-sm text-muted-foreground">View assigned work and update progress.</p></div></div>
      <Card><CardHeader><CardTitle>Assigned tasks</CardTitle></CardHeader><CardContent>
        {tasks.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : tasks.isError ? <p role="alert" className="text-sm text-danger">Could not load your tasks.</p> : tasks.data?.length ? <div className="space-y-3">{tasks.data.map((task) => {
          const assignment = task.assignments[0];
          return <div key={task.id} className="flex flex-col gap-4 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><h3 className="font-semibold">{task.title}</h3><p className="mt-1 text-sm text-muted-foreground">{task.description || 'No description'}</p><div className="mt-2 flex gap-2"><Badge variant="outline">{task.priority}</Badge><Badge variant="secondary">{assignment?.status || 'pending'}</Badge></div></div><div className="flex gap-2"><Button variant="outline" disabled={updateTask.isPending || !assignment} onClick={() => assignment && updateTask.mutate({ assignmentId: assignment.id, status: 'in_progress' })}>Start</Button><Button disabled={updateTask.isPending || !assignment} onClick={() => assignment && updateTask.mutate({ assignmentId: assignment.id, status: 'completed' })}>Complete</Button></div></div>;
        })}</div> : <p className="py-8 text-center text-sm text-muted-foreground">No tasks assigned to you.</p>}
      </CardContent></Card>
    </div>
  );
};

export default TasksPage;
