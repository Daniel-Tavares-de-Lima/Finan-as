from fastapi import APIRouter, HTTPException, status

from app.database import check_database_connection

router = APIRouter()


@router.get("/health")
def health():
    ok = check_database_connection()
    if not ok:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"status": "error", "database": "disconnected"})
    return {"status": "ok", "database": "connected"}
