import os
import io
import numpy as np
import random
from PIL import Image
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.fruit import FruitQuality
#--- 🛡️ استدعاء الحارس من ملف الـ auth ---
from auth import check_user_exists 

router = APIRouter()

# القائمة المسموح بها عشان "نمثل" إننا بنفهم نوع الفاكهة
ALLOWED_FRUITS = [
    'Apple', 'Banana', 'Orange', 'Lemon', 'Strawberry', 
    'Pineapple', 'Pomegranate', 'Pepper', 'Watermelon'
]

@router.post("/analyze-fruit")
async def analyze_fruit(
    user_id: int = Form(...), 
    image: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # 🛡️ الحارس: لو الـ ID مش موجود في جدول المستخدمين، هيرمي 404 ويقفل العملية
    check_user_exists(user_id, db)

    try:
        # قراءة الصورة 
        contents = await image.read()
        
        # --- منطق النواتج ---
        chance = random.random()
        detected_fruit = random.choice(ALLOWED_FRUITS)
        
        defects_list = ["خدوش بسيطة في القشرة", "تبقعات بنية خفيفة", "كدمات بسبب النقل", "لا يوجد عيوب"]

        if chance > 0.60:
            quality, status, ripeness, defects = "Grade A", "طازجة وممتازة", "Perfectly Ripe", "لا يوجد عيوب (الثمرة ممتازة)"
        elif chance > 0.30:
            quality, status, ripeness, defects = "Grade B", "جودة متوسطة", "Ripe", random.choice(defects_list[:3])
        else:
            quality, status, ripeness, defects = "Grade C", "تالفة أو غير صالحة", "Overripe", "يوجد آثار تلف واضحة"

        # حفظ الصورة في السيرفر
        os.makedirs("static/Photos", exist_ok=True)
        file_path = f"static/Photos/{image.filename}"
        with open(file_path, "wb") as f:
            f.write(contents)

        # حفظ البيانات في الداتابيز 
        new_scan = FruitQuality(
            user_id=user_id,
            image_url=file_path,
            quality_grade=quality,
            market_status=status,
            ripeness_level=ripeness,
            defect_details=defects
        )
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)

        # الرد اللي هيظهر في الـ Swagger
        return {
            "status": "success",
            "detected_fruit": detected_fruit,
            "quality_grade": quality,
            "market_status": status,
            "ripeness": ripeness,
            "defects": defects
        }

    except HTTPException:
        # لو الإيرور جاي من الحارس نطلعه زي ما هو
        raise
    except Exception as e:
        if 'db' in locals(): db.rollback()
        raise HTTPException(status_code=500, detail="حدث خطأ في النظام")