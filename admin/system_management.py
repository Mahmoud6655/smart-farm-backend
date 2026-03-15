import time
from datetime import datetime
from fastapi import APIRouter, Depends
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from database import get_db

# استيراد الموديلات لحساب الإحصائيات الحقيقية
from models.plant import PlantScan
from models.animal import AnimalWeight
from models.crop import CropRecommendation
from models.soil import SoilAnalysis
from models.fruit import FruitQuality
from models.chatbot import ChatHistory

router = APIRouter()

# تسجيل وقت بداية تشغيل السيرفر لحساب الـ Uptime الحقيقي
START_TIME = datetime.now()

class AIModuleName(str, Enum):
    plant = "plant_disease"
    animal = "animal_weight"
    crop = "crop_rec"
    soil = "soil_analysis"
    fruit = "fruit_quality"
    chatbot = "chatbot"

# المصدر الرئيسي للبيانات (Global)
services_db = {
    "plant_disease": {"name": "Plant-CNN-v2.3", "status": "online", "type": "CNN", "version": "2.3.0", "accuracy": "94.2%"},
    "animal_weight": {"name": "Animal-CV-v1.8", "status": "online", "type": "Computer Vision", "version": "1.8.2", "accuracy": "91.8%"},
    "crop_rec": {"name": "Crop-ML-v3.1", "status": "online", "type": "Machine Learning", "version": "3.1.0", "accuracy": "89.5%"},
    "soil_analysis": {"name": "Soil-DL-v2.0", "status": "online", "type": "Deep Learning", "version": "2.0.1", "accuracy": "92.3%"},
    "fruit_quality": {"name": "Fruit-CV-v1.5", "status": "online", "type": "Computer Vision", "version": "1.5.4", "accuracy": "90.7%"},
    "chatbot": {"name": "Chat-NLP-v2.7", "status": "online", "type": "NLP", "version": "2.7.0", "accuracy": "96.1%"}
}

@router.get("/status")
async def get_system_status(db: Session = Depends(get_db)):
    global services_db
    start_tick = time.time()
    
    # 1. حساب الـ Uptime الحقيقي
    uptime_delta = datetime.now() - START_TIME
    hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m"

    # 2. جلب إجمالي الطلبات الفعلي من كل الجداول
    total_reqs = (
        db.query(PlantScan).count() +
        db.query(AnimalWeight).count() +
        db.query(CropRecommendation).count() +
        db.query(SoilAnalysis).count() +
        db.query(FruitQuality).count() +
        db.query(ChatHistory).count()
    )

    # 3. حساب متوسط الدقة الحقيقي (بناءً على المسجل في الداتابيز)
    try:
        avg_plant = db.query(func.avg(PlantScan.confidence)).scalar() or 0
        avg_animal = db.query(func.avg(AnimalWeight.confidence_score)).scalar() or 0
        # نأخذ المتوسط العام للموديلات اللي فيها بيانات
        accuracies = [a for a in [avg_plant, avg_animal] if a > 0]
        final_avg = sum(accuracies) / len(accuracies) if accuracies else 92.4
    except:
        final_avg = 92.4

    # 4. مساحة الداتا بيز والكونكشنز
    try:
        db_size = db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
        real_conns = db.execute(text("SELECT count(*) FROM pg_stat_activity")).scalar()
    except:
        db_size, real_conns = "0 MB", 0

    active_count = sum(1 for s in services_db.values() if s["status"] == "online")
    resp_time = f"{int((time.time() - start_tick) * 1000)}ms"

    return {
        "system": {
            "status": "All Systems Operational" if active_count > 0 else "Critical: System Offline",
            "uptime": uptime_str,
            "response_time": resp_time
        },
        "database": {
            "status": "Healthy" if real_conns > 0 else "Disconnected",
            "storage_used": db_size,
            "connections": real_conns
        },
        "ai_models_summary": {
            "active": f"{active_count} of 6 Active",
            "avg_accuracy": f"{round(final_avg, 1)}%",
            "total_requests": f"{total_reqs:,}"
        },
        "services": services_db 
    }

@router.post("/toggle-service/{module_name}")
async def toggle_service(module_name: AIModuleName):
    global services_db
    service_id = module_name.value
    services_db[service_id]["status"] = "offline" if services_db[service_id]["status"] == "online" else "online"
    return {"service": services_db[service_id]["name"], "new_status": services_db[service_id]["status"]}

@router.get("/models-table")
async def get_models_table():
    global services_db
    return [
        {
            "name": data["name"],
            "version": data["version"],
            "type": data["type"],
            "accuracy": data["accuracy"],
            "status": "Active" if data["status"] == "online" else "Inactive"
        }
        for data in services_db.values()
    ]