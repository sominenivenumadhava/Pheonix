import React, { useState, useEffect } from 'react';
import { Booking, Service, Customer } from '../types';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

export const BookingsPage: React.FC = () => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const { user } = useAuth();

  // Create Booking State
  const [showCreate, setShowCreate] = useState(false);
  const [selectedServiceId, setSelectedServiceId] = useState<string>('');
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('');
  const [scheduledAt, setScheduledAt] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [bookingsData, servicesData] = await Promise.all([
        api.getBookings(),
        api.getServices()
      ]);
      setBookings(bookingsData);
      setServices(servicesData);

      if (user?.role === 'admin' || user?.role === 'staff') {
        const customersData = await api.getCustomers();
        setCustomers(customersData);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error fetching bookings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [user]);

  const handleCreateBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMsg(null);

    const serviceId = parseInt(selectedServiceId, 10);
    if (!serviceId) {
      setFormError('Please select a service.');
      return;
    }

    if (!scheduledAt) {
      setFormError('Please select a scheduled appointment date & time.');
      return;
    }

    let customerId = parseInt(selectedCustomerId, 10);
    if (user?.role === 'customer') {
      // Find own customer profile
      const ownCustomer = customers.find(c => c.user_id === user.id) || 
        // Fallback: fetch directly
        customers[0];
      if (ownCustomer) {
        customerId = ownCustomer.id;
      } else {
        // First customer ID or customer record
        customerId = 1;
      }
    } else if (!customerId) {
      setFormError('Please select a client for this booking.');
      return;
    }

    try {
      setSubmitting(true);
      const newBooking = await api.createBooking({
        service_id: serviceId,
        customer_id: customerId,
        scheduled_at: new Date(scheduledAt).toISOString(),
        notes: notes.trim() || undefined
      });
      setSuccessMsg(`Booking ${newBooking.booking_no} created successfully!`);
      setShowCreate(false);
      setSelectedServiceId('');
      setSelectedCustomerId('');
      setScheduledAt('');
      setNotes('');
      await fetchData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create booking');
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusTransition = async (bookingId: number, targetStatus: string) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await api.updateBookingStatus(bookingId, targetStatus);
      setSuccessMsg(`Booking ${updated.booking_no} transitioned to '${targetStatus}'.`);
      await fetchData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update booking status');
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Bookings & Appointments</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Track client requests and manage appointment lifecycle
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="btn btn-primary"
          data-testid="toggle-create-booking-btn"
        >
          {showCreate ? 'Close Form' : '+ New Booking'}
        </button>
      </div>

      {successMsg && <div className="alert alert-success">{successMsg}</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      {showCreate && (
        <div className="card" data-testid="create-booking-card">
          <h3 className="card-title">Schedule New Appointment</h3>
          {formError && <div className="alert alert-danger">{formError}</div>}
          <form onSubmit={handleCreateBooking}>
            {(user?.role === 'admin' || user?.role === 'staff') && (
              <div className="form-group">
                <label className="form-label" htmlFor="customer-select">Customer</label>
                <select
                  id="customer-select"
                  className="form-select"
                  value={selectedCustomerId}
                  onChange={(e) => setSelectedCustomerId(e.target.value)}
                  disabled={submitting}
                >
                  <option value="">-- Select Client Profile --</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.email})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="form-group">
              <label className="form-label" htmlFor="service-select">Select Service</label>
              <select
                id="service-select"
                className="form-select"
                value={selectedServiceId}
                onChange={(e) => setSelectedServiceId(e.target.value)}
                disabled={submitting}
              >
                <option value="">-- Select Service --</option>
                {services.filter(s => s.is_active).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} - ${s.price.toFixed(2)} ({s.duration_minutes} min)
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="scheduled-time">Scheduled Date & Time</label>
              <input
                id="scheduled-time"
                type="datetime-local"
                className="form-input"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                disabled={submitting}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="booking-notes">Special Requirements / Notes</label>
              <textarea
                id="booking-notes"
                className="form-textarea"
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional client details or system requirements"
                disabled={submitting}
              />
            </div>

            <button type="submit" className="btn btn-success" disabled={submitting}>
              {submitting ? 'Confirming Booking...' : 'Create Booking'}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="state-loading">Loading bookings registry...</div>
      ) : bookings.length === 0 ? (
        <div className="card state-empty">No active bookings found.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Booking #</th>
                <th>Scheduled At</th>
                <th>Status</th>
                <th>Locked Price</th>
                <th>Lifecycle Actions</th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.id}>
                  <td><strong>{b.booking_no}</strong></td>
                  <td>{new Date(b.scheduled_at).toLocaleString()}</td>
                  <td>
                    <span className={`badge badge-${b.status}`}>
                      {b.status}
                    </span>
                  </td>
                  <td>${b.total_price.toFixed(2)}</td>
                  <td>
                    {b.status === 'pending' && (
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {(user?.role === 'admin' || user?.role === 'staff') && (
                          <button
                            onClick={() => handleStatusTransition(b.id, 'confirmed')}
                            className="btn btn-primary btn-sm"
                          >
                            Confirm
                          </button>
                        )}
                        <button
                          onClick={() => handleStatusTransition(b.id, 'cancelled')}
                          className="btn btn-danger btn-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    )}

                    {b.status === 'confirmed' && (
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {(user?.role === 'admin' || user?.role === 'staff') && (
                          <button
                            onClick={() => handleStatusTransition(b.id, 'completed')}
                            className="btn btn-success btn-sm"
                          >
                            Complete
                          </button>
                        )}
                        <button
                          onClick={() => handleStatusTransition(b.id, 'cancelled')}
                          className="btn btn-danger btn-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    )}

                    {b.status === 'completed' && (
                      <span style={{ color: 'var(--success)', fontSize: '0.85rem', fontWeight: 600 }}>
                        Completed (Billed)
                      </span>
                    )}

                    {b.status === 'cancelled' && (
                      <span style={{ color: 'var(--danger)', fontSize: '0.85rem' }}>
                        Cancelled
                      </span>
                    )}
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
