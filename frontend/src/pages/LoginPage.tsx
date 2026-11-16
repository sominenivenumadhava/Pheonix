import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Form validation
    if (!email.trim() || !password.trim()) {
      setError('Both email and password are required.');
      return;
    }

    if (!email.includes('@')) {
      setError('Please provide a valid email address.');
      return;
    }

    try {
      setLoading(true);
      await login(email, password);
      navigate('/services');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Login failed. Please verify your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '440px', marginTop: '4rem' }}>
      <div className="card">
        <h2 className="card-title" style={{ textAlign: 'center' }}>Portal Sign In</h2>

        {error && (
          <div className="alert alert-danger" data-testid="login-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} data-testid="login-form">
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <input
              id="email"
              type="text"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. admin@phoenix.local"
              autoComplete="username"
              disabled={loading}
              data-testid="email-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              autoComplete="current-password"
              disabled={loading}
              data-testid="password-input"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.5rem' }}
            disabled={loading}
            data-testid="login-submit-btn"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '1.25rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <strong>Default Seed Accounts:</strong>
          <ul style={{ paddingLeft: '1.2rem', marginTop: '0.25rem' }}>
            <li>Admin: <code>admin@phoenix.local</code> (AdminPass123!)</li>
            <li>Staff: <code>staff@phoenix.local</code> (StaffPass123!)</li>
            <li>Client: <code>customer@phoenix.local</code> (CustomerPass123!)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
