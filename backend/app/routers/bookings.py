from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Booking, Customer, Service, User
from app.schemas import BookingCreate, BookingStatusUpdate, BookingOut
from app.deps import get_current_user, require_role

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

# Valid state machine transitions
ALLOWED_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["completed", "cancelled"],
    "completed": [], # terminal state
    "cancelled": [], # terminal state
}

def generate_booking_no(db: Session) -> str:
    """Generate human-readable booking identifier BK-YYYY-XXXX."""
    current_year = datetime.now(timezone.utc).year
    count = db.query(Booking).count() + 1
    return f"BK-{current_year}-{count:04d}"

@router.get("", response_model=List[BookingOut])
def list_bookings(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List bookings. Customers see only their own bookings; Staff/Admin see all."""
    query = db.query(Booking)
    
    if current_user.role == "customer":
        customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not customer:
            return []
        query = query.filter(Booking.customer_id == customer.id)
    
    if status_filter:
        query = query.filter(Booking.status == status_filter.lower())
        
    return query.order_by(Booking.created_at.desc()).all()

@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve booking by ID."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if current_user.role == "customer":
        customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not customer or booking.customer_id != customer.id:
            raise HTTPException(status_code=403, detail="Cannot access other customers' bookings")

    return booking

@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new booking with initial 'pending' status."""
    # Verify customer
    customer = db.query(Customer).filter(Customer.id == booking_in.customer_id).first()
    if not customer or customer.is_archived:
        raise HTTPException(status_code=400, detail="Customer not found or is archived")

    # If customer role, verify ownership of customer record
    if current_user.role == "customer" and customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot create bookings for other customer accounts")

    # Verify service
    service = db.query(Service).filter(Service.id == booking_in.service_id).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=400, detail="Service not found or inactive")

    # Generate unique readable booking number
    booking_no = generate_booking_no(db)
    
    # Check assigned staff if provided
    staff_id = booking_in.staff_id
    if staff_id:
        staff_user = db.query(User).filter(User.id == staff_id, User.role.in_(["staff", "admin"])).first()
        if not staff_user:
            raise HTTPException(status_code=400, detail="Assigned staff user not found or invalid role")

    booking = Booking(
        booking_no=booking_no,
        customer_id=customer.id,
        service_id=service.id,
        staff_id=staff_id,
        status="pending",
        scheduled_at=booking_in.scheduled_at,
        notes=booking_in.notes,
        total_price=service.price
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(
    booking_id: int,
    status_update: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update booking lifecycle status with strict state machine validation."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    target_status = status_update.status.lower()
    current_status = booking.status.lower()

    # Role-based restriction: Customers can only cancel their own pending/confirmed bookings
    if current_user.role == "customer":
        customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not customer or booking.customer_id != customer.id:
            raise HTTPException(status_code=403, detail="Forbidden")
        if target_status != "cancelled":
            raise HTTPException(status_code=403, detail="Customers can only cancel bookings")

    # Validate state transitions
    valid_targets = ALLOWED_TRANSITIONS.get(current_status, [])
    if target_status not in valid_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from '{current_status}' to '{target_status}'. Valid transitions: {valid_targets}"
        )

    booking.status = target_status
    db.commit()
    db.refresh(booking)
    return booking
