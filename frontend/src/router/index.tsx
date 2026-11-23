import React from 'react';
import { Routes, Route, Navigate, createBrowserRouter } from 'react-router-dom';

// Layouts and Guards
import { ProtectedRoute } from '@/router/ProtectedRoute';
import { RoleGuard } from '@/router/RoleGuard';
import { FounderLayout } from '@/components/layout/FounderLayout';
import { EmployeeLayout } from '@/components/layout/EmployeeLayout';

// Auth Pages
import { LoginPage } from '@/pages/auth/LoginPage';

// Founder Pages
import { OverviewPage } from '@/pages/founder/OverviewPage';
import { EmployeesPage as FounderEmployeesPage } from '@/pages/founder/EmployeesPage';
import { DepartmentsPage as FounderDepartmentsPage } from '@/pages/founder/DepartmentsPage';
import { ProjectsPage as FounderProjectsPage } from '@/pages/founder/ProjectsPage';
import { TasksPage as FounderTasksPage } from '@/pages/founder/TasksPage';
import { AttendancePage as FounderAttendancePage } from '@/pages/founder/AttendancePage';
import { ReportsPage as FounderReportsPage } from '@/pages/founder/ReportsPage';
import { LeavePage as FounderLeavePage } from '@/pages/founder/LeavePage';
import { LiveActivityPage as FounderLiveActivityPage } from '@/pages/founder/LiveActivityPage';
import { AnalyticsPage as FounderAnalyticsPage } from '@/pages/founder/AnalyticsPage';
import { NotificationsPage as FounderNotificationsPage } from '@/pages/founder/NotificationsPage';
import { SettingsPage as FounderSettingsPage } from '@/pages/founder/SettingsPage';

// Employee Pages
import { DashboardPage as EmployeeDashboardPage } from '@/pages/employee/DashboardPage';
import { ProjectsPage as EmployeeProjectsPage } from '@/pages/employee/ProjectsPage';
import { TasksPage as EmployeeTasksPage } from '@/pages/employee/TasksPage';
import { AttendancePage as EmployeeAttendancePage } from '@/pages/employee/AttendancePage';
import { ReportsPage as EmployeeReportsPage } from '@/pages/employee/ReportsPage';
import { LeavePage as EmployeeLeavePage } from '@/pages/employee/LeavePage';
import { NotificationsPage as EmployeeNotificationsPage } from '@/pages/employee/NotificationsPage';
import { ProfilePage as EmployeeProfilePage } from '@/pages/employee/ProfilePage';

/**
 * JSX Route Structure used within App.tsx
 */
export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Public Login */}
      <Route path="/login" element={<LoginPage />} />

      {/* Founder Protected Routes */}
      <Route
        path="/founder"
        element={
          <ProtectedRoute>
            <RoleGuard role="founder">
              <FounderLayout />
            </RoleGuard>
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/founder/overview" replace />} />
        <Route path="overview" element={<OverviewPage />} />
        <Route path="employees" element={<FounderEmployeesPage />} />
        <Route path="departments" element={<FounderDepartmentsPage />} />
        <Route path="projects" element={<FounderProjectsPage />} />
        <Route path="tasks" element={<FounderTasksPage />} />
        <Route path="attendance" element={<FounderAttendancePage />} />
        <Route path="reports" element={<FounderReportsPage />} />
        <Route path="leaves" element={<FounderLeavePage />} />
        <Route path="live-activity" element={<FounderLiveActivityPage />} />
        <Route path="analytics" element={<FounderAnalyticsPage />} />
        <Route path="notifications" element={<FounderNotificationsPage />} />
        <Route path="settings" element={<FounderSettingsPage />} />
      </Route>

      {/* Employee Protected Routes */}
      <Route
        path="/employee"
        element={
          <ProtectedRoute>
            <RoleGuard role="employee">
              <EmployeeLayout />
            </RoleGuard>
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/employee/dashboard" replace />} />
        <Route path="dashboard" element={<EmployeeDashboardPage />} />
        <Route path="projects" element={<EmployeeProjectsPage />} />
        <Route path="tasks" element={<EmployeeTasksPage />} />
        <Route path="attendance" element={<EmployeeAttendancePage />} />
        <Route path="reports" element={<EmployeeReportsPage />} />
        <Route path="leaves" element={<EmployeeLeavePage />} />
        <Route path="notifications" element={<EmployeeNotificationsPage />} />
        <Route path="profile" element={<EmployeeProfilePage />} />
      </Route>

      {/* Catch-all Wildcard */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

/**
 * createBrowserRouter definition for programmatic routing
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/founder',
    element: (
      <ProtectedRoute>
        <RoleGuard role="founder">
          <FounderLayout />
        </RoleGuard>
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/founder/overview" replace /> },
      { path: 'overview', element: <OverviewPage /> },
      { path: 'employees', element: <FounderEmployeesPage /> },
      { path: 'departments', element: <FounderDepartmentsPage /> },
      { path: 'projects', element: <FounderProjectsPage /> },
      { path: 'tasks', element: <FounderTasksPage /> },
      { path: 'attendance', element: <FounderAttendancePage /> },
      { path: 'reports', element: <FounderReportsPage /> },
      { path: 'leaves', element: <FounderLeavePage /> },
      { path: 'live-activity', element: <FounderLiveActivityPage /> },
      { path: 'analytics', element: <FounderAnalyticsPage /> },
      { path: 'notifications', element: <FounderNotificationsPage /> },
      { path: 'settings', element: <FounderSettingsPage /> },
    ],
  },
  {
    path: '/employee',
    element: (
      <ProtectedRoute>
        <RoleGuard role="employee">
          <EmployeeLayout />
        </RoleGuard>
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/employee/dashboard" replace /> },
      { path: 'dashboard', element: <EmployeeDashboardPage /> },
      { path: 'projects', element: <EmployeeProjectsPage /> },
      { path: 'tasks', element: <EmployeeTasksPage /> },
      { path: 'attendance', element: <EmployeeAttendancePage /> },
      { path: 'reports', element: <EmployeeReportsPage /> },
      { path: 'leaves', element: <EmployeeLeavePage /> },
      { path: 'notifications', element: <EmployeeNotificationsPage /> },
      { path: 'profile', element: <EmployeeProfilePage /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/login" replace />,
  },
]);

export default AppRoutes;
