# Phoenix Frontend – Small Business Portal UI

Lightweight, resilient frontend interface built with **React**, **TypeScript**, and **Vite** using **Plain CSS**.

---

## 1. Design & Security Principles
- **Zero External CDNs**: All scripts, fonts, and assets are local; no third-party CDNs.
- **Zero External Icon Fonts**: Clean, accessible CSS badges and unicode indicators.
- **Role-Aware Views**: Dynamic navigation and page gates for `admin`, `staff`, and `customer`.
- **Form Validation & State Handling**: Strict client-side validation, loading spinners, error alerts, and empty-state placeholders.

---

## 2. Pages & Features

1. **Login Page (`/login`)**:
   - Secure authentication against `/auth/login`
   - Client-side email validation and inactive account alert handling
   - Token persistence in memory & `localStorage`
2. **Services Catalog (`/services`)**:
   - Lists active business services with standard pricing
   - Inline creation of new offerings for `admin` role
3. **Bookings & Appointments (`/bookings`)**:
   - State machine lifecycle (`pending` $\to$ `confirmed` $\to$ `completed` / `cancelled`)
   - Appointment creation form with service selection and scheduling
   - Customer users see only their own bookings; Staff/Admin see all
4. **Billing & Invoices (`/billing`)**:
   - Restricted to `admin` and `staff` roles
   - Automated invoice generation strictly restricted to completed bookings
5. **System & DevOps Status (`/status`)**:
   - Live telemetry probing `/health` (Nagios target probe) and `/api/status`
   - Real-time display of latest verified database backup and self-healing audit trail

---

## 3. Running & Testing

### Development Server
```bash
npm run dev
```
Runs Vite development server at [http://localhost:5173](http://localhost:5173).

### Running Tests
```bash
npm test
```
Executes Vitest suite with `@testing-library/react`.

### Production Build
```bash
npm run build
```
Generates optimized static bundle in `frontend/dist/`.
