from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Customer, Service, Booking, Invoice, BackupRecord, RecoveryEvent
from app.schemas import (
    SystemStatusResponse, BackupRecordCreate, BackupRecordOut,
    RecoveryEventCreate, RecoveryEventOut
)
from app.config import settings

router = APIRouter(tags=["System & Operations"])

@router.get("/api/status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    """System and recovery operational status dashboard."""
    users_count = db.query(User).count()
    customers_count = db.query(Customer).count()
    services_count = db.query(Service).count()
    bookings_count = db.query(Booking).count()
    invoices_count = db.query(Invoice).count()

    latest_backup = db.query(BackupRecord).order_by(BackupRecord.timestamp.desc()).first()
    recent_events = db.query(RecoveryEvent).order_by(RecoveryEvent.timestamp.desc()).limit(10).all()

    return {
        "status": "operational",
        "app_version": settings.APP_VERSION,
        "uptime_status": "healthy",
        "total_users": users_count,
        "total_customers": customers_count,
        "total_services": services_count,
        "total_bookings": bookings_count,
        "total_invoices": invoices_count,
        "latest_backup": latest_backup,
        "recent_recovery_events": recent_events
    }

@router.get("/api/ops/backups", response_model=List[BackupRecordOut])
def list_backup_records(db: Session = Depends(get_db)):
    """List historical database backups and verification statuses."""
    return db.query(BackupRecord).order_by(BackupRecord.timestamp.desc()).all()

@router.post("/api/ops/backups", response_model=BackupRecordOut, status_code=status.HTTP_201_CREATED)
def record_backup(backup_in: BackupRecordCreate, db: Session = Depends(get_db)):
    """Register an executed database backup into the audit log."""
    record = BackupRecord(**backup_in.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/api/ops/recovery-events", response_model=List[RecoveryEventOut])
def list_recovery_events(db: Session = Depends(get_db)):
    """Audit log of all detected failures, drift repairs, and disaster recovery runs."""
    return db.query(RecoveryEvent).order_by(RecoveryEvent.timestamp.desc()).all()

@router.post("/api/ops/recovery-events", response_model=RecoveryEventOut, status_code=status.HTTP_201_CREATED)
def record_recovery_event(event_in: RecoveryEventCreate, db: Session = Depends(get_db)):
    """Register a self-healing or disaster recovery event."""
    event = RecoveryEvent(**event_in.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
