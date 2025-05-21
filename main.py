# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env (nếu có)
load_dotenv()

# Cấu hình kết nối PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/newsdb")

# Tạo SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Định nghĩa Models
class BaiViet(Base):
    __tablename__ = "bai_viet"
    
    id = Column(Integer, primary_key=True, index=True)
    tieu_de = Column(String, index=True)
    mo_ta = Column(String)
    noi_dung = Column(Text)
    hinh_anh = Column(String)
    ngay_dang = Column(DateTime, default=datetime.now)
    la_tin_hot = Column(Boolean, default=False)
    luot_xem = Column(Integer, default=0)
    danh_muc_id = Column(Integer, ForeignKey("danh_muc.id"))
    
    danh_muc = relationship("DanhMuc", back_populates="bai_viet")

class DanhMuc(Base):
    __tablename__ = "danh_muc"
    
    id = Column(Integer, primary_key=True, index=True)
    ten = Column(String, unique=True, index=True)
    
    bai_viet = relationship("BaiViet", back_populates="danh_muc")

# Định nghĩa Pydantic models cho request/response
class DanhMucBase(BaseModel):
    ten: str

class DanhMucCreate(DanhMucBase):
    pass

class DanhMucResponse(DanhMucBase):
    id: int
    
    class Config:
        orm_mode = True

class BaiVietBase(BaseModel):
    tieu_de: str
    mo_ta: Optional[str] = None
    noi_dung: str
    hinh_anh: Optional[str] = None
    la_tin_hot: Optional[bool] = False
    danh_muc_id: int

class BaiVietCreate(BaiVietBase):
    pass

class BaiVietResponse(BaiVietBase):
    id: int
    ngay_dang: datetime
    luot_xem: int
    
    class Config:
        orm_mode = True

# Tạo ứng dụng FastAPI
app = FastAPI(title="Tin Tức API")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường production, hãy giới hạn origins cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency để lấy database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Các hàm CRUD
def get_tin_hot(db: Session, skip: int = 0, limit: int = 10):
    return db.query(BaiViet).filter(BaiViet.la_tin_hot == True).order_by(BaiViet.ngay_dang.desc()).offset(skip).limit(limit).all()

def get_tin_moi_nhat(db: Session, skip: int = 0, limit: int = 10):
    return db.query(BaiViet).order_by(BaiViet.ngay_dang.desc()).offset(skip).limit(limit).all()

def get_bai_viet_by_id(db: Session, bai_viet_id: int):
    return db.query(BaiViet).filter(BaiViet.id == bai_viet_id).first()

def get_bai_viet_by_danh_muc(db: Session, danh_muc_id: int, skip: int = 0, limit: int = 10):
    return db.query(BaiViet).filter(BaiViet.danh_muc_id == danh_muc_id).order_by(BaiViet.ngay_dang.desc()).offset(skip).limit(limit).all()

def create_bai_viet(db: Session, bai_viet: BaiVietCreate):
    db_bai_viet = BaiViet(**bai_viet.dict())
    db.add(db_bai_viet)
    db.commit()
    db.refresh(db_bai_viet)
    return db_bai_viet

# Định nghĩa API endpoints
@app.get("/")
def read_root():
    return {"message": "Chào mừng đến với API tin tức"}

@app.get("/api/tintuc/hot", response_model=List[BaiVietResponse])
def api_get_tin_hot(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Lấy danh sách tin nóng/tin hot"""
    return get_tin_hot(db, skip=skip, limit=limit)

@app.get("/api/tintuc/moinhat", response_model=List[BaiVietResponse])
def api_get_tin_moi_nhat(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Lấy danh sách tin mới nhất"""
    return get_tin_moi_nhat(db, skip=skip, limit=limit)

@app.get("/api/tintuc/{tin_id}", response_model=BaiVietResponse)
def api_get_tin_chi_tiet(tin_id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết một bài viết theo ID"""
    tin_tuc = get_bai_viet_by_id(db, bai_viet_id=tin_id)
    if tin_tuc is None:
        raise HTTPException(status_code=404, detail="Bài viết không tìm thấy")
    
    # Tăng lượt xem
    tin_tuc.luot_xem += 1
    db.commit()
    
    return tin_tuc

@app.get("/api/danhmuc/{danh_muc_id}/tintuc", response_model=List[BaiVietResponse])
def api_get_tin_theo_danh_muc(danh_muc_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Lấy danh sách tin theo danh mục"""
    return get_bai_viet_by_danh_muc(db, danh_muc_id=danh_muc_id, skip=skip, limit=limit)

@app.post("/api/tintuc/", response_model=BaiVietResponse, status_code=status.HTTP_201_CREATED)
def api_tao_bai_viet(bai_viet: BaiVietCreate, db: Session = Depends(get_db)):
    """Tạo một bài viết mới"""
    return create_bai_viet(db, bai_viet)

# Khởi chạy ứng dụng với uvicorn nếu file được git checkout -b cicd-testchạy trực tiếp
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)