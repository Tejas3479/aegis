from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.auth import create_access_token, pwd_context

router = APIRouter()

# Mock user database for enterprise demonstration
MOCK_USERS = {
    "doctor_smith": {"username": "doctor_smith", "password": pwd_context.hash("aegis2026"), "role": "DOCTOR"},
    "admin_triage": {"username": "admin_triage", "password": pwd_context.hash("adminsecret"), "role": "ADMIN"}
}

@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Enterprise authentication endpoint issuing secure JWT tokens.
    """
    user = MOCK_USERS.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}
