import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from models.users import User
from models.plant import PlantScan
from models.animal import AnimalWeight
from models.crop import CropRecommendation
from models.soil import SoilAnalysis
from models.fruit import FruitQuality
from models.chatbot import ChatHistory
from datetime import datetime, timedelta

# استيراد المصدر الموحد للبيانات
from admin.system_management import services_db 

router = APIRouter()

@router.get("/stats")
async def get_admin_dashboard_stats(db: Session = Depends(get_db)):
    # 1. جلب الأعداد الإجمالية لكل خدمة (مع حماية ضد الجداول غير الموجودة)
    try:
        counts = {
            "Plant Disease": db.query(PlantScan).count(),
            "Animal Weight": db.query(AnimalWeight).count(),
            "Crop AI": db.query(CropRecommendation).count(),
            "Soil Analysis": db.query(SoilAnalysis).count(),
            "Fruit Quality": db.query(FruitQuality).count(),
            "Chatbot": db.query(ChatHistory).count()
        }
    except Exception as e:
        # لو في جدول لسه مش موجود في الداتابيز هيحط مكانه 0 عشان السيستم ميفصلش
        counts = {"Error": 0}

    # المستخدمين الفعليين (غير المحذوفين)
    total_users = db.query(User).filter(User.role != "deleted").count()
    
    # إجمالي الطلبات الكلي
    total_all_reqs = sum(counts.values())
    # التحاليل العلمية (بدون الشات بوت)
    total_scientific = total_all_reqs - counts.get("Chatbot", 0)

    # 2. عدد الخدمات الـ Online
    active_services_count = sum(1 for s in services_db.values() if s["status"] == "online")
    
    # 3. الخدمة الأكثر استخداماً
    top_service_name = max(counts, key=counts.get) if total_all_reqs > 0 else "None"

    # 4. توزيع الخدمات للـ Pie Chart
    distribution = {
        k: round((v / total_all_reqs * 100), 1) if total_all_reqs > 0 else 0 
        for k, v in counts.items()
    }

    # 5. النشاط الأسبوعي (تعديل الأيام ليكون ديناميكي تماماً)
    today = datetime.now().date()
    week_activity = {}
    all_models = [PlantScan, AnimalWeight, CropRecommendation, SoilAnalysis, FruitQuality, ChatHistory]

    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        day_name = target_date.strftime('%a')
        
        daily_total = 0
        for model in all_models:
            try:
                daily_total += db.query(model).filter(func.date(model.created_at) == target_date).count()
            except:
                continue # لو جدول ملوش عمود تاريخ يتخطاه
        
        week_activity[day_name] = daily_total

    # 6. جلب "آخر النشاطات" (حل مشكلة عدم ظهور بعض الموديلات)
    all_activities = []

    def fetch_recent(model, action_name):
        try:
            # بنجيب آخر 5 سجلات من الموديل
            records = db.query(model).order_by(desc(model.created_at)).limit(5).all()
            for record in records:
                # محاولة جلب اليوزر
                user = db.query(User).filter(User.id == record.user_id).first()
                
                # لو اليوزر محذوف مش هنعرض النشاط
                if user and user.role == "deleted":
                    continue
                
                user_name = user.name if user else "Guest"
                
                all_activities.append({
                    "user": user_name,
                    "action": action_name,
                    "time": record.created_at.strftime("%Y-%m-%d %H:%M")
                })
        except Exception as e:
            # لو في موديل فشل (مثلاً معندوش عمود created_at) مش هيوقف الباقي
            print(f"Error fetching recent for {action_name}: {e}")

    # تنفيذ الجلب لكل الموديلات
    fetch_recent(PlantScan, "Scanned a Plant")
    fetch_recent(AnimalWeight, "Measured Animal")
    fetch_recent(CropRecommendation, "Requested Crop AI")
    fetch_recent(SoilAnalysis, "Analyzed Soil")
    fetch_recent(FruitQuality, "Checked Fruit")
    fetch_recent(ChatHistory, "Talked to AI")

    # ترتيب نهائي لكل الأنشطة عشان الأحدث يظهر فوق
    final_recent_activity = sorted(all_activities, key=lambda x: x['time'], reverse=True)[:5]

    return {
        "summary": {
            "total_users": total_users,
            "total_analyses": total_scientific, 
            "total_requests": total_all_reqs,    
            "active_services": f"{active_services_count} of 6",
            "top_service": top_service_name 
        },
        "charts": {
            "service_distribution": distribution,
            "active_users_week": week_activity
        },
        "recent_activity": final_recent_activity
    }