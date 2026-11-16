import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../src/components/ProtectedRoute';
import * as AuthContextModule from '../src/context/AuthContext';

describe('ProtectedRoute Component', () => {
  it('redirects unauthenticated users to login', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      token: null,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      isAuthenticated: false,
    });

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Secret Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page Target</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByText('Secret Content')).not.toBeInTheDocument();
    expect(screen.getByText('Login Page Target')).toBeInTheDocument();
  });

  it('blocks users without required role and shows access denied', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 3,
        email: 'customer@phoenix.local',
        full_name: 'Customer Test',
        role: 'customer',
        is_active: true,
      },
      token: 'dummy-token',
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      isAuthenticated: true,
    });

    render(
      <MemoryRouter initialEntries={['/admin-only']}>
        <Routes>
          <Route
            path="/admin-only"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <div>Admin Secret Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByText('Admin Secret Content')).not.toBeInTheDocument();
    expect(screen.getByTestId('unauthorized-message')).toHaveTextContent('Access Denied');
  });

  it('renders children when authenticated with authorized role', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 1,
        email: 'admin@phoenix.local',
        full_name: 'Admin Test',
        role: 'admin',
        is_active: true,
      },
      token: 'dummy-admin-token',
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      isAuthenticated: true,
    });

    render(
      <MemoryRouter initialEntries={['/admin-only']}>
        <Routes>
          <Route
            path="/admin-only"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <div data-testid="admin-content">Admin Secret Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('admin-content')).toBeInTheDocument();
  });
});
