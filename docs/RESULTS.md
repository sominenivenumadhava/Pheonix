# PHOENIX: Test, Execution & Verification Log (RESULTS.md)

This document is the single source of truth for all test executions, demonstrations, and operational checks for Project **PHOENIX**.
Per project rules:
- **No invented results**: Only tests and commands physically executed are marked as PASSED.
- **Unrun tests**: Any test or operational check that cannot be run in the current environment is explicitly listed as **NOT RUN** with the exact technical reason.

---

## 1. Test Execution Summary

| Phase / Component | Total Checks | Passed | Failed | Not Run | Status |
|---|---|---|---|---|---|
| **Phase 0: Repo Skeleton** | 3 | 3 | 0 | 0 | Completed |
| **Day 1: Backend & DB** | 32 | 32 | 0 | 0 | Completed |
| **Day 2: Frontend (Vite+React)** | 0 | 0 | 0 | 0 | Pending |
| **Day 3: Puppet & Drift** | 0 | 0 | 0 | 0 | Pending |
| **Day 4: Ansible & DR** | 0 | 0 | 0 | 0 | Pending |
| **Day 5: Terraform, Nagios & Demo** | 0 | 0 | 0 | 0 | Pending |

---

## 2. Detailed Execution Log

### Phase 0: Repository Skeleton & Governance
| Check ID | Description | Execution Command | Result | Notes / Evidence |
|---|---|---|---|---|
| **P0-CHK-01** | Git repository initialization | `git status` | **PASSED** | Repository initialized on branch `master` |
| **P0-CHK-02** | Security .gitignore verification | `git check-ignore -v .env id_rsa test.db .terraform/ ...` | **PASSED** | Verified secrets, keys, DBs, and vaults ignored |
| **P0-CHK-03** | Monorepo folder hierarchy | Directory inspection | **PASSED** | All 8 required modules verified present |

### Day 1: Backend, Database, Auth & Operational Verification
**Execution Timestamp**: 2026-11-16 11:12:06 IST  
**Environment**: Python 3.12.9, pytest 9.2.0, SQLite 3 (WAL mode), platform Windows 11  

| Check ID | Test File / Feature | Test Function Name | Result | Evidence / Details |
|---|---|---|---|---|
| **D1-CHK-01** | Database Seeder | `python backend/seed.py` | **PASSED** | Initialized tables; seeded Admin, Staff, Customer, Inactive users & 4 services |
| **D1-CHK-02** | Backup Snapshot Script | `python scripts/backup.py` | **PASSED** | Created snapshot in `backups/`, calculated SHA-256, verified integrity (`ok`), logged to `backup_records` |
| **D1-CHK-03** | Restore & Verification | `python scripts/restore.py` | **PASSED** | Restored snapshot to disposable DB, verified integrity (`ok`), verified table row counts match, logged `DATABASE_RESTORE` event |
| **D1-CHK-04** | Auth: Login Valid | `test_auth.py::test_login_success` | **PASSED** | HTTP 200, returned signed JWT bearer token and user role |
| **D1-CHK-05** | Auth: Invalid Password | `test_auth.py::test_login_invalid_password` | **PASSED** | HTTP 401 Unauthorized |
| **D1-CHK-06** | Auth: Unknown User | `test_auth.py::test_login_unknown_user` | **PASSED** | HTTP 401 Unauthorized |
| **D1-CHK-07** | Auth: Inactive Account | `test_auth.py::test_login_inactive_user_blocked` | **PASSED** | HTTP 403 Forbidden with inactive detail |
| **D1-CHK-08** | Auth: User Profile | `test_auth.py::test_get_current_user_profile` | **PASSED** | HTTP 200, returns claims of authenticated user |
| **D1-CHK-09** | Auth: Unauthenticated | `test_auth.py::test_protected_route_without_token` | **PASSED** | HTTP 401 Unauthorized |
| **D1-CHK-10** | Backup: API Audit | `test_backups.py::test_backup_record_logging_and_retrieval` | **PASSED** | HTTP 201 created audit record, retrieved in listing |
| **D1-CHK-11** | Recovery: Event Audit | `test_backups.py::test_recovery_event_audit_logging` | **PASSED** | HTTP 201 recorded `DRIFT_REPAIRED` event |
| **D1-CHK-12** | Ops: Status Dashboard | `test_backups.py::test_system_status_endpoint` | **PASSED** | HTTP 200 returned total entity counts & latest backup info |
| **D1-CHK-13** | Bookings: Creation | `test_bookings.py::test_create_booking_persistence` | **PASSED** | HTTP 201 created booking with `BK-YYYY-XXXX`, status `pending` |
| **D1-CHK-14** | Bookings: Valid Flow | `test_bookings.py::test_booking_status_workflow` | **PASSED** | Valid transitions: `pending` $\to$ `confirmed` $\to$ `completed` |
| **D1-CHK-15** | Bookings: Skip Status | `test_bookings.py::test_invalid_booking_transition_skip_confirmed` | **PASSED** | HTTP 400 rejected skipping `confirmed` |
| **D1-CHK-16** | Bookings: Terminal State | `test_bookings.py::test_completed_booking_is_terminal` | **PASSED** | HTTP 400 rejected transitioning out of `completed` |
| **D1-CHK-17** | Bookings: Cancellation | `test_bookings.py::test_booking_cancellation_workflow` | **PASSED** | Cancelled pending booking; rejected reopening cancelled booking |
| **D1-CHK-18** | Invoices: Valid Invoice | `test_invoices.py::test_invoice_creation_for_completed_booking` | **PASSED** | HTTP 201 generated `INV-YYYY-XXXX` with subtotal and tax |
| **D1-CHK-19** | Invoices: Uncompleted | `test_invoices.py::test_invoice_creation_rejected_for_uncompleted_booking` | **PASSED** | HTTP 400 rejected invoice creation on pending/confirmed bookings |
| **D1-CHK-20** | Invoices: Duplicate Block | `test_invoices.py::test_duplicate_invoice_prevented` | **PASSED** | HTTP 400 prevented duplicate invoice for same booking |
| **D1-CHK-21** | Invoices: Status Update | `test_invoices.py::test_invoice_status_update` | **PASSED** | HTTP 200 updated status to `paid` |
| **D1-CHK-22** | Roles: Admin Service | `test_roles.py::test_admin_can_create_service` | **PASSED** | HTTP 201 Admin successfully created service |
| **D1-CHK-23** | Roles: Staff Service Block | `test_roles.py::test_staff_cannot_create_service` | **PASSED** | HTTP 403 Staff blocked from service creation |
| **D1-CHK-24** | Roles: Customer Service Block | `test_roles.py::test_customer_cannot_create_service` | **PASSED** | HTTP 403 Customer blocked from service creation |
| **D1-CHK-25** | Roles: Customer List Block | `test_roles.py::test_customer_cannot_list_all_customers` | **PASSED** | HTTP 403 Customer cannot browse global customer registry |
| **D1-CHK-26** | Roles: Staff/Admin Access | `test_roles.py::test_staff_and_admin_can_list_customers` | **PASSED** | HTTP 200 Staff and Admin can view customer list |
| **D1-CHK-27** | Roles: Service Deactivate | `test_roles.py::test_admin_can_deactivate_service` | **PASSED** | HTTP 200 Admin soft-deleted / deactivated service |
| **D1-CHK-28** | Validation: Malformed Email | `test_validation.py::test_login_invalid_email_format` | **PASSED** | HTTP 422 rejected invalid email format |
| **D1-CHK-29** | Validation: Negative Price | `test_validation.py::test_service_validation_negative_price` | **PASSED** | HTTP 422 rejected negative price |
| **D1-CHK-30** | Validation: Empty Name | `test_validation.py::test_service_validation_empty_name` | **PASSED** | HTTP 422 rejected name below minimum length |
| **D1-CHK-31** | Probe: Nagios /health | `test_validation.py::test_health_check_endpoint` | **PASSED** | HTTP 200 returned `status: "healthy"`, `db: "ok"` |
| **D1-CHK-32** | Probe: Ansible /ready | `test_validation.py::test_readiness_probe_endpoint` | **PASSED** | HTTP 200 returned `ready: true`, database verified |

---

## 3. Environment Limitations & Unrun Items Log

| Date | Target Subsystem | Intended Check | Reason for Not Running | Remediation / Next Action |
|---|---|---|---|---|
| 2026-11-16 | AWS Infrastructure | `terraform apply` on AWS | Awaiting user instructions and active AWS session approval | Maintained in IaC templates; dry-run via `terraform validate` |
| 2026-11-16 | VirtualBox Lab | VM headless boot | Host virtualization nested VT-x check requires manual user terminal | VirtualBox VM definitions provided; scripts ready for manual execution |
