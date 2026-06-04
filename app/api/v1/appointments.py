from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app import models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=schemas.appointment.Appointment)
def create_appointment(
    *,
    db: Session = Depends(get_db),
    appointment_in: schemas.appointment.AppointmentCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    doctor = db.query(models.Doctor).filter(models.Doctor.id == appointment_in.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    db_obj = models.Appointment(
        user_id=current_user.id,
        doctor_id=appointment_in.doctor_id,
        appointment_datetime=appointment_in.appointment_datetime,
        consultation_type=appointment_in.consultation_type,
        notes=appointment_in.notes
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/me", response_model=List[schemas.appointment.Appointment])
def read_my_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    return db.query(models.Appointment).filter(
        models.Appointment.user_id == current_user.id
    ).all()

@router.get("/availability/{doctor_id}")
def get_availability(
    doctor_id: int,
    date: str, # Format: YYYY-MM-DD
    db: Session = Depends(get_db)
) -> Any:
    """
    Fetch available timeslots for a specific doctor on a specific date.
    """
    try:
        search_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    all_slots = []
    # Work day: 9 AM to 5 PM
    current_slot = search_date.replace(hour=9, minute=0, second=0, microsecond=0)
    end_of_day = search_date.replace(hour=17, minute=0, second=0, microsecond=0)

    # Fetch existing appointments for this doctor on this day
    existing_appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.status == "confirmed",
        models.Appointment.appointment_datetime >= search_date,
        models.Appointment.appointment_datetime < search_date + timedelta(days=1)
    ).all()

    booked_times = [appt.appointment_datetime for appt in existing_appointments]

    while current_slot < end_of_day:
        # Check if slot is booked (allowing 30 min slots)
        is_booked = any(
            current_slot <= bt < current_slot + timedelta(minutes=30) 
            for bt in booked_times
        )
        
        all_slots.append({
            "time": current_slot.strftime("%H:%M"),
            "datetime": current_slot.isoformat(),
            "available": not is_booked
        })
        current_slot += timedelta(minutes=30)

    return all_slots

@router.delete("/{appointment_id}")
def cancel_appointment(
    *,
    db: Session = Depends(get_db),
    appointment_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.user_id == current_user.id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    appointment.status = "cancelled"
    db.commit()
    return {"message": "Appointment cancelled successfully"}
