from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func, text

from backend_app import models
from backend_app.database import engine, SessionLocal, init_db
from backend_app.models import InvalidEmail, MasterEmail, EmailTR, EmailMFM, EmailNYSS

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
    allow_origins=["*", "http://localhost:5173"],
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

# Pydantic model for invalid email submission
class EmailUploadRequest(BaseModel):
    emails: List[str]
    brand: str

# Upload and preview route
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
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        if 'Email' not in df.columns:
            return JSONResponse(status_code=400, content={"error": "CSV missing 'Email' column."})

        df['Email'] = normalize_emails(df['Email'])

        # Get invalid emails from DB
        invalid_emails = db.query(InvalidEmail.email).all()
        invalid_emails_set = {email for (email,) in invalid_emails if email}

        df['is_invalid'] = df['Email'].apply(lambda e: e in invalid_emails_set)

        # Filter out invalids and save cleaned CSV
        cleaned_df = df[df['is_invalid'] == False].copy()
        cleaned_path = os.path.join(UPLOAD_FOLDER, f"cleaned_{file.filename}")
        cleaned_df.to_csv(cleaned_path, index=False)

        sample = cleaned_df.head(10).to_dict(orient="records")

        # === AUTO-RUN CLEANING PIPELINE === #

        # 1. Transform cleaned data
        from fastapi import Form as _Form  # Prevent FastAPI Form conflict
        transform_result = transform_cleaned_data(
            filename=f"cleaned_{file.filename}",
            brand=brand,
            db=db
        )
        if isinstance(transform_result, JSONResponse):
            return transform_result

        # 2. Save to brand table
        save_result = save_to_brand(
            filename=transform_result["transformed_file"],
            brand=brand,
            db=db
        )
        if isinstance(save_result, JSONResponse):
            return save_result

        # 3. Merge into master_emails
        merge_result = merge_into_master(db=db)
        if isinstance(merge_result, JSONResponse):
            return merge_result

        # Final response
        return {
            "status": "success",
            "brand": brand,
            "rows_uploaded": len(df),
            "rows_after_invalid_removal": len(cleaned_df),
            "transformed_file": transform_result["transformed_file"],
            "preview": sample,
            "inserted_to_brand": save_result.get("inserted", 0),
            "merge_result": merge_result
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Upload failed: {str(e)}"})


# Add invalid emails
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

# Validate emails in uploaded CSV
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
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid CSV: {str(e)}"})

    email_col = next((col for col in df.columns if "email" in col.lower()), None)
    if not email_col:
        return JSONResponse(status_code=400, content={"error": "Email column not found in CSV."})

    df[email_col] = normalize_emails(df[email_col])
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

# Transform data + UPSERT into master
@app.post("/transform-cleaned-data")
def transform_cleaned_data(
    filename: str = Form(...),
    brand: str = Form(...),
    db: Session = Depends(get_db)
):
    brand = brand.strip()
    brand_short = {
        "Tony Romas": "TR",
        "The Manhattan Fish Market": "MFM",
        "New York Steak Shack": "NYSS"
    }

    if brand not in brand_short:
        return JSONResponse(status_code=400, content={"error": "Unknown brand."})

    brand_code = brand_short[brand]
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found."})

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        segment_col = next((col for col in df.columns if "segment" in col.lower()), None)
        if not segment_col:
            return JSONResponse(status_code=400, content={"error": "Segment column not found."})
        brand_col = next((col for col in df.columns if "brand" in col.lower()), None)
        if not brand_col:
            return JSONResponse(status_code=400, content={"error": "Brand column not found."})

        df[segment_col] = brand_code + "_" + df[segment_col].astype(str).str.strip()
        df[brand_col] = brand

        transformed_filename = f"transformed_{filename}"
        transformed_path = os.path.join(UPLOAD_FOLDER, transformed_filename)
        df.to_csv(transformed_path, index=False)

        segment_field = f"segment_{brand_code.lower()}"
        is_flag = f"is_{brand_code.lower()}"

        for _, row in df.iterrows():
            email = row.get("email")
            if pd.isna(email):
                continue
            stmt = text(f"""
                INSERT INTO master_emails (
                    email, card_no, name, phone,
                    {segment_field}, {is_flag}, last_updated
                )
                VALUES (
                    :email, :card_no, :name, :phone,
                    :segment, TRUE, NOW()
                )
                ON CONFLICT (email) DO UPDATE SET
                    {segment_field} = EXCLUDED.{segment_field},
                    {is_flag} = TRUE,
                    last_updated = NOW(),
                    card_no = COALESCE(master_emails.card_no, EXCLUDED.card_no),
                    name = COALESCE(master_emails.name, EXCLUDED.name),
                    phone = COALESCE(master_emails.phone, EXCLUDED.phone);
            """)
            db.execute(stmt, {
                "email": row.get("email"),
                "card_no": row.get("card_no"),
                "name": row.get("name"),
                "phone": row.get("phone"),
                "segment": row.get(segment_col)
            })

        db.commit()
        preview = df.head(10).to_dict(orient="records")
        return {
            "status": "success",
            "brand": brand,
            "segment_column": segment_col,
            "brand_column": brand_col,
            "transformed_file": transformed_filename,
            "preview": preview
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to transform: {str(e)}"})

# Save into brand-specific table
@app.post("/save-to-brand")
def save_to_brand(
    filename: str = Form(...),
    brand: str = Form(...),
    db: Session = Depends(get_db)
):
    brand_map = {
        "Tony Romas": "emails_tr",
        "The Manhattan Fish Market": "emails_mfm",
        "New York Steak Shack": "emails_nyss"
    }

    if brand not in brand_map:
        return JSONResponse(status_code=400, content={"error": "Unknown brand."})

    table_name = brand_map[brand]
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found."})

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        # 🔧 Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]

        # ✅ Required columns check
        required_cols = ["card_no", "brand", "name", "phone", "email", "segment"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            return JSONResponse(status_code=400, content={"error": f"Missing columns: {missing_cols}"})

        insert_count = 0
        for _, row in df.iterrows():
            stmt = text(f"""
                INSERT INTO {table_name} (card_no, brand, name, phone, email, segment)
                VALUES (:card_no, :brand, :name, :phone, :email, :segment)
                ON CONFLICT (email) DO UPDATE SET
                    card_no = EXCLUDED.card_no,
                    brand = EXCLUDED.brand,
                    name = EXCLUDED.name,
                    phone = EXCLUDED.phone,
                    segment = EXCLUDED.segment;
            """)
            
            db.execute(stmt, {
                "card_no": row["card_no"],
                "brand": row["brand"],
                "name": row["name"],
                "phone": row["phone"],
                "email": str(row["email"]).strip().lower(),
                "segment": row["segment"]
            })

        insert_count += 1

        db.commit()
        return {
            "status": "success",
            "brand_table": table_name,
            "inserted": insert_count
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to save: {str(e)}"})

# Merge all brand tables into master
@app.post("/merge-into-master")
def merge_into_master(db: Session = Depends(get_db)):
    try:
        now = datetime.utcnow()
        inserted, updated = 0, 0

        tr_data = db.execute(select(EmailTR)).scalars().all()
        mfm_data = db.execute(select(EmailMFM)).scalars().all()
        nyss_data = db.execute(select(EmailNYSS)).scalars().all()

        email_map = {}

        for record in tr_data + mfm_data + nyss_data:
            email = record.email.strip().lower()
            if email not in email_map:
                email_map[email] = {
                    "email": email,
                    "card_no": record.card_no,
                    "name": record.name,
                    "phone": record.phone,
                    "segment_tr": None,
                    "segment_mfm": None,
                    "segment_nyss": None,
                    "is_tr": False,
                    "is_mfm": False,
                    "is_nyss": False,
                    "last_updated": now
                }

            if isinstance(record, EmailTR):
                email_map[email]["segment_tr"] = record.segment
                email_map[email]["is_tr"] = True
            elif isinstance(record, EmailMFM):
                email_map[email]["segment_mfm"] = record.segment
                email_map[email]["is_mfm"] = True
            elif isinstance(record, EmailNYSS):
                email_map[email]["segment_nyss"] = record.segment
                email_map[email]["is_nyss"] = True

        for email, data in email_map.items():
            existing = db.query(MasterEmail).filter_by(email=email).first()
            if existing:
                for field, value in data.items():
                    setattr(existing, field, value)
                updated += 1
            else:
                db.add(MasterEmail(**data))
                inserted += 1

        db.commit()
        return {
            "status": "success",
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
