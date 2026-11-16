import re
from datetime import datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field, AfterValidator, ConfigDict

def validate_email_format(v: str) -> str:
    """Validate RFC email format while allowing local testing domains like .local."""
    if not isinstance(v, str):
        raise ValueError("Email must be a string")
    v = v.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
        raise ValueError("Invalid email format")
    return v

EmailStr = Annotated[str, AfterValidator(validate_email_format)]

# --- Auth & Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    email: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "customer" # admin, staff, customer
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    user_id: Optional[int] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_archived: Optional[bool] = None

class CustomerOut(CustomerBase):
    id: int
    user_id: Optional[int] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Service Schemas ---
class ServiceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    duration_minutes: int = Field(default=60, gt=0)
    is_active: bool = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0.0)
    duration_minutes: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None

class ServiceOut(ServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Booking Schemas ---
class BookingBase(BaseModel):
    customer_id: int
    service_id: int
    scheduled_at: datetime
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    staff_id: Optional[int] = None

class BookingStatusUpdate(BaseModel):
    status: str = Field(..., description="Target status: confirmed, completed, or cancelled")

class BookingOut(BaseModel):
    id: int
    booking_no: str
    customer_id: int
    service_id: int
    staff_id: Optional[int] = None
    status: str
    scheduled_at: datetime
    notes: Optional[str] = None
    total_price: float
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerOut] = None
    service: Optional[ServiceOut] = None

    model_config = ConfigDict(from_attributes=True)

# --- Invoice Schemas ---
class InvoiceCreate(BaseModel):
    booking_id: int
    tax: float = Field(default=0.0, ge=0.0)

class InvoiceOut(BaseModel):
    id: int
    invoice_no: str
    booking_id: int
    amount: float
    tax: float
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Backup Record Schemas ---
class BackupRecordCreate(BaseModel):
    location: str
    size_bytes: int = Field(..., gt=0)
    checksum_sha256: str
    restore_verified: bool = False
    details: Optional[str] = None

class BackupRecordOut(BaseModel):
    id: int
    timestamp: datetime
    location: str
    size_bytes: int
    checksum_sha256: str
    restore_verified: bool
    details: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Recovery Event Schemas ---
class RecoveryEventCreate(BaseModel):
    event_type: str
    detail: Optional[str] = None
    triggered_by: str

class RecoveryEventOut(BaseModel):
    id: int
    event_type: str
    detail: Optional[str]
    triggered_by: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Health & Operational Schemas ---
class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    db: str

class ReadyResponse(BaseModel):
    ready: bool
    checks: dict
    timestamp: datetime

class SystemStatusResponse(BaseModel):
    status: str
    app_version: str
    uptime_status: str
    total_users: int
    total_customers: int
    total_services: int
    total_bookings: int
    total_invoices: int
    latest_backup: Optional[BackupRecordOut] = None
    recent_recovery_events: List[RecoveryEventOut] = []
