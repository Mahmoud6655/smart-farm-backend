from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.users import User
from sqlalchemy import func
from datetime import datetime

router = APIRouter()

# 1. عرض ملخص وإحصائيات المستخدمين (مضاف إليها تاريخ الانضمام)
@router.get("/summary-and-list")
async def get_user_management_data(db: Session = Depends(get_db)):
    # جلب المستخدمين غير المحذوفين فقط (النشطين والمعطلين)
    base_query = db.query(User).filter(User.role != "deleted")
    
    total_users = base_query.count()
    
    # حساب المستخدمين النشطين (farmer و admin)
    active_users_count = base_query.filter(User.role.in_(["farmer", "admin"])).count()
    
    # حساب المديرين فقط
    admins_count = base_query.filter(User.role == "admin").count()
    
    # المستخدمين غير النشطين (inactive)
    inactive_users = base_query.filter(User.role == "inactive").count()

    # جلب القائمة للجدول (بدون المحذوفين)
    all_users = base_query.all()
    user_list = []
    for u in all_users:
        # تنسيق التاريخ ليظهر بشكل: Jan 15, 2024
        # ملاحظة: تأكد أن اسم الحقل في موديل User هو created_at
        joined_date = "N/A"
        if hasattr(u, 'created_at') and u.created_at:
            joined_date = u.created_at.strftime("%b %d, %Y")

        user_list.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.capitalize() if u.role else "Unknown",
            "status": "Active" if u.role in ["farmer", "admin"] else "Inactive",
            "joined": joined_date  # الحقل الجديد اللي طلبته
        })

    return {
        "stats": {
            "total_users": total_users,
            "active_users": active_users_count,
            "inactive_users": inactive_users,
            "admins": admins_count
        },
        "users": user_list
    }

# 2. وظيفة البحث (Search) - مضاف إليها تنسيق التاريخ أيضاً
@router.get("/search")
async def search_users(query: str, db: Session = Depends(get_db)):
    users = db.query(User).filter(
        User.role != "deleted",
        (User.name.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%"))
    ).all()
    
    # تنسيق النتائج لإرجاع التاريخ في البحث أيضاً إذا لزم الأمر
    formatted_users = []
    for u in users:
        joined_date = u.created_at.strftime("%b %d, %Y") if hasattr(u, 'created_at') and u.created_at else "N/A"
        formatted_users.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "joined": joined_date
        })
    return formatted_users

# 3. حذف مزارع (Soft Delete)
@router.delete("/delete/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    try:
        user.role = "deleted"
        db.commit()
        return {"status": "success", "message": "تم حذف المستخدم من النظام بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 4. تعطيل حساب مزارع (Deactivate)
@router.patch("/deactivate/{user_id}")
async def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    try:
        user.role = "inactive"
        db.commit()
        return {"status": "success", "message": "تم تعطيل الحساب بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 5. إعادة تفعيل حساب مزارع (Activate)
@router.patch("/activate/{user_id}")
async def activate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    try:
        user.role = "farmer"
        db.commit()
        return {"status": "success", "message": "تم إعادة تفعيل الحساب بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))