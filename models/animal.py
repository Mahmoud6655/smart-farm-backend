from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class AnimalWeight(Base):
    __tablename__ = "animal_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # البيانات المطلوبة بناءً على التصميم
    estimated_weight = Column(Float)   # الوزن المقدر (مثل 363.0)
    animal_type = Column(String)      # نوع الحيوان (مثل Cattle)
    confidence_score = Column(Float)   # نسبة التأكد (مثل 95.0)
    image_url = Column(String)         # صورة الحيوان
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())