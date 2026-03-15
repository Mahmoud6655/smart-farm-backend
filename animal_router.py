import random
import cv2
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

# الاستدعاءات الخاصة بقاعدة البيانات
from database import get_db
from models.animal import AnimalWeight
#--- استدعاء الحارس من ملف الـ auth ---
from auth import check_user_exists 

router = APIRouter()

# 1. قاموس الترجمة المدمج
ANIMALS_DICT_AR = {
    "cow": "بقرة",
    "horse": "حصان",
    "zebra": "حمار وحشي",
    "giraffe": "زرافة",
    "elephant": "فيل",
    "sheep": "خروف",
    "goat": "ماعز",
    "pig": "خنزير",
    "dog": "كلب",
    "cat": "قطة",
    "bird": "طائر"
}

@router.post("/estimate-weight")
async def estimate_weight(
    user_id: int = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 🛡️ الحارس: لو الـ ID مش موجود، ارفض فوراً
    check_user_exists(user_id, db)

    # 🚀 الضربة القاضية للبطء: 
    # بنعمل import للمكتبة والموديل "جوه" الدالة فقط
    # كدة السيرفر هيفتح في لمح البصر لأنه مش هيحمل YOLO غير لما ترفع صورة
    from ultralytics import YOLO 
    model = YOLO('yolov8n.pt') 

    try:
        # 3. معالجة الصورة وتثبيت المقاس
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="الصورة غير صالحة")
            
        img_resized = cv2.resize(img, (640, 640))
        total_area = 640 * 640

        # 4. تشغيل الموديل
        results = model(img_resized)
        
        if not results or len(results[0].boxes) == 0:
            raise HTTPException(status_code=400, detail="لم يتم اكتشاف أي كائن")

        box = results[0].boxes[0]
        detected_name_en = model.names[int(box.cls)]
        confidence = float(box.conf) * 100

        # 5. الفلتر والمعاملات
        allowed_animals = {
            "cow": 650, "horse": 550, "zebra": 350, "giraffe": 1000, 
            "elephant": 2500, "sheep": 100, "goat": 80, "pig": 120, 
            "dog": 40, "cat": 6, "bird": 5
        }

        if detected_name_en not in allowed_animals:
            return {
                "status": "Rejected",
                "message": f"عذراً، الكائن ({detected_name_en}) غير مدعوم.",
                "detected_object": detected_name_en
            }

        detected_name_ar = ANIMALS_DICT_AR.get(detected_name_en, detected_name_en)

        # 7. حساب الوزن
        coords = box.xyxy[0].tolist() 
        box_area = (coords[2] - coords[0]) * (coords[3] - coords[1])
        area_ratio = box_area / total_area
        
        current_factor = allowed_animals[detected_name_en]
        raw_weight = (np.sqrt(area_ratio) * current_factor) + (current_factor * 0.1)
        
        calculated_weight = float(round(raw_weight / 5) * 5) if raw_weight > 10 else float(round(raw_weight, 2))

        # 8. حفظ في الداتابيز
        new_entry = AnimalWeight(
            user_id=user_id,
            estimated_weight=calculated_weight,
            animal_type=detected_name_ar, 
            confidence_score=round(confidence, 1),
            image_url=f"Photos/{image.filename}"
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        # 8. الرد النهائي (تأكد إن "confidence" موجود هنا)
        return {
            "id": new_entry.id,
            "animal_name_ar": detected_name_ar,
            "animal_name_en": detected_name_en,
            "confidence": f"{round(confidence, 1)}%", # السطر ده اللي كان ناقصك
            "estimated_weight": f"{calculated_weight} kg",
            "status": "Success"
        }

    except Exception as e:
        if 'db' in locals(): db.rollback()
        raise HTTPException(status_code=400, detail=str(e))