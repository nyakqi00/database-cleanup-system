from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import os
from datetime import datetime

UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = FastAPI()

# Enable frontend access (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Email Cleanup API is live!"}

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
