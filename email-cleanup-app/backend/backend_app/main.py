from fastapi import FastAPI, UploadFile, File, Form, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
import io
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from sqlalchemy import or_, and_

from backend_app import models
from backend_app.database import engine, SessionLocal, init_db
from backend_app.models import InvalidEmail, MasterEmail, EmailTR, EmailMFM, EmailNYSS

# Initialize DB
models.Base.metadata.create_all(bind=engine)
init_db()

UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def normalize_emails(series):
    return series.astype(str).str.strip().str.lower()

def normalize_and_map_columns(df):
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    column_aliases = {
        "card_no": ["card_no", "card_number", "cardnum", "cardno", "card_no_"],
        "brand": ["brand", "restaurant", "outlet"],
        "name": ["name", "full_name", "customer_name"],
        "phone": ["phone", "mobile", "mobile_number", "contact"],
        "email": ["email", "email_address", "e-mail"],
        "segment": ["segment", "segment_group", "group"]
    }
    for standard, aliases in column_aliases.items():
        for alias in aliases:
            if alias in df.columns and alias != standard:
                df.rename(columns={alias: standard}, inplace=True)
                break
    return df

class EmailUploadRequest(BaseModel):
    emails: List[str]
    brand: str

@app.get("/")
def read_root():
    return {"message": "Email Cleanup API is live!"}

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...), brand: str = Form(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_FOLDER, f"{datetime.now().timestamp()}_{file.filename}")
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df = normalize_and_map_columns(df)

        if 'email' not in df.columns:
            return JSONResponse(status_code=400, content={"error": "CSV missing 'email' column.", "detected_columns": df.columns.tolist()})

        df['email'] = normalize_emails(df['email'])

        invalid_emails_set = {email for (email,) in db.query(InvalidEmail.email).all() if email}
        df['is_invalid'] = df['email'].apply(lambda e: e in invalid_emails_set)

        cleaned_df = df[df['is_invalid'] == False].copy()
        cleaned_path = os.path.join(UPLOAD_FOLDER, f"cleaned_{file.filename}")
        cleaned_df.to_csv(cleaned_path, index=False)
        sample = cleaned_df.head(10).to_dict(orient="records")

        transform_result = transform_cleaned_data(filename=f"cleaned_{file.filename}", brand=brand, db=db)
        if isinstance(transform_result, JSONResponse):
            return transform_result

        save_result = save_to_brand(filename=transform_result["transformed_file"], brand=brand, db=db)
        if isinstance(save_result, JSONResponse):
            return save_result
        
        db.flush()
        db.expire_all()

        merge_result = merge_into_master(db=db)
        if isinstance(merge_result, JSONResponse):
            return merge_result
        
        # Extract invalids
        invalid_df = df[df['is_invalid'] == True].copy()
        invalid_emails = invalid_df['email'].tolist()
        invalid_count = len(invalid_emails)

        return {
            "status": "success",
            "brand": brand,
            "rows_uploaded": len(df),
            "rows_after_invalid_removal": len(cleaned_df),
            "invalid_count": invalid_count,
            "invalid_emails": invalid_emails[:50],  # Optional: show top 50 only
            "transformed_file": transform_result["transformed_file"],
            "preview": sample,
            "inserted_to_brand": save_result.get("inserted", 0),
            "merge_result": merge_result
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Upload failed: {str(e)}"})


@app.post("/invalid-emails/upload")
async def upload_invalid_emails(
    file: UploadFile = File(...),
    brand: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8-sig")))

        if 'email' not in df.columns:
            return JSONResponse(status_code=400, content={
                "error": "Missing 'email' column.",
                "detected_columns": df.columns.tolist()
            })

        df['email'] = df['email'].astype(str).str.strip().str.lower()
        added = 0

        for email in df['email'].unique():
            if not db.query(InvalidEmail).filter_by(email=email).first():
                db.add(InvalidEmail(email=email, brand=brand))
                added += 1

        db.commit()
        return {"status": "success", "brand": brand, "added": added}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/invalid-emails")
def get_invalid_emails(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    brand: str = Query(None),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(InvalidEmail)

        if search:
            query = query.filter(InvalidEmail.email.ilike(f"%{search}%"))
        if brand:
            query = query.filter(InvalidEmail.brand == brand)

        total = query.count()
        emails = query.offset(offset).limit(limit).all()

        return {
            "status": "success",
            "total": total,
            "data": [{"email": e.email, "brand": e.brand} for e in emails]
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



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
        df = normalize_and_map_columns(df)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid CSV: {str(e)}"})

    if 'email' not in df.columns:
        return JSONResponse(status_code=400, content={"error": "Email column not found in CSV.", "detected_columns": df.columns.tolist()})

    df["email"] = normalize_emails(df["email"])
    invalid_set = {
        record.email.strip().lower()
        for record in db.query(InvalidEmail).all()
        if record.email
    }

    df["status"] = df["email"].apply(lambda e: "invalid" if e in invalid_set else "valid")
    valid_emails = df[df["status"] == "valid"]["email"].tolist()
    invalid_emails = df[df["status"] == "invalid"]["email"].tolist()

    return {
        "total": len(df),
        "valid_count": len(valid_emails),
        "invalid_count": len(invalid_emails),
        "valid_emails": valid_emails[:50],
        "invalid_emails": invalid_emails[:50],
    }



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
        df = normalize_and_map_columns(df)

        if "segment" not in df.columns or "brand" not in df.columns:
            return JSONResponse(status_code=400, content={
                "error": "Missing required columns: segment or brand.",
                "detected_columns": df.columns.tolist()
            })

        df["segment"] = brand_code + "_" + df["segment"].astype(str).str.strip()
        df["brand"] = brand

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
                "email": str(row.get("email")).strip().lower(),
                "card_no": row.get("card_no"),
                "name": row.get("name"),
                "phone": row.get("phone"),
                "segment": row.get("segment")
            })

        db.commit()
        preview = df.head(10).to_dict(orient="records")
        return {
            "status": "success",
            "brand": brand,
            "transformed_file": transformed_filename,
            "preview": preview
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to transform: {str(e)}"})



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
        df = normalize_and_map_columns(df)

        required_cols = ["card_no", "brand", "name", "phone", "email", "segment"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return JSONResponse(status_code=400, content={"error": f"Missing columns: {missing_cols}", "detected_columns": df.columns.tolist()})

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


@app.post("/merge-into-master")
def merge_into_master(db: Session = Depends(get_db)):
    try:
        now = datetime.utcnow()
        inserted, updated, removed = 0, 0, 0

        tr_data = db.execute(select(EmailTR)).scalars().all()
        mfm_data = db.execute(select(EmailMFM)).scalars().all()
        nyss_data = db.execute(select(EmailNYSS)).scalars().all()


        # Rebuild master_emails from brand tables
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



@app.get("/master-emails")
def get_master_emails(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    brand: str = Query(None),
    segment: str = Query(None),
    full_export: bool = Query(False),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(MasterEmail)

        # Apply filters
        if search:
            query = query.filter(MasterEmail.email.ilike(f"%{search}%"))
        if brand == "TR":
            query = query.filter(MasterEmail.is_tr == True)
        elif brand == "MFM":
            query = query.filter(MasterEmail.is_mfm == True)
        elif brand == "NYSS":
            query = query.filter(MasterEmail.is_nyss == True)
        if segment:
            query = query.filter(
                or_(
                    MasterEmail.segment_tr.ilike(f"%{segment}%"),
                    MasterEmail.segment_mfm.ilike(f"%{segment}%"),
                    MasterEmail.segment_nyss.ilike(f"%{segment}%"),
                )
            )

        total = query.count()

        # Only paginate if not full_export
        if not full_export:
            query = query.offset(offset).limit(limit)

        results = query.order_by(MasterEmail.last_updated.desc()).all()

        emails = [
            {
                "email": row.email,
                "card_no": row.card_no,
                "name": row.name,
                "phone": row.phone,
                "segment_tr": row.segment_tr,
                "segment_mfm": row.segment_mfm,
                "segment_nyss": row.segment_nyss,
                "is_tr": row.is_tr,
                "is_mfm": row.is_mfm,
                "is_nyss": row.is_nyss,
                "last_updated": row.last_updated
            }
            for row in results
        ]

        return {"status": "success", "total": total, "data": emails}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
