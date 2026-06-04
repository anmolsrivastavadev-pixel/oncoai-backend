from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app import models
from app.api import deps
import os

router = APIRouter()

UPLOAD_DIR = "uploads"

@router.get("/uploads/{filename}")
def get_protected_file(
    filename: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    Serve uploaded images only to authenticated users who own the scan.
    """
    # Check if this file belongs to a scan owned by the user
    scan = db.query(models.Scan).filter(
        models.Scan.filename == filename,
        models.Scan.user_id == current_user.id
    ).first()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or file not found"
        )

    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(file_path)
