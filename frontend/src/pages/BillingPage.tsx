import React, { useState, useEffect } from 'react';
import { Invoice, Booking } from '../types';
import { api } from '../api';

export const BillingPage: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [completedBookings, setCompletedBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New Invoice State
  const [showGenerate, setShowGenerate] = useState(false);
  const [selectedBookingId, setSelectedBookingId] = useState<string>('');
  const [tax, setTax] = useState<string>('0.00');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [invoicesData, allBookings] = await Promise.all([
        api.getInvoices(),
        api.getBookings('completed')
      ]);
      setInvoices(invoicesData);
      setCompletedBookings(allBookings);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error fetching billing records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGenerateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMsg(null);

    const bookingId = parseInt(selectedBookingId, 10);
    const taxNum = parseFloat(tax) || 0;

    if (!bookingId) {
      setFormError('Please select a completed appointment.');
      return;
    }

    try {
      setSubmitting(true);
      const newInv = await api.createInvoice(bookingId, taxNum);
      setSuccessMsg(`Invoice ${newInv.invoice_no} issued successfully! Total: $${newInv.total_amount.toFixed(2)}`);
      setShowGenerate(false);
      setSelectedBookingId('');
      setTax('0.00');
      await fetchData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to generate invoice');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Billing & Accounts Receivable</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Financial invoicing strictly generated against verified completed service bookings
          </p>
        </div>
        <button
          onClick={() => setShowGenerate(!showGenerate)}
          className="btn btn-primary"
          data-testid="toggle-generate-invoice-btn"
        >
          {showGenerate ? 'Close Form' : '+ Issue Invoice'}
        </button>
      </div>

      {successMsg && <div className="alert alert-success">{successMsg}</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      {showGenerate && (
        <div className="card" data-testid="generate-invoice-card">
          <h3 className="card-title">Generate Billing Record (Completed Bookings Only)</h3>
          {formError && <div className="alert alert-danger">{formError}</div>}
          <form onSubmit={handleGenerateInvoice}>
            <div className="form-group">
              <label className="form-label" htmlFor="booking-select">Completed Booking</label>
              <select
                id="booking-select"
                className="form-select"
                value={selectedBookingId}
                onChange={(e) => setSelectedBookingId(e.target.value)}
                disabled={submitting}
              >
                <option value="">-- Choose Completed Booking --</option>
                {completedBookings.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.booking_no} — Service Price: ${b.total_price.toFixed(2)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="tax-amount">Tax Amount ($ USD)</label>
              <input
                id="tax-amount"
                type="number"
                step="0.01"
                className="form-input"
                value={tax}
                onChange={(e) => setTax(e.target.value)}
                placeholder="0.00"
                disabled={submitting}
              />
            </div>

            <button type="submit" className="btn btn-success" disabled={submitting}>
              {submitting ? 'Generating Invoice...' : 'Confirm & Issue Invoice'}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="state-loading">Loading invoices...</div>
      ) : invoices.length === 0 ? (
        <div className="card state-empty">No invoices currently generated.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Booking ID</th>
                <th>Base Amount</th>
                <th>Tax</th>
                <th>Total Billed</th>
                <th>Status</th>
                <th>Issued Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td><strong>{inv.invoice_no}</strong></td>
                  <td>Booking #{inv.booking_id}</td>
                  <td>${inv.amount.toFixed(2)}</td>
                  <td>${inv.tax.toFixed(2)}</td>
                  <td><strong>${inv.total_amount.toFixed(2)}</strong></td>
                  <td>
                    <span className={`badge ${inv.status === 'paid' ? 'badge-healthy' : 'badge-pending'}`}>
                      {inv.status}
                    </span>
                  </td>
                  <td>{new Date(inv.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
