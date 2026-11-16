from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Service, User
from app.schemas import ServiceCreate, ServiceUpdate, ServiceOut
from app.deps import get_current_user, require_role

router = APIRouter(prefix="/api/services", tags=["Services"])

@router.get("", response_model=List[ServiceOut])
def list_services(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List business services (active services available to all users)."""
    query = db.query(Service)
    if active_only:
        query = query.filter(Service.is_active == True)
    return query.all()

@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db)):
    """Retrieve service details by ID."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    service_in: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Create a new service (Admin only)."""
    existing = db.query(Service).filter(Service.name == service_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Service name already exists")
    
    service = Service(**service_in.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

@router.put("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    service_in: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Update service parameters (Admin only)."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    update_data = service_in.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != service.name:
        existing = db.query(Service).filter(Service.name == update_data["name"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Service name already exists")

    for field, value in update_data.items():
        setattr(service, field, value)
    
    db.commit()
    db.refresh(service)
    return service

@router.delete("/{service_id}", status_code=status.HTTP_200_OK)
def deactivate_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Soft-delete / deactivate service (Admin only)."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service.is_active = False
    db.commit()
    return {"message": f"Service '{service.name}' deactivated successfully"}
