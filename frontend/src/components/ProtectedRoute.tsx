import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';

interface ProtectedRouteProps {
  children: React.ReactElement;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div className="container">
        <div className="card state-loading" data-testid="auth-loading">
          Loading authentication state...
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="container">
        <div className="alert alert-danger" data-testid="unauthorized-message">
          <strong>Access Denied:</strong> Your role ({user.role}) does not have permission to access this page.
        </div>
      </div>
    );
  }

  return children;
};
