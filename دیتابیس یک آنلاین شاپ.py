from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel
from typing import List

# تنظیمات پایگاه داده
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# مدل‌های پایگاه داده
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

    posts = relationship("Post", back_populates="owner")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    caption = Column(String)
    image_url = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="posts")

# ایجاد پایگاه داده
Base.metadata.create_all(bind=engine)

# اسکیماهای Pydantic
class PostBase(BaseModel):
    caption: str
    image_url: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    posts: List[Post] = []

    class Config:
        orm_mode = True

# توابع CRUD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(db: Session, user: UserCreate):
    db_user = User(username=user.username, password_hash=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_posts(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Post).offset(skip).limit(limit).all()

def create_post(db: Session, post: PostCreate, owner_id: int):
    db_post = Post(**post.dict(), owner_id=owner_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

# API اصلی
app = FastAPI()

@app.post("/users/", response_model=User)
def api_create_user(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db=db, user=user)

@app.post("/posts/", response_model=Post)
def api_create_post(post: PostCreate, db: Session = Depends(get_db), owner_id: int = 1):
    return create_post(db=db, post=post, owner_id=owner_id)

@app.get("/posts/", response_model=List[Post])
def api_get_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_posts(db, skip=skip, limit=limit)

@app.post("/uploadfile/")
async def api_upload_file(file: UploadFile = File(...)):
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(file.file.read())
    return {"filename": file.filename}

