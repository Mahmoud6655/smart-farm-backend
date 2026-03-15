#=========== auth.py النسخة النهائية (بواب ذكي بفرق بين الحذف والعدم) ================

from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
from models.users import User 
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional

# إعدادات التشفير
SECRET_KEY = "my_super_secret_key_99" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b")

router = APIRouter()

# --- 🛡️ دالة الحماية (البواب الذكي المطور) ---
def check_user_exists(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    
    # 1. لو الـ ID مش موجود نهائياً في قاعدة البيانات
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"خطأ: المستخدم رقم ({user_id}) غير مسجل في النظام أصلاً."
        )
    
    # 2. لو اليوزر موجود بس الأدمن غير الرول لـ deleted
    if user.role == "deleted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="عذراً، هذا الحساب تم حذفه أو تعطيله بواسطة الإدارة."
        )
        
    return user

# --- 1. كود التسجيل (Register) ---
@router.post("/register")
def register(
    name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="الايميل مسجل بالفعل")
    
    new_user = User(
        name=name, 
        email=email, 
        password=pwd_context.hash(password), 
        role="farmer"
    )
    db.add(new_user)
    db.commit()
    return {"message": "تم التسجيل بنجاح"}

# --- 2. كود الدخول (Login) ---
@router.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    
    # فحص الحسابات المحذوفة عند الدخول
    if user and user.role == "deleted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="تم تعطيل حسابك. يرجى التواصل مع الإدارة."
        )

    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=400, detail="بيانات الدخول غير صحيحة")
    
    access_token = jwt.encode({"sub": str(user.id)}, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
        "message": f"أهلاً بك يا {user.name}"
    }

# --- 3. تحديث البيانات (يحافظ على القديم لو الخانة فاضية) ---
@router.put("/save-all-settings/{user_id}")
async def save_all_settings(
    user_id: int, 
    full_name: Optional[str] = Form(None), 
    email: Optional[str] = Form(None), 
    phone: Optional[str] = Form(None), 
    db: Session = Depends(get_db)
):
    # التأكد من وجود اليوزر وحالته (بواسطة الحارس المطور)
    user = check_user_exists(user_id, db)

    if full_name and full_name.strip():
        user.name = full_name

    if email and email.strip():
        db_email = db.query(User).filter(User.email == email, User.id != user_id).first()
        if db_email:
            raise HTTPException(status_code=400, detail="الإيميل الجديد مستخدم بالفعل")
        user.email = email

    if phone and phone.strip():
        user.phone_number = phone
    
    try:
        db.commit()
        db.refresh(user)
        return {
            "status": "success", 
            "message": "تم تحديث البيانات بنجاح",
            "data": {"name": user.name, "email": user.email}
        }
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="فشل في حفظ البيانات")

# --- 4. كود الخروج ---
@router.post("/logout/{user_id}")
def logout(user_id: int, db: Session = Depends(get_db)):
    # فحص الحالة للزيادة في التأمين
    user = check_user_exists(user_id, db)
    
    return {
        "status": "success", 
        "message": f"المستخدم {user.name} سجل خروجه بنجاح"
    }