#=========== user_summary.py النسخة المؤمنة ================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from datetime import datetime
from models.plant import PlantScan
from models.animal import AnimalWeight
from models.crop import CropRecommendation
from models.soil import SoilAnalysis
from models.fruit import FruitQuality
from models.chatbot import ChatHistory
#--- 🛡️ استدعاء الحارس من ملف الـ auth ---
from auth import check_user_exists 

router = APIRouter()

@router.get("/user-summary/{user_id}")
async def get_user_report_summary(user_id: int, db: Session = Depends(get_db)):
    
    # 🛡️ الحارس: لو الـ ID مش مسجل، هيرفض يكمل ويرمي 404 فوراً
    # بدل ما يروح يلف في الـ 6 جداول على الفاضي
    check_user_exists(user_id, db)

    # دالة مساعدة لجلب تاريخ آخر عملية أو تاريخ اليوم لو مفيش بيانات
    def get_last_date(model):
        last_record = db.query(model).filter(model.user_id == user_id).order_by(desc(model.created_at)).first()
        if last_record and last_record.created_at:
            return last_record.created_at.strftime("%B %d, %Y")
        return datetime.now().strftime("%B %d, %Y")

    # 1. ملخص أمراض النبات
    plant_count = db.query(PlantScan).filter(PlantScan.user_id == user_id).count()
    
    # 2. ملخص الحيوانات والأوزان
    animal_stats = db.query(
        func.count(AnimalWeight.id).label("total"),
        func.avg(AnimalWeight.estimated_weight).label("avg_weight")
    ).filter(AnimalWeight.user_id == user_id).first()

    # 3. ملخص المحاصيل
    crop_count = db.query(CropRecommendation).filter(CropRecommendation.user_id == user_id).count()

    # 4. ملخص تحليل التربة
    soil_count = db.query(SoilAnalysis).filter(SoilAnalysis.user_id == user_id).count()

    # 5. ملخص جودة الفواكه
    fruit_count = db.query(FruitQuality).filter(FruitQuality.user_id == user_id).count()

    # 6. ملخص الشات بوت
    chat_count = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).count()

    return {
        "plant_report": {
            "title": "Plant Disease Analysis Report",
            "stat": f"{plant_count} images analyzed",
            "date": get_last_date(PlantScan),
            "type": "AI Analysis"
        },
        "livestock_report": {
            "title": "Livestock Weight Monitoring",
            "stat": f"{animal_stats.total} animals tracked, avg weight: {int(animal_stats.avg_weight or 0)}kg",
            "date": get_last_date(AnimalWeight),
            "type": "Computer Vision"
        },
        "crop_report": {
            "title": "Crop Recommendation Summary",
            "stat": f"{crop_count} fields analyzed",
            "date": get_last_date(CropRecommendation),
            "type": "Machine Learning"
        },
        "soil_report": {
            "title": "Soil Analysis Report",
            "stat": f"Fertility levels assessed for {soil_count} zones",
            "date": get_last_date(SoilAnalysis),
            "type": "AI Analysis"
        },
        "fruit_report": {
            "title": "Fruit Quality Analysis",
            "stat": f"{fruit_count} fruits analyzed",
            "date": get_last_date(FruitQuality),
            "type": "Image Classification"
        },
        "chatbot_report": {
            "title": "Smart Assistant Activity",
            "stat": f"{chat_count} messages exchanged",
            "date": get_last_date(ChatHistory),
            "type": "NLP Chatbot"
        }
    }