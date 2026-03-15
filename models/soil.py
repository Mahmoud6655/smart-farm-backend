from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class SoilAnalysis(Base):
    __tablename__ = "soil_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # المدخلات الرقمية اللي المستخدم هيبعتها (N, P, K, pH, Moisture)
    ph_level = Column(Float)
    moisture = Column(Float)
    nitrogen = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    
    # مخرجات النتيجة (السيستم هو اللي بيحسبهم ويخزنهم هنا)
    detected_soil_type = Column(String) # نوع التربة المكتشف
    fertility_level = Column(String)    # مستوى الخصوبة
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())