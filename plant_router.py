import random
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.plant import PlantScan 
from datetime import datetime
#--- 🛡️ استدعاء الحارس من ملف الـ auth ---
from auth import check_user_exists 

router = APIRouter()

@router.post("/detect")
async def detect_disease(
    user_id: int = Form(...), 
    image: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # 🛡️ الحارس: لو الـ ID رقم 3 مش موجود في جدول المستخدمين، هيرفض يكمل ويرمي 404
    check_user_exists(user_id, db)

    try:
        # قائمة بالأمراض
        diseases = ["Apple Scab", "Tomato Leaf Mold", "Potato Late Blight", "Corn Rust"]
        
        # منطق النواتج العشوائي
        chance = random.random() 
        
        if chance > 0.5:
            status = "Healthy"
            disease_name = None
            message = "الزرعة سليمة وزي الفل يا حاج."
        else:
            status = "Disease Detected"
            disease_name = random.choice(diseases)
            message = f"للأسف اكتشفنا مرض ({disease_name})."

        # حفظ النتيجة في الداتابيز
        new_scan = PlantScan(
            user_id=user_id,
            status=status,
            disease_name=disease_name,
            confidence=round(random.uniform(85.0, 99.0), 1),
            image_url=f"Photos/{image.filename}"
        )
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)

        return {
            "status": "success",
            "analysis": {
                "condition": status,
                "disease": disease_name,
                "confidence": f"{new_scan.confidence}%",
                "message": message
            }
        }
    except HTTPException:
        # لو الإيرور جاي من الحارس نطلعه زي ما هو
        raise
    except Exception as e:
        if 'db' in locals(): db.rollback()
        raise HTTPException(status_code=500, detail=str(e))