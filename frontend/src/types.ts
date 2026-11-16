export type UserRole = 'admin' | 'staff' | 'customer';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Customer {
  id: number;
  user_id?: number | null;
  name: string;
  email: string;
  phone?: string | null;
  address?: string | null;
  is_archived: boolean;
}

export interface Service {
  id: number;
  name: string;
  description?: string | null;
  price: number;
  duration_minutes: number;
  is_active: boolean;
}

export interface Booking {
  id: number;
  booking_no: string;
  customer_id: number;
  service_id: number;
  staff_id?: number | null;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled';
  scheduled_at: string;
  notes?: string | null;
  total_price: number;
  created_at: string;
  customer?: Customer;
  service?: Service;
}

export interface Invoice {
  id: number;
  invoice_no: string;
  booking_id: number;
  amount: number;
  tax: number;
  total_amount: number;
  status: 'draft' | 'issued' | 'paid' | 'cancelled';
  created_at: string;
}

export interface BackupRecord {
  id: number;
  timestamp: string;
  location: string;
  size_bytes: number;
  checksum_sha256: string;
  restore_verified: boolean;
  details?: string | null;
}

export interface RecoveryEvent {
  id: number;
  event_type: string;
  detail?: string | null;
  triggered_by: string;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  db: string;
}

export interface SystemStatus {
  status: string;
  app_version: string;
  uptime_status: string;
  total_users: number;
  total_customers: number;
  total_services: number;
  total_bookings: number;
  total_invoices: number;
  latest_backup?: BackupRecord | null;
  recent_recovery_events: RecoveryEvent[];
}
