from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models.user import User
from ..utils.security import hash_password, create_access_token
from database import get_db

router = APIRouter()

@router.post("/register")
def register_user(email: str, full_name: str, password: str, db: Session = Depends(get_db)):
    hashed_password = hash_password(password)
    new_user = User(email=email, full_name=full_name, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/login")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}