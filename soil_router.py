from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from database import get_db
# تأكد إنك شلت الـ # من السطر اللي تحت ده عشان الكود يشوف الموديل
from models.soil import SoilAnalysis 
#--- 🛡️ استدعاء الحارس من ملف الـ auth ---
from auth import check_user_exists 

router = APIRouter()

# دي حالة الخدمة
services_db = {"soil_analysis": {"status": "online"}}

@router.post("/analyze-soil")
async def analyze_soil(
    user_id: int = Form(...),
    ph: float = Form(...),
    moisture: float = Form(...),
    n: float = Form(...),
    p: float = Form(...),
    k: float = Form(...),
    db: Session = Depends(get_db)
):
    # 🛡️ الحارس: لو الـ ID مش موجود في الداتابيز، هيرمي 404 فوراً ويقفل العملية
    check_user_exists(user_id, db)

    # 1. فحص هل الخدمة شغالة
    if services_db["soil_analysis"]["status"] == "offline":
        raise HTTPException(status_code=503, detail="Soil Analysis AI is offline.")

    # 2. منطق الذكاء الاصطناعي (تحديد النوع بناءً على الأرقام)
    if n < 30:
        predicted_soil = "Sandy"
        fertility = "Low"
    elif n >= 30 and ph < 7:
        predicted_soil = "Clay"
        fertility = "High"
    else:
        predicted_soil = "Loamy"
        fertility = "Medium"

    # 3. حفظ النتيجة في الداتابيز
    try:
        new_analysis = SoilAnalysis(
            user_id=user_id,
            ph_level=ph,
            moisture=moisture,   
            nitrogen=n,
            phosphorus=p,
            potassium=k,
            detected_soil_type=predicted_soil,
            fertility_level=fertility
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
    except Exception as e:
        db.rollback()
        print(f"DATABASE ERROR: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"Database Error: {str(e)}"
        )

    # 4. الرد النهائي
    return {
        "analysis_id": new_analysis.id,
        "result": {
            "detected_soil_type": predicted_soil,
            "fertility_level": fertility,
            "message": f"Based on your soil's NPK ({n}, {p}, {k}), it is classified as {predicted_soil}."
        }
    }