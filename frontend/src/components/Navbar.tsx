import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="navbar">
      <NavLink to="/" className="nav-brand">
        PHOENIX PORTAL
      </NavLink>

      <nav className="nav-links">
        {isAuthenticated ? (
          <>
            <NavLink to="/services" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Services
            </NavLink>
            <NavLink to="/bookings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Bookings
            </NavLink>

            {user && (user.role === 'admin' || user.role === 'staff') && (
              <NavLink to="/billing" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Billing
              </NavLink>
            )}

            <NavLink to="/status" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              System Status
            </NavLink>

            <span className="user-badge" data-testid="user-role-badge">
              {user?.role}: {user?.email}
            </span>

            <button onClick={handleLogout} className="btn btn-secondary btn-sm" data-testid="logout-btn">
              Logout
            </button>
          </>
        ) : (
          <NavLink to="/login" className="btn btn-primary btn-sm">
            Sign In
          </NavLink>
        )}
      </nav>
    </header>
  );
};
