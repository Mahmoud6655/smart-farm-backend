import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db

# الموديلات
from models.users import User
from models.plant import PlantScan
from models.animal import AnimalWeight
from models.crop import CropRecommendation
from models.soil import SoilAnalysis
from models.fruit import FruitQuality
from models.chatbot import ChatHistory
from models.reports import GeneratedReport

# مكتبات الـ PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

router = APIRouter()

@router.post("/generate-pdf")
async def generate_premium_report(
    period: str = Query("all", enum=["weekly", "monthly", "all"]),
    db: Session = Depends(get_db)
):
    # --- المسار اللي قولت عليه ---
    base_dir = os.getcwd() 
    reports_dir = os.path.join(base_dir, "download_reports", "admin_reports")
    logo_path = os.path.join(base_dir, "static", "logo.jpg") 
    os.makedirs(reports_dir, exist_ok=True)
    
    start_date = None
    if period == "weekly": start_date = datetime.now() - timedelta(days=7)
    elif period == "monthly": start_date = datetime.now() - timedelta(days=30)

    # 1. جلب بيانات الموديلات الستة
    def get_c(model):
        q = db.query(model)
        if start_date: q = q.filter(model.created_at >= start_date)
        return q.count()

    models_data = {
        "Plant AI": get_c(PlantScan),
        "Soil AI": get_c(SoilAnalysis),
        "Livestock AI": get_c(AnimalWeight),
        "Fruit AI": get_c(FruitQuality),
        "Crop Smart": get_c(CropRecommendation),
        "Agri-Chatbot": get_c(ChatHistory)
    }

    # عدد المستخدمين اللي في الداتا بيز حالياً
    total_users = db.query(User).count()
    active_now = db.query(PlantScan.user_id).distinct().count()

    # 2. رسم بياني ملون وشكله نظيف
    plt.figure(figsize=(9, 4))
    plt.bar(models_data.keys(), models_data.values(), color=['#2E7D32', '#388E3C', '#43A047', '#4CAF50', '#66BB6A', '#81C784'])
    plt.title("AI Systems Usage Analysis", fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    chart_path = os.path.join(reports_dir, "usage_chart.png")
    plt.savefig(chart_path, bbox_inches='tight')
    plt.close()

    # 3. بناء الـ PDF
    report_name = f"SmartFarm_Strategy_{datetime.now().strftime('%H%M')}.pdf"
    file_path = os.path.join(reports_dir, report_name)
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # ستايلات الألوان
    title_s = ParagraphStyle('T', fontSize=26, textColor=colors.HexColor("#1B5E20"), alignment=1)
    header_s = ParagraphStyle('H', fontSize=15, textColor=colors.HexColor("#2E7D32"), spaceBefore=12)

    # اللوجو من فولدر ستاتيك
    if os.path.exists(logo_path):
        img = Image(logo_path, width=60, height=60)
        img.hAlign = 'RIGHT'
        elements.append(img)

    elements.append(Paragraph("Smart Farm AI: Management Audit", title_s))
    elements.append(Spacer(1, 20))

    # --- جدول ملخص المنصة ---
    elements.append(Paragraph("I. Platform Key Metrics", header_s))
    summary_table = Table([
        ["Metric Description", "Value", "System Status"],
        ["Total Registered Farmers", str(total_users), "Operational"],
        ["Current Active Users", str(active_now), "Stable"]
    ], colWidths=[200, 140, 140])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E8F5E9")),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 8)
    ]))
    elements.append(summary_table)

    # --- الرسم البياني ---
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("II. AI Modules Activity Distribution", header_s))
    elements.append(Image(chart_path, width=480, height=220))

    # --- جدول الموديلات الستة ---
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("III. Core AI Services Performance", header_s))
    mod_data = [["Service Name", "Requests Count", "Deployment Status"]]
    for name, count in models_data.items():
        mod_data.append([name, str(count), "Online"])

    t2 = Table(mod_data, colWidths=[180, 150, 150])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F8E9")])
    ]))
    elements.append(t2)

    doc.build(elements)
    if os.path.exists(chart_path): os.remove(chart_path)

    # حفظ السجل
    new_report = GeneratedReport(name=report_name, report_type="Executive Audit", size=f"{os.path.getsize(file_path)/1024:.1f} KB", file_path=file_path)
    db.add(new_report); db.commit()

    return {
        "status": "success",
        "message": "Strategic report generated and saved successfully.",
        "file_url": f"/download_reports/admin_reports/{report_name}"
    }