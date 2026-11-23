import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Building2, Plus, Users } from 'lucide-react';
import { toast } from 'sonner';
import { departmentsApi, employeesApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const errorMessage = (error: unknown) =>
  axios.isAxiosError(error) ? (String(error.response?.data?.detail || 'Request failed.')) : 'Request failed.';

export const DepartmentsPage: React.FC = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const queryClient = useQueryClient();
  const departments = useQuery({ queryKey: ['departments'], queryFn: departmentsApi.list });
  const employees = useQuery({
    queryKey: ['employees', 'active-by-department'],
    queryFn: () => employeesApi.list({ page: 1, page_size: 100, is_active: true }),
  });
  const createDepartment = useMutation({
    mutationFn: () => departmentsApi.create({ name: name.trim(), description: description.trim() || undefined }),
    onSuccess: async () => {
      setName('');
      setDescription('');
      await queryClient.invalidateQueries({ queryKey: ['departments'] });
      toast.success('Department created.');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent"><Building2 className="h-5 w-5" /></div>
        <div><h1 className="text-2xl font-bold">Departments</h1><p className="text-sm text-muted-foreground">Create and manage organizational departments.</p></div>
      </div>
      <Card>
        <CardHeader><CardTitle>Add department</CardTitle></CardHeader>
        <CardContent>
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); createDepartment.mutate(); }}>
            <label className="space-y-1 text-sm font-medium">Department name<Input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Engineering" /></label>
            <label className="space-y-1 text-sm font-medium">Description<Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" /></label>
            <div className="sm:col-span-2"><Button disabled={createDepartment.isPending}><Plus className="mr-2 h-4 w-4" />{createDepartment.isPending ? 'Creating...' : 'Create department'}</Button></div>
          </form>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>All departments</CardTitle></CardHeader>
        <CardContent>
          {departments.isLoading || employees.isLoading ? <p className="text-sm text-muted-foreground">Loading...</p> : departments.isError || employees.isError ? (
            <p role="alert" className="text-sm text-danger">Could not load departments or employees. Refresh and try again.</p>
          ) : departments.data?.length ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {departments.data.map((department) => (
                <div key={department.id} className="rounded-xl border p-4">
                  <div className="flex items-center justify-between"><h3 className="font-semibold">{department.name}</h3><Badge variant="secondary"><Users className="mr-1 h-3 w-3" />{department.employee_count || 0}</Badge></div>
                  <p className="mt-2 text-sm text-muted-foreground">{department.description || 'No description'}</p>
                  <ul className="mt-3 space-y-1 border-t pt-3 text-sm">
                    {(employees.data?.items || [])
                      .filter((employee) => employee.department_id === department.id && employee.is_active)
                      .map((employee) => <li key={employee.id}>{employee.full_name}</li>)}
                    {(employees.data?.items || []).every((employee) => employee.department_id !== department.id) && (
                      <li className="text-muted-foreground">No active employees assigned</li>
                    )}
                  </ul>
                </div>
              ))}
            </div>
          ) : <p className="py-6 text-center text-sm text-muted-foreground">No departments added yet.</p>}
        </CardContent>
      </Card>
    </div>
  );
};

export default DepartmentsPage;
