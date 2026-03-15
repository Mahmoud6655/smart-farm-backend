from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class CropRecommendation(Base):
    __tablename__ = "crop_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # المدخلات
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall = Column(Float)
    soil_type = Column(String)
    
    # الحقل الجديد لتخزين الشهر
    growing_month = Column(Integer) 
    
    # المخرجات
    recommended_crop = Column(String)    # المحصول المقترح
    expected_yield = Column(String)      # مستوى الإنتاج (High, Medium, Low)
    recommendation_desc = Column(String) # النص التوضيحي
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())