from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from database import Base

class PlantScan(Base):
    __tablename__ = "plant_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # الأعمدة الجديدة والمعدلة حسب طلبك
    status = Column(String)          # "Healthy" أو "Disease Detected"
    disease_name = Column(String, nullable=True) # اسم المرض أو NULL لو سليم
    confidence = Column(Float)       # نسبة التأكد كرقـم (مثلاً 88.5)
    image_url = Column(String)       # مسار الصورة
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())