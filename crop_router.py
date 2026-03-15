from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.crop import CropRecommendation 
from enum import Enum 
from datetime import datetime
#--- 🛡️ استدعاء الحارس من ملف الـ auth ---
from auth import check_user_exists 

router = APIRouter()

# --- 1. دالة المحاكاة المنطقية ---
def get_mock_recommendation(temp, hum, rain):
    if temp >= 28 and rain >= 150:
        return ["rice", "papaya", "coconut"]
    elif temp >= 25:
        return ["maize", "cotton", "jute"]
    elif temp <= 20:
        return ["wheat", "lentil", "chickpea"]
    else:
        return ["maize", "orange", "pomegranate"]

# --- 2. تعريف أنواع التربة ---
class SoilType(str, Enum):
    clay = "Clay"
    sandy = "Sandy"
    loamy = "Loamy"

# --- 3. الـ API Endpoint المعدل ---
@router.post("/recommend-crop")
async def recommend_crop(
    user_id: int = Form(...),
    temperature: float = Form(..., description="درجة الحرارة مئوية"), 
    humidity: float = Form(..., description="نسبة الرطوبة %"),
    rainfall: float = Form(..., description="كمية الأمطار mm"),
    soil: SoilType = Form(...),
    db: Session = Depends(get_db)
):
    # 🛡️ الحارس: لو الـ ID رقم 3 مش مسجل، هيرمي 404 فوراً قبل ما يحسب أي حاجة
    check_user_exists(user_id, db)

    # جلب التوصية فوراً
    recommended_list = get_mock_recommendation(temperature, humidity, rainfall)
    primary_crop = recommended_list[0]
    alternatives = recommended_list[1:]
    
    current_month = datetime.now().month
    description = f"توصية بناءً على المدخلات اليدوية: عند حرارة {temperature}°C، الأنسب هو {primary_crop}."

    # حفظ السجل في قاعدة البيانات
    try:
        new_rec = CropRecommendation(
            user_id=user_id,
            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,
            soil_type=soil.value,
            growing_month=current_month,
            recommended_crop=primary_crop,
            expected_yield="High",
            recommendation_desc=description
        )
        db.add(new_rec)
        db.commit()
        db.refresh(new_rec)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database Error: {str(e)}")

    # الرد النهائي
    return {
        "id": new_rec.id,
        "status": "Success",
        "inputs": {
            "temperature": f"{temperature}°C",
            "humidity": f"{humidity}%",
            "rainfall": f"{rainfall}mm",
            "soil_type": soil.value
        },
        "recommendations": {
            "primary": primary_crop,
            "alternatives": alternatives
        },
        "description": description
    }