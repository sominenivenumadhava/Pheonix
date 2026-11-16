from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Invoice, Booking, User
from app.schemas import InvoiceCreate, InvoiceOut
from app.deps import get_current_user, require_role

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

def generate_invoice_no(db: Session) -> str:
    """Generate human-readable invoice identifier INV-YYYY-XXXX."""
    current_year = datetime.now(timezone.utc).year
    count = db.query(Invoice).count() + 1
    return f"INV-{current_year}-{count:04d}"

@router.get("", response_model=List[InvoiceOut])
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "staff"]))
):
    """List all billing invoices (Admin and Staff only)."""
    return db.query(Invoice).order_by(Invoice.created_at.desc()).all()

@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve invoice details."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # If customer, verify ownership through booking
    if current_user.role == "customer":
        booking = invoice.booking
        if not booking or booking.customer.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    return invoice

@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_in: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "staff"]))
):
    """
    Generate an invoice against a booking.
    STRICT RULE: Invoices can ONLY be generated for bookings in 'completed' status.
    """
    booking = db.query(Booking).filter(Booking.id == invoice_in.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status.lower() != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoices can only be created for completed bookings. Current status is '{booking.status}'."
        )

    # Check if invoice already exists
    existing_invoice = db.query(Invoice).filter(Invoice.booking_id == booking.id).first()
    if existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice already exists for booking {booking.booking_no} ({existing_invoice.invoice_no})"
        )

    amount = booking.total_price
    tax = invoice_in.tax
    total_amount = round(amount + tax, 2)
    invoice_no = generate_invoice_no(db)

    invoice = Invoice(
        invoice_no=invoice_no,
        booking_id=booking.id,
        amount=amount,
        tax=tax,
        total_amount=total_amount,
        status="issued"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

@router.patch("/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    invoice_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "staff"]))
):
    """Update invoice payment status (e.g. 'paid', 'cancelled')."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    allowed_statuses = ["draft", "issued", "paid", "cancelled"]
    if new_status.lower() not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid invoice status '{new_status}'. Allowed: {allowed_statuses}"
        )

    invoice.status = new_status.lower()
    db.commit()
    db.refresh(invoice)
    return invoice
