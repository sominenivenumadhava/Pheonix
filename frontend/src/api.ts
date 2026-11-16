import {
  User, Service, Customer, Booking, Invoice, HealthStatus, SystemStatus
} from './types';

const TOKEN_KEY = 'phoenix_auth_token';

export const getAuthToken = (): string | null => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(TOKEN_KEY);
    }
  } catch {
    // fallback
  }
  return null;
};

export const setAuthToken = (token: string): void => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(TOKEN_KEY, token);
    }
  } catch {
    // fallback
  }
};

export const removeAuthToken = (): void => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // fallback
  }
};

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (options.body && typeof options.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' 
          ? errorJson.detail 
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Authentication
  login: async (email: string, password: string): Promise<{ access_token: string; role: string; email: string }> => {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  getMe: async (): Promise<User> => {
    return request<User>('/auth/me');
  },

  // Services
  getServices: async (): Promise<Service[]> => {
    return request<Service[]>('/api/services');
  },

  createService: async (service: Partial<Service>): Promise<Service> => {
    return request<Service>('/api/services', {
      method: 'POST',
      body: JSON.stringify(service),
    });
  },

  // Customers
  getCustomers: async (): Promise<Customer[]> => {
    return request<Customer[]>('/api/customers');
  },

  createCustomer: async (customer: Partial<Customer>): Promise<Customer> => {
    return request<Customer>('/api/customers', {
      method: 'POST',
      body: JSON.stringify(customer),
    });
  },

  // Bookings
  getBookings: async (status?: string): Promise<Booking[]> => {
    const url = status ? `/api/bookings?status_filter=${status}` : '/api/bookings';
    return request<Booking[]>(url);
  },

  createBooking: async (bookingData: { customer_id: number; service_id: number; scheduled_at: string; notes?: string }): Promise<Booking> => {
    return request<Booking>('/api/bookings', {
      method: 'POST',
      body: JSON.stringify(bookingData),
    });
  },

  updateBookingStatus: async (bookingId: number, status: string): Promise<Booking> => {
    return request<Booking>(`/api/bookings/${bookingId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  // Invoices
  getInvoices: async (): Promise<Invoice[]> => {
    return request<Invoice[]>('/api/invoices');
  },

  createInvoice: async (bookingId: number, tax: number = 0): Promise<Invoice> => {
    return request<Invoice>('/api/invoices', {
      method: 'POST',
      body: JSON.stringify({ booking_id: bookingId, tax }),
    });
  },

  // Health and System Operations
  getHealth: async (): Promise<HealthStatus> => {
    return request<HealthStatus>('/health');
  },

  getSystemStatus: async (): Promise<SystemStatus> => {
    return request<SystemStatus>('/api/status');
  },
};
