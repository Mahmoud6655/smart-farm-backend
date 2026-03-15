import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from database import engine, Base
from models import users, plant, animal, crop, soil, fruit, chatbot
from models.reports import GeneratedReport
from fastapi.staticfiles import StaticFiles
from admin import dashboard, user_management, system_management, system_reports
import farmer_reports

import auth
import plant_router 
import animal_router
import crop_router
import soil_router
import fruit_router
import chatbot_router
import reports_router # 1. استيراد راوتر التقارير الجديد

# إنشاء الجداول في الداتابيز (تأكد من تحديث pgAdmin)
Base.metadata.create_all(bind=engine)

# التأكد من وجود فولدر الرفع عشان الصور متضيعش
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

app = FastAPI(
    title="Smart Farm AI System",
    description="Backend API for all farming modules including AI analysis and reporting"
)

# ربط الـ Routers بالترتيب حسب المنيو في Figma
app.include_router(auth.router, tags=["Authentication"])

# قسم أمراض النبات
app.include_router(plant_router.router, prefix="/plants", tags=["Plant Disease Detection"])

# قسم أوزان الحيوانات
app.include_router(animal_router.router, prefix="/animals", tags=["Animal Weight Estimation"])

# قسم توصيات المحاصيل
app.include_router(crop_router.router, prefix="/crops", tags=["Crop Recommendation"])

# قسم تحليل التربة
app.include_router(soil_router.router, prefix="/soil", tags=["Soil Type Analysis"])

# قسم جودة الفاكهة
app.include_router(fruit_router.router, prefix="/fruits", tags=["Fruit Quality Analysis"])

# قسم الشات بوت (الوحش بذاكرته الحالية)
app.include_router(chatbot_router.router, prefix="/chatbot", tags=["Smart Farm Chatbot (NLP)"])

# 2. إضافة قسم التقارير النهائي
app.include_router(reports_router.router, prefix="/reports", tags=["Reports System"])

app.include_router(dashboard.router, prefix="/admin/dashboard", tags=["Admin: Dashboard"])
app.include_router(user_management.router, prefix="/admin/users", tags=["Admin: User Management"])
app.include_router(system_management.router, prefix="/admin/system", tags=["Admin: System Management"])
app.include_router(system_reports.router, prefix="/admin/reports", tags=["Admin: System Reports"])
app.mount("/download_reports", StaticFiles(directory="download_reports"), name="download_reports")
app.include_router(farmer_reports.router, prefix="/farmer_reports", tags=["Farmer Reports"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ده بيخلي أي موبايل أو موقع يكلم الباك إند بتاعك
    allow_credentials=True,
    allow_methods=["*"],  # بيسمح بكل العمليات (GET, POST, etc.)
    allow_headers=["*"],  # بيسمح بكل أنواع الـ Headers
)

@app.get("/")
def home():
    return {"message": "Smart Farm API is Running Successfully!"}


    