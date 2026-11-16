from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Customer, User
from app.schemas import CustomerCreate, CustomerUpdate, CustomerOut
from app.deps import get_current_user, require_role

router = APIRouter(prefix="/api/customers", tags=["Customers"])

@router.get("", response_model=List[CustomerOut])
def list_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "staff"]))
):
    """List non-archived customers (Admin/Staff only)."""
    return db.query(Customer).filter(Customer.is_archived == False).all()

@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve customer details. Customers can view their own profile."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if current_user.role == "customer" and customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access other customers' profiles")

    return customer

@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create customer profile. Customers can register their own profile; staff/admin can register any."""
    # Check if email is already in use by another customer
    existing = db.query(Customer).filter(Customer.email == customer_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Customer with this email already exists")

    # If customer role, bind to current user ID
    user_id = customer_in.user_id
    if current_user.role == "customer":
        user_id = current_user.id

    customer = Customer(
        name=customer_in.name,
        email=customer_in.email,
        phone=customer_in.phone,
        address=customer_in.address,
        user_id=user_id
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update customer details."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if current_user.role == "customer" and customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit other customers' profiles")

    update_data = customer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer

@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
def archive_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "staff"]))
):
    """Soft-delete / archive customer record (Admin/Staff only)."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.is_archived = True
    db.commit()
    return {"message": f"Customer '{customer.name}' archived successfully"}
