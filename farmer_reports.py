import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db

# مكتبات دعم اللغة العربية
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# استيراد الموديلات
from models.plant import PlantScan
from models.animal import AnimalWeight
from models.crop import CropRecommendation
from models.soil import SoilAnalysis
from models.fruit import FruitQuality
from models.reports import GeneratedReport

# مكتبات الـ PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

router = APIRouter()

# --- دالة إصلاح اللغة العربية ---
def ar(text):
    if not text: return ""
    return get_display(reshape(str(text)))

# تسجيل الخط العربي
try:
    font_path = "arial.ttf" 
    pdfmetrics.registerFont(TTFont('Arabic', font_path))
except:
    print("Warning: arial.ttf not found.")

@router.get("/stats/{user_id}")
async def get_farmer_stats(user_id: int, db: Session = Depends(get_db)):
    total_pdfs = db.query(GeneratedReport).filter(GeneratedReport.user_id == user_id).count()
    stats = {
        "Plants": db.query(PlantScan).filter(PlantScan.user_id == user_id).count(),
        "Animals": db.query(AnimalWeight).filter(AnimalWeight.user_id == user_id).count(),
        "Crops": db.query(CropRecommendation).filter(CropRecommendation.user_id == user_id).count(),
        "Soil": db.query(SoilAnalysis).filter(SoilAnalysis.user_id == user_id).count(),
        "Fruit": db.query(FruitQuality).filter(FruitQuality.user_id == user_id).count()
    }
    return {"top_cards": {"total_reports": total_pdfs, "growth": "+25%"}, "services_summary": stats}

@router.post("/generate/{user_id}")
async def generate_farmer_pdf(
    user_id: int, 
    period: str = Query("all", enum=["weekly", "monthly", "all"]), 
    db: Session = Depends(get_db)
):
    base_dir = os.path.dirname(os.path.abspath(__file__)) 
    reports_dir = os.path.join(base_dir, "download_reports", "farmer_reports")
    
    # تأكد من أن الصورة logo.JPG موجودة داخل مجلد static بجانب ملف الكود
    logo_path = os.path.join(base_dir, "static", "logo.JPG") 
    
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir, exist_ok=True)

    start_date = None
    period_label = "الشامل"
    if period == "weekly":
        start_date = datetime.now() - timedelta(days=7)
        period_label = "الأسبوعي"
    elif period == "monthly":
        start_date = datetime.now() - timedelta(days=30)
        period_label = "الشهري"

    report_name = f"Farmer_Report_ID_{user_id}_{period}.pdf"
    file_path = os.path.join(reports_dir, report_name)

    def get_data(model):
        query = db.query(model).filter(model.user_id == user_id)
        if start_date:
            query = query.filter(model.created_at >= start_date)
        return query.order_by(desc(model.created_at)).all()

    animal_h = get_data(AnimalWeight)
    plant_h = get_data(PlantScan)
    soil_h = get_data(SoilAnalysis)
    crop_h = get_data(CropRecommendation)
    fruit_h = get_data(FruitQuality)

    counts = {
        ar("نبات"): len(plant_h),
        ar("حيوان"): len(animal_h),
        ar("تربة"): len(soil_h),
        ar("محاصيل"): len(crop_h),
        ar("فاكهة"): len(fruit_h)
    }

    plt.figure(figsize=(7, 4))
    plt.bar(counts.keys(), counts.values(), color='#2E7D32')
    plt.title(f"Farm Activity - {period.capitalize()}")
    chart_path = os.path.join(reports_dir, f"temp_{user_id}.png")
    plt.savefig(chart_path)
    plt.close()

    try:
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        elements = []
        
        # --- الجزء الجديد: إضافة اللوجو في أعلى الصفحة ---
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=70, height=70)
            logo.hAlign = 'RIGHT' # محاذاة لليمين
            elements.append(logo)
            elements.append(Spacer(1, 10))
        # ---------------------------------------------

        styles = getSampleStyleSheet()
        styles['Title'].fontName = 'Arabic'
        styles['Heading2'].fontName = 'Arabic'
        styles['Normal'].fontName = 'Arabic'
        styles['Title'].alignment = 1
        styles['Heading2'].alignment = 2

        full_title = f"تقرير المزرعة الذكي - السجل {period_label}"
        elements.append(Paragraph(ar(full_title), styles['Title']))
        
        info_text = f"Farmer ID: {user_id}<br/>Date / Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        elements.append(Paragraph(info_text, styles['Normal']))
        
        elements.append(Spacer(1, 10))
        elements.append(Image(chart_path, width=400, height=220))
        elements.append(Spacer(1, 15))

        def get_thumbnail(img_path):
            if not img_path: return ar("بدون صورة")
            clean_p = img_path.replace("\\", "/").strip("/")
            paths_to_try = [
                os.path.join(base_dir, clean_p),
                os.path.join(base_dir, "static", clean_p.replace("static/", "")),
                os.path.join(base_dir, "static", "uploads", clean_p.split("/")[-1])
            ]
            for path in paths_to_try:
                if os.path.exists(path):
                    return Image(path, width=45, height=45)
            return ar("غير موجودة")

        # 1. سجل الماشية
        elements.append(Paragraph(ar("1. سجل الماشية المصور"), styles['Heading2']))
        a_data = [[ar("الصورة"), ar("النوع"), ar("الوزن"), ar("التاريخ")]]
        for a in animal_h[:5]:
            a_data.append([get_thumbnail(a.image_url), ar(a.animal_type), f"{a.estimated_weight}kg", a.created_at.strftime("%m-%d %H:%M")])
        t1 = Table(a_data, colWidths=[60, 150, 120, 100]); t1.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#2E7D32")),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),'Arabic'),('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('GRID',(0,0),(-1,-1),1,colors.grey)]))
        elements.append(t1)

        # 2. سجل التربة
        elements.append(Paragraph(ar("2. سجل تحليل التربة التفصيلي"), styles['Heading2']))
        s_data = [[ar("الخصوبة"), ar("النوع المكتشف"), "pH", ar("قيم N-P-K"), ar("التاريخ")]]
        for s in soil_h[:5]: 
            npk = f"(N:{int(s.nitrogen)}) (P:{int(s.phosphorus)}) (K:{int(s.potassium)})"
            s_data.append([ar(s.fertility_level), ar(s.detected_soil_type), str(s.ph_level), npk, s.created_at.strftime("%m-%d %H:%M")])
        t2 = Table(s_data, colWidths=[80, 100, 40, 150, 100]); t2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#795548")),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),'Arabic'),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),1,colors.grey)]))
        elements.append(t2)

        # 3. توصيات المحاصيل
        elements.append(Paragraph(ar("3. سجل توصيات المحاصيل"), styles['Heading2']))
        c_data = [[ar("المحصول"), ar("الإنتاج"), ar("الطقس"), ar("التربة"), ar("التاريخ")]]
        for c in crop_h[:5]: 
            thr = f"T:{int(c.temperature)} H:{int(c.humidity)} R:{int(c.rainfall)}"
            c_data.append([ar(c.recommended_crop), ar(c.expected_yield), thr, ar(c.soil_type), c.created_at.strftime("%m-%d %H:%M")])
        t3 = Table(c_data, colWidths=[90, 70, 140, 80, 100]); t3.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#388E3C")),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),'Arabic'),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),1,colors.grey),('FONTSIZE',(0,0),(-1,-1),8)]))
        elements.append(t3)

        # 4. سجل أمراض النبات
        elements.append(Paragraph(ar("4. سجل أمراض النبات"), styles['Heading2']))
        p_data = [[ar("الصورة"), ar("المرض"), ar("التأكد"), ar("التاريخ")]]
        for p in plant_h[:5]:
            p_data.append([get_thumbnail(p.image_url), ar(p.disease_name or "سليم"), f"{p.confidence}%", p.created_at.strftime("%m-%d %H:%M")])
        t4 = Table(p_data, colWidths=[60, 170, 100, 100]); t4.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1976D2")),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),'Arabic'),('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('GRID',(0,0),(-1,-1),1,colors.grey)]))
        elements.append(t4)

        # 5. سجل جودة الفاكهة
        elements.append(Paragraph(ar("5. سجل جودة الفاكهة"), styles['Heading2']))
        f_data = [[ar("الصورة"), ar("الدرجة"), ar("النضج"), ar("التاريخ")]]
        for f in fruit_h[:5]:
            f_data.append([get_thumbnail(f.image_url), ar(f.quality_grade), ar(f.ripeness_level), f.created_at.strftime("%m-%d %H:%M")])
        t5 = Table(f_data, colWidths=[60, 120, 150, 100]); t5.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#FFA000")),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),'Arabic'),('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('GRID',(0,0),(-1,-1),1,colors.grey)]))
        elements.append(t5)

        doc.build(elements)
        if os.path.exists(chart_path): os.remove(chart_path)
    except Exception as e:
        if os.path.exists(chart_path): os.remove(chart_path)
        raise HTTPException(status_code=500, detail=str(e))
    new_report = GeneratedReport(user_id=user_id, name=report_name, report_type=f"{period.capitalize()} Report", size=f"{os.path.getsize(file_path)/1024:.1f} KB", file_path=file_path)
    db.add(new_report); db.commit()
    return {"status": "success", "url": f"/download_reports/farmer_reports/{report_name}"}
@router.get("/list/{user_id}")
async def list_farmer_reports(user_id: int, db: Session = Depends(get_db)):
    return db.query(GeneratedReport).filter(GeneratedReport.user_id == user_id).order_by(desc(GeneratedReport.date)).all()