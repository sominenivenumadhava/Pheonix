import React, { useState, useEffect } from 'react';
import { Service } from '../types';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

export const ServicesPage: React.FC = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  // Admin New Service Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [duration, setDuration] = useState('60');
  const [formError, setFormError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const fetchServices = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getServices();
      setServices(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch services');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
  }, []);

  const handleCreateService = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const priceNum = parseFloat(price);
    const durationNum = parseInt(duration, 10);

    if (!name.trim()) {
      setFormError('Service name is required.');
      return;
    }

    if (isNaN(priceNum) || priceNum < 0) {
      setFormError('Price must be a positive number.');
      return;
    }

    try {
      setCreating(true);
      await api.createService({
        name: name.trim(),
        description: description.trim() || undefined,
        price: priceNum,
        duration_minutes: durationNum || 60,
        is_active: true
      });
      setName('');
      setDescription('');
      setPrice('');
      setDuration('60');
      setShowAddForm(false);
      await fetchServices();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Error creating service');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Service Catalog</h1>
          <p style={{ color: 'var(--text-muted)' }}>Available IT & DevOps business offerings</p>
        </div>
        {user?.role === 'admin' && (
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn btn-primary"
            data-testid="toggle-add-service-btn"
          >
            {showAddForm ? 'Cancel' : '+ Add Service'}
          </button>
        )}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {showAddForm && user?.role === 'admin' && (
        <div className="card" data-testid="add-service-card">
          <h3 className="card-title">Create New Service Offering</h3>
          {formError && <div className="alert alert-danger">{formError}</div>}
          <form onSubmit={handleCreateService}>
            <div className="form-group">
              <label className="form-label" htmlFor="svc-name">Service Title</label>
              <input
                id="svc-name"
                className="form-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Cloud Disaster Recovery Audit"
                disabled={creating}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="svc-desc">Description</label>
              <textarea
                id="svc-desc"
                className="form-textarea"
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Scope of work and deliverables"
                disabled={creating}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="svc-price">Price ($ USD)</label>
                <input
                  id="svc-price"
                  type="number"
                  step="0.01"
                  className="form-input"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="250.00"
                  disabled={creating}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="svc-duration">Duration (Minutes)</label>
                <input
                  id="svc-duration"
                  type="number"
                  className="form-input"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  placeholder="60"
                  disabled={creating}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-success" disabled={creating}>
              {creating ? 'Saving...' : 'Save Service'}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="state-loading">Loading service catalog...</div>
      ) : services.length === 0 ? (
        <div className="card state-empty">No services currently listed.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Service Name</th>
                <th>Description</th>
                <th>Duration</th>
                <th>Standard Price</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {services.map((svc) => (
                <tr key={svc.id}>
                  <td><strong>{svc.name}</strong></td>
                  <td style={{ color: 'var(--text-muted)' }}>{svc.description || '—'}</td>
                  <td>{svc.duration_minutes} mins</td>
                  <td><strong>${svc.price.toFixed(2)}</strong></td>
                  <td>
                    <span className={`badge ${svc.is_active ? 'badge-healthy' : 'badge-cancelled'}`}>
                      {svc.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
