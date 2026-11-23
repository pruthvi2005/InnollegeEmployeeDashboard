import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Check, Copy, KeyRound, Trash2, UserPlus, Users } from 'lucide-react';
import { toast } from 'sonner';
import { departmentsApi, employeesApi, EmployeeCreateData, EmployeeListItem } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';

type EmployeeFormValues = {
  full_name: string;
  email: string;
  password: string;
  phone: string;
  designation: string;
  department_id: string;
};

const initialForm: EmployeeFormValues = {
  full_name: '',
  email: '',
  password: '',
  phone: '',
  designation: '',
  department_id: '',
};

const errorMessage = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg).join(', ');
  }
  return 'Could not complete the request. Please try again.';
};

export const EmployeesPage: React.FC = () => {
  const [form, setForm] = useState(initialForm);
  const [createdCredentials, setCreatedCredentials] = useState<{ email: string; password: string } | null>(null);
  const [passwordResetEmployee, setPasswordResetEmployee] = useState<EmployeeListItem | null>(null);
  const [resetPassword, setResetPassword] = useState('');
  const [confirmResetPassword, setConfirmResetPassword] = useState('');
  const [passwordResetError, setPasswordResetError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const employeeQuery = useQuery({
    queryKey: ['employees'],
    queryFn: () => employeesApi.list({ page: 1, page_size: 100 }),
  });
  const departmentQuery = useQuery({
    queryKey: ['departments'],
    queryFn: departmentsApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (data: EmployeeCreateData) => employeesApi.create(data),
    onSuccess: async (employee) => {
      setCreatedCredentials({ email: employee.email, password: form.password });
      setForm(initialForm);
      await queryClient.invalidateQueries({ queryKey: ['employees'] });
      await queryClient.invalidateQueries({ queryKey: ['departments'] });
      toast.success(`${employee.full_name} can now sign in with the credentials shown below.`);
    },
    onError: (error: unknown) => toast.error(errorMessage(error)),
  });

  const updateDepartmentMutation = useMutation({
    mutationFn: ({ employeeId, departmentId }: { employeeId: string; departmentId: string }) =>
      employeesApi.update(employeeId, { department_id: departmentId }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['employees'] });
      await queryClient.invalidateQueries({ queryKey: ['departments'] });
      toast.success('Employee department updated.');
    },
    onError: (error: unknown) => toast.error(errorMessage(error)),
  });

  const passwordResetMutation = useMutation({
    mutationFn: ({ employeeId, newPassword }: { employeeId: string; newPassword: string }) =>
      employeesApi.resetPassword(employeeId, newPassword),
    onSuccess: () => {
      setPasswordResetEmployee(null);
      setResetPassword('');
      setConfirmResetPassword('');
      setPasswordResetError(null);
      toast.success('Employee password reset. Share the new password privately.');
    },
    onError: (error: unknown) => toast.error(errorMessage(error)),
  });

  const deleteMutation = useMutation({
    mutationFn: (employee: EmployeeListItem) => employeesApi.delete(employee.id),
    onSuccess: async (_, employee) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['employees'] }),
        queryClient.invalidateQueries({ queryKey: ['departments'] }),
        queryClient.invalidateQueries({ queryKey: ['projects'] }),
        queryClient.invalidateQueries({ queryKey: ['tasks'] }),
      ]);
      toast.success(`${employee.full_name} was deleted.`);
    },
    onError: (error: unknown) => toast.error(errorMessage(error)),
  });

  const updateField = (field: keyof EmployeeFormValues) =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setForm((current) => ({ ...current, [field]: event.target.value }));
    };

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data: EmployeeCreateData = {
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      password: form.password,
    };
    if (form.phone.trim()) data.phone = form.phone.trim();
    if (form.designation.trim()) data.designation = form.designation.trim();
    if (form.department_id) data.department_id = form.department_id;
    createMutation.mutate(data);
  };

  const copyCredentials = async () => {
    if (!createdCredentials) return;
    try {
      await navigator.clipboard.writeText(
        `Login: ${createdCredentials.email}\nPassword: ${createdCredentials.password}`
      );
      toast.success('Credentials copied to clipboard.');
    } catch {
      toast.error('Could not access the clipboard. Copy the credentials manually.');
    }
  };

  const submitPasswordReset = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!passwordResetEmployee) return;
    if (resetPassword !== confirmResetPassword) {
      setPasswordResetError('Passwords do not match.');
      return;
    }

    setPasswordResetError(null);
    passwordResetMutation.mutate({
      employeeId: passwordResetEmployee.id,
      newPassword: resetPassword,
    });
  };

  return (
    <div className="space-y-6 p-4 sm:p-6">
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-accent">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Employee Management</h1>
            <p className="text-sm text-muted-foreground">Create employee accounts and share their sign-in credentials.</p>
          </div>
        </div>
      </div>

      {createdCredentials && (
        <Card className="border-emerald-200 bg-emerald-50/60">
          <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <div className="mb-2 flex items-center gap-2 font-semibold text-emerald-900">
                <Check className="h-4 w-4" />
                Employee account created
              </div>
              <p className="text-sm text-emerald-900"><strong>Login:</strong> {createdCredentials.email}</p>
              <p className="break-all text-sm text-emerald-900"><strong>Password:</strong> {createdCredentials.password}</p>
              <p className="mt-2 text-xs text-emerald-800">Share these credentials privately. The password is shown only in this page until dismissed or refreshed.</p>
            </div>
            <div className="flex shrink-0 gap-2">
              <Button type="button" variant="outline" onClick={copyCredentials}>
                <Copy className="mr-2 h-4 w-4" />
                Copy credentials
              </Button>
              <Button type="button" variant="ghost" onClick={() => setCreatedCredentials(null)}>Dismiss</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5 text-accent" />
            Add employee
          </CardTitle>
          <CardDescription>Create an employee login. The employee role is assigned automatically.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-1.5 text-sm font-medium">
              Full name
              <Input required minLength={2} maxLength={255} autoComplete="name" value={form.full_name} onChange={updateField('full_name')} placeholder="Employee name" />
            </label>
            <label className="space-y-1.5 text-sm font-medium">
              Email address (login)
              <Input required type="email" autoComplete="email" value={form.email} onChange={updateField('email')} placeholder="employee@company.com" />
            </label>
            <label className="space-y-1.5 text-sm font-medium">
              Initial password
              <Input required type="password" minLength={8} maxLength={128} autoComplete="new-password" value={form.password} onChange={updateField('password')} placeholder="At least 8 characters" />
            </label>
            <label className="space-y-1.5 text-sm font-medium">
              Phone (optional)
              <Input type="tel" autoComplete="tel" value={form.phone} onChange={updateField('phone')} placeholder="+91..." />
            </label>
            <label className="space-y-1.5 text-sm font-medium sm:col-span-2">
              Designation (optional)
              <Input value={form.designation} onChange={updateField('designation')} placeholder="e.g. Software Engineer" />
            </label>
            <label className="space-y-1.5 text-sm font-medium sm:col-span-2">
              Department
              <select
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={form.department_id}
                onChange={(event) => setForm((current) => ({ ...current, department_id: event.target.value }))}
              >
                <option value="">No department</option>
                {departmentQuery.data?.map((department) => (
                  <option key={department.id} value={department.id}>{department.name}</option>
                ))}
              </select>
            </label>
            <div className="sm:col-span-2">
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating account...' : 'Create employee account'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Employees</CardTitle>
          <CardDescription>Employee accounts that can sign in to the platform.</CardDescription>
        </CardHeader>
        <CardContent>
          {employeeQuery.isLoading ? (
            <p className="py-6 text-center text-sm text-muted-foreground">Loading employees...</p>
          ) : employeeQuery.isError ? (
            <p role="alert" className="py-6 text-center text-sm text-danger">{errorMessage(employeeQuery.error)}</p>
          ) : employeeQuery.data?.items.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] text-left text-sm">
                <thead className="border-b text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-3 font-medium">Employee</th>
                    <th className="px-3 py-3 font-medium">Employee ID</th>
                    <th className="px-3 py-3 font-medium">Designation</th>
                    <th className="px-3 py-3 font-medium">Department</th>
                    <th className="px-3 py-3 font-medium">Status</th>
                    <th className="px-3 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {employeeQuery.data.items.map((employee: EmployeeListItem) => (
                    <tr key={employee.id}>
                      <td className="px-3 py-4">
                        <div className="font-medium text-foreground">{employee.full_name}</div>
                        <div className="text-muted-foreground">{employee.email}</div>
                      </td>
                      <td className="px-3 py-4">{employee.employee_id}</td>
                      <td className="px-3 py-4">{employee.designation || '—'}</td>
                      <td className="px-3 py-4">
                        <select
                          aria-label={`Department for ${employee.full_name}`}
                          className="h-9 min-w-36 rounded-md border border-input bg-background px-2 text-sm"
                          value={employee.department_id || ''}
                          onChange={(event) => updateDepartmentMutation.mutate({
                            employeeId: employee.id,
                            departmentId: event.target.value,
                          })}
                          disabled={updateDepartmentMutation.isPending}
                        >
                          <option value="">No department</option>
                          {departmentQuery.data?.map((department) => (
                            <option key={department.id} value={department.id}>{department.name}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-4">
                        <Badge variant={employee.is_active ? 'success' : 'secondary'}>
                          {employee.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="px-3 py-4">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setPasswordResetEmployee(employee);
                              setResetPassword('');
                              setConfirmResetPassword('');
                              setPasswordResetError(null);
                            }}
                          >
                            <KeyRound className="mr-1 h-4 w-4" />Reset password
                          </Button>
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            disabled={deleteMutation.isPending}
                            onClick={() => {
                              if (window.confirm(`Permanently delete ${employee.full_name} and their related records?`)) {
                                deleteMutation.mutate(employee);
                              }
                            }}
                          >
                            <Trash2 className="mr-1 h-4 w-4" />Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="py-6 text-center text-sm text-muted-foreground">No employees added yet.</p>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={passwordResetEmployee !== null}
        onOpenChange={(open) => {
          if (!open && !passwordResetMutation.isPending) {
            setPasswordResetEmployee(null);
            setResetPassword('');
            setConfirmResetPassword('');
            setPasswordResetError(null);
          }
        }}
      >
        <DialogContent>
          <form onSubmit={submitPasswordReset} className="space-y-5">
            <DialogHeader>
              <DialogTitle>Reset employee password</DialogTitle>
              <DialogDescription>
                Set a new sign-in password for {passwordResetEmployee?.email}. Share it privately; it will not be shown again.
              </DialogDescription>
            </DialogHeader>
            <label className="block space-y-1.5 text-sm font-medium">
              New password
              <Input
                type="password"
                required
                minLength={8}
                maxLength={128}
                autoComplete="new-password"
                value={resetPassword}
                onChange={(event) => setResetPassword(event.target.value)}
              />
            </label>
            <label className="block space-y-1.5 text-sm font-medium">
              Confirm new password
              <Input
                type="password"
                required
                minLength={8}
                maxLength={128}
                autoComplete="new-password"
                value={confirmResetPassword}
                onChange={(event) => setConfirmResetPassword(event.target.value)}
              />
            </label>
            {passwordResetError && (
              <p role="alert" className="text-sm text-danger">{passwordResetError}</p>
            )}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                disabled={passwordResetMutation.isPending}
                onClick={() => setPasswordResetEmployee(null)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={passwordResetMutation.isPending}>
                {passwordResetMutation.isPending ? 'Resetting...' : 'Reset password'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EmployeesPage;
