from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
from datetime import datetime
from sqlalchemy.orm import Session

from app import models
from app.database import engine, SessionLocal
from app.models import InvalidEmail
from app.database import init_db

# Initialize DB
models.Base.metadata.create_all(bind=engine)
init_db()

# Temp uploads folder
UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create FastAPI app
app = FastAPI()

# CORS config (allow React/frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: Get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check route
@app.get("/")
def read_root():
    return {"message": "Email Cleanup API is live!"}

# CSV upload route
@app.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    brand: str = Form(...)
):
    file_path = os.path.join(UPLOAD_FOLDER, f"{datetime.now().timestamp()}_{file.filename}")
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        df = pd.read_csv(file_path, encoding='cp1252')
        sample = df.head(5).to_dict(orient="records")
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid CSV: {str(e)}"})

    return {
        "filename": file.filename,
        "rows": len(df),
        "brand": brand,
        "preview": sample
    }

# Pydantic model for JSON upload
class EmailUploadRequest(BaseModel):
    emails: List[str]
    brand: str

# Route to save invalid emails (accepts JSON)
@app.post("/invalid-emails/add")
def add_invalid_emails(
    data: EmailUploadRequest,
    db: Session = Depends(get_db)
):
    added = 0
    for email in data.emails:
        email = email.strip().lower()
        if not db.query(InvalidEmail).filter_by(email=email, brand=data.brand).first():
            db.add(InvalidEmail(email=email, brand=data.brand))
            added += 1
    db.commit()
    return {"status": "success", "brand": data.brand, "added": added}
