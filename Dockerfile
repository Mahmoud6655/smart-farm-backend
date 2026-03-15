# اختيار نظام التشغيل بايثون
FROM python:3.10-slim

# ضبط مكان العمل جوه السيرفر
WORKDIR /app

# تثبيت مكتبات النظام اللازمة لـ OpenCV والذكاء الاصطناعي
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المكتبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# فتح بورت السيرفر (Hugging Face بيستخدم 7860 أوتوماتيك)
EXPOSE 7860

# أمر تشغيل السيرفر
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]