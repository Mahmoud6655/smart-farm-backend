from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class FruitQuality(Base):
    __tablename__ = "fruit_quality_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    image_url = Column(String)
    quality_grade = Column(String)    # Grade A, B, C
    market_status = Column(String)    # الوصف مثل Premium quality
    ripeness_level = Column(String)   # مستوى النضج
    defect_details = Column(String)   # تفاصيل العيوب
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())