from sqlalchemy import Column, Integer, String, DateTime, ForeignKey # ضفنا ForeignKey هنا
from database import Base
from datetime import datetime

class GeneratedReport(Base):
    __tablename__ = "generated_reports"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)      # اسم الملف
    date = Column(DateTime, default=datetime.now)
    report_type = Column(String) # نوع التقرير (Full Audit, AI, etc.)
    size = Column(String)      # حجم الملف (مثلاً 1.2 MB)
    file_path = Column(String) # مكان الملف على السيرفر
    
    # السطر الجديد اللي هيحل الـ AttributeError:
    user_id = Column(Integer, ForeignKey("users.id"))