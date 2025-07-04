from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

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

# Utility: Normalize email column
def normalize_emails(series):
    return series.astype(str).str.strip().str.lower()

# Health check route
@app.get("/")
def read_root():
    return {"message": "Email Cleanup API is live!"}

# CSV upload route
@app.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    brand: str = Form(...),
    db: Session = Depends(get_db)
):
    file_path = os.path.join(UPLOAD_FOLDER, f"{datetime.now().timestamp()}_{file.filename}")
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        df = pd.read_csv(file_path, encoding='cp1252')

        if 'Email' not in df.columns:
            return JSONResponse(status_code=400, content={"error": "CSV missing 'Email' column."})

        df['Email'] = normalize_emails(df['Email'])

        # Get all invalid emails from DB (no brand filter)
        invalid_emails = db.query(InvalidEmail.email).all()
        invalid_emails_set = {email for (email,) in invalid_emails if email}

        df['is_invalid'] = df['Email'].apply(lambda e: e in invalid_emails_set)
        sample = df.head(10).to_dict(orient="records")

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid CSV: {str(e)}"})

    return {
        "filename": file.filename,
        "rows": len(df),
        "brand": brand.strip(),
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
        if not db.query(InvalidEmail).filter_by(email=email).first():
            db.add(InvalidEmail(email=email, brand=data.brand.strip()))
            added += 1
    db.commit()
    return {"status": "success", "brand": data.brand.strip(), "added": added}

# Route to validate emails in uploaded CSV
@app.post("/validate-emails")
async def validate_emails(
    file: UploadFile = File(...),
    brand: str = Form(...),
    db: Session = Depends(get_db)
):
    file_path = os.path.join(UPLOAD_FOLDER, f"validate_{datetime.now().timestamp()}_{file.filename}")
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        df = pd.read_csv(file_path, encoding='cp1252')
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid CSV: {str(e)}"})

    # Detect email column
    email_col = None
    for col in df.columns:
        if "email" in col.lower():
            email_col = col
            break

    if not email_col:
        return JSONResponse(status_code=400, content={"error": "Email column not found in CSV."})

    df[email_col] = normalize_emails(df[email_col])

    # Get all invalid emails (no brand filter)
    invalid_set = {
        record.email.strip().lower()
        for record in db.query(InvalidEmail).all()
        if record.email
    }

    df["status"] = df[email_col].apply(lambda e: "invalid" if e in invalid_set else "valid")

    valid_emails = df[df["status"] == "valid"][email_col].tolist()
    invalid_emails = df[df["status"] == "invalid"][email_col].tolist()

    return {
        "total": len(df),
        "valid_count": len(valid_emails),
        "invalid_count": len(invalid_emails),
        "valid_emails": valid_emails[:50],
        "invalid_emails": invalid_emails[:50],
    }
