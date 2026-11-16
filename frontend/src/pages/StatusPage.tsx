import React, { useState, useEffect } from 'react';
import { HealthStatus, SystemStatus } from '../types';
import { api } from '../api';

export const StatusPage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const [healthData, statusData] = await Promise.all([
        api.getHealth(),
        api.getSystemStatus()
      ]);
      setHealth(healthData);
      setSystemStatus(statusData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error polling system status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="container">
      <div className="page-header">
        <div>
          <h1 className="page-title">DevOps & System Status</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Real-time Nagios target probe and Disaster Recovery audit telemetry
          </p>
        </div>
        <button onClick={fetchStatus} className="btn btn-secondary" disabled={loading}>
          {loading ? 'Polling...' : 'Refresh Status'}
        </button>
      </div>

      {error && (
        <div className="alert alert-danger" data-testid="status-error-alert">
          <strong>System Health Alert:</strong> {error}
        </div>
      )}

      {/* --- Live Probes Summary --- */}
      <div className="card" data-testid="health-probe-card">
        <h3 className="card-title">Live Application Probes (Nagios Target)</h3>
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
          <div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block' }}>Application Health</span>
            <span className={`badge ${health?.status === 'healthy' ? 'badge-healthy' : 'badge-critical'}`} style={{ fontSize: '1rem', marginTop: '0.25rem' }}>
              {health?.status || 'UNKNOWN'}
            </span>
          </div>

          <div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block' }}>Database Probe</span>
            <span className="badge badge-healthy" style={{ fontSize: '1rem', marginTop: '0.25rem' }}>
              DB: {health?.db || 'N/A'}
            </span>
          </div>

          <div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block' }}>Engine Version</span>
            <strong style={{ display: 'block', marginTop: '0.25rem' }}>{health?.version || '1.0.0'}</strong>
          </div>
        </div>
      </div>

      {/* --- Metrics Grid --- */}
      {systemStatus && (
        <div className="metric-grid">
          <div className="metric-card">
            <div className="metric-label">Active Users</div>
            <div className="metric-value">{systemStatus.total_users}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Client Accounts</div>
            <div className="metric-value">{systemStatus.total_customers}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Active Services</div>
            <div className="metric-value">{systemStatus.total_services}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Total Bookings</div>
            <div className="metric-value">{systemStatus.total_bookings}</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Invoices Issued</div>
            <div className="metric-value">{systemStatus.total_invoices}</div>
          </div>
        </div>
      )}

      {/* --- Latest Verified Backup --- */}
      <div className="card" data-testid="latest-backup-card">
        <h3 className="card-title">Latest Verified Database Snapshot</h3>
        {systemStatus?.latest_backup ? (
          <div>
            <p><strong>Snapshot Timestamp:</strong> {new Date(systemStatus.latest_backup.timestamp).toLocaleString()}</p>
            <p><strong>Storage Location:</strong> <code>{systemStatus.latest_backup.location}</code></p>
            <p><strong>Snapshot Size:</strong> {(systemStatus.latest_backup.size_bytes / 1024).toFixed(1)} KB</p>
            <p><strong>SHA-256 Digest:</strong> <code>{systemStatus.latest_backup.checksum_sha256}</code></p>
            <p>
              <strong>Integrity Verification:</strong>{' '}
              <span className={`badge ${systemStatus.latest_backup.restore_verified ? 'badge-healthy' : 'badge-pending'}`}>
                {systemStatus.latest_backup.restore_verified ? 'Restore Verified' : 'Created & Hash Checked'}
              </span>
            </p>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No backups logged yet in audit registry.</p>
        )}
      </div>

      {/* --- Recent Self-Healing & Recovery Events --- */}
      <div className="card" data-testid="recovery-events-card">
        <h3 className="card-title">DevOps Recovery & Self-Healing Audit Trail</h3>
        {systemStatus?.recent_recovery_events && systemStatus.recent_recovery_events.length > 0 ? (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event Type</th>
                  <th>Actor / Automation</th>
                  <th>Audit Detail</th>
                </tr>
              </thead>
              <tbody>
                {systemStatus.recent_recovery_events.map((evt) => (
                  <tr key={evt.id}>
                    <td>{new Date(evt.timestamp).toLocaleString()}</td>
                    <td>
                      <span className="badge badge-confirmed">{evt.event_type}</span>
                    </td>
                    <td><strong>{evt.triggered_by}</strong></td>
                    <td style={{ color: 'var(--text-muted)' }}>{evt.detail || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No disaster recovery or drift events logged.</p>
        )}
      </div>
    </div>
  );
};
