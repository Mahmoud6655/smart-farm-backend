import requests
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.chatbot import ChatHistory
from models.soil import SoilAnalysis      # موديل التربة
from models.animal import AnimalWeight    # موديل وزن الحيوان
from models.plant import PlantScan        # موديل أمراض النبات
from models.fruit import FruitQuality     # موديل جودة الفاكهة
from admin.system_management import services_db 
from datetime import datetime
#--- استدعاء الحارس من ملف الـ auth ---
from auth import check_user_exists 

router = APIRouter()

# المفتاح الخاص بك من Groq
GROQ_API_KEY = "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"

@router.post("/ask-farm-bot")
async def ask_farm_bot(
    user_id: int = Form(...),
    question: str = Form(...),
    language: str = Form("ar"), 
    db: Session = Depends(get_db)
):
    # 🛡️ الحارس: لو الـ ID مش موجود، العملية هتقف هنا فوراً وترجع 404
    check_user_exists(user_id, db)

    # 1. التأكد إن الخدمة أونلاين
    if services_db["chatbot"]["status"] == "offline":
        raise HTTPException(status_code=503, detail="المساعد الذكي أوفلاين حالياً.")

    # 2. جلب أحدث البيانات من الـ 4 جداول للمستخدم
    latest_soil = db.query(SoilAnalysis).filter(SoilAnalysis.user_id == user_id).order_by(SoilAnalysis.id.desc()).first()
    latest_animal = db.query(AnimalWeight).filter(AnimalWeight.user_id == user_id).order_by(AnimalWeight.id.desc()).first()
    latest_plant = db.query(PlantScan).filter(PlantScan.user_id == user_id).order_by(PlantScan.id.desc()).first()
    latest_fruit = db.query(FruitQuality).filter(FruitQuality.user_id == user_id).order_by(FruitQuality.id.desc()).first()

    # 3. بناء سياق المعلومات (الذاكرة الشاملة للبوت)
    extra_info = "\nسياق بيانات المستخدم الحالية:"
    
    if latest_soil:
        extra_info += f"\n- التربة: نوعها ({latest_soil.detected_soil_type}) وخصوبتها ({latest_soil.fertility_level})."
    else:
        extra_info += "\n- التربة: لم يقم المستخدم بتحليل التربة بعد."

    if latest_animal:
        extra_info += f"\n- الحيوان: نوعه ({latest_animal.animal_type}) ووزنه ({latest_animal.estimated_weight} كيلو)."
    else:
        extra_info += "\n- الحيوان: لم يقم المستخدم بوزن أي حيوان بعد."

    if latest_plant:
        if latest_plant.status == "Healthy":
            extra_info += "\n- صحة الزرع: آخر فحص أظهر أن النبات سليم (Healthy)."
        else:
            extra_info += f"\n- صحة الزرع: تم اكتشاف إصابة بـ ({latest_plant.disease_name})."
    else:
        extra_info += "\n- صحة الزرع: لم يقم المستخدم بفحص أي نباتات بعد."

    if latest_fruit:
        extra_info += (f"\n- جودة المحصول: آخر ثمرة فحصها تصنيفها ({latest_fruit.quality_grade})، "
                       f"وحالتها السوقية ({latest_fruit.market_status})، ونضجها ({latest_fruit.ripeness_level})، "
                       f"وملحوظات العيوب: ({latest_fruit.defect_details}).")
    else:
        extra_info += "\n- جودة المحصول: لم يتم فحص جودة أي ثمار بعد."

    # 4. تحديد التوجيهات (System Content)
    if language == "en":
        system_content = (
            "You are a helpful Egyptian farm expert. Chat naturally like a friend on WhatsApp. "
            "Respond directly and keep it short. Use this user data ONLY if asked: "
            f"{extra_info}"
        )
        error_msg = "Sorry, connection error."
    else:
        system_content = (
            "أنت خبير زراعي وبيطري مصري شاطر جداً. دردش بلهجة فلاحي بسيطة وكأنك بتكلم صاحبك على واتساب. "
            "ممنوع استخدام كلمات أجنبية (إلا لأسماء الأدوية أو الأمراض بالإنجليزية بين قوسين). "
            "ردودك مباشرة وقصيرة جداً وممنوع تفتح مواضيع من عندك. "
            "استخدم المعلومات دي لو المستخدم سألك عن أرضه أو حيواناته أو زرعه أو جودة محصوله: "
            f"{extra_info}"
        )
        error_msg = "عذراً، حصلت مشكلة في الاتصال."

    # 5. جلب ذاكرة الشات (آخر 5 محادثات)
    past_chats = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.id.desc()).limit(5).all()
    
    messages_payload = [{"role": "system", "content": system_content}]
    for chat in reversed(past_chats):
        messages_payload.append({"role": "user", "content": chat.user_message})
        messages_payload.append({"role": "assistant", "content": chat.bot_response})
    
    messages_payload.append({"role": "user", "content": question})

    # 6. الاتصال بـ Groq API
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages_payload,
            "temperature": 0.5 
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        if response.status_code == 200:
            response_text = result["choices"][0]["message"]["content"]
        else:
            response_text = error_msg
    except Exception:
        response_text = error_msg

    # 7. حفظ المحادثة الجديدة في الداتابيز
    try:
        new_chat = ChatHistory(user_id=user_id, user_message=question, bot_response=response_text)
        db.add(new_chat)
        db.commit()
    except Exception:
        db.rollback()

    return {"bot_response": response_text, "time": datetime.now().strftime("%H:%M")}

# --- جلب تاريخ المحادثة ---
@router.get("/chat-history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_db)):
    
    check_user_exists(user_id, db)
    
    history = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.id.asc()).all()
    formatted_history = []
    for chat in history:
        formatted_history.append({"sender": "user", "message": chat.user_message, "time": chat.created_at.strftime("%H:%M") if chat.created_at else ""})
        formatted_history.append({"sender": "bot", "message": chat.bot_response, "time": chat.created_at.strftime("%H:%M") if chat.created_at else ""})
    return formatted_history