from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import os

from database import db, create_document, get_documents
from schemas import User, Product, User as _UserSchema  # keep import to ensure schemas are loaded

app = FastAPI(title="SEO Agency API", version="1.0.0")

# CORS - allow all for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LeadIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=120)
    website: Optional[str] = Field(None, max_length=200)
    budget: Optional[str] = Field(None, max_length=100)
    message: Optional[str] = Field(None, max_length=2000)


class LeadOut(LeadIn):
    id: str


@app.get("/")
def root():
    return {"message": "SEO Agency backend is running"}


@app.get("/test")
def test_connection():
    db_url = os.getenv("DATABASE_URL", "")
    db_name = os.getenv("DATABASE_NAME", "")

    # Determine connection status and list collections if possible
    try:
        collections = db.list_collection_names() if db is not None else []
        connection_status = "connected" if db is not None else "not_configured"
    except Exception as e:
        collections = []
        connection_status = f"error: {str(e)}"

    # Mask DB URL for safety
    masked_url = None
    if db_url:
        prefix = db_url.split("://")[0] + "://"
        masked_url = prefix + "***@" + db_url.split("@")[-1] if "@" in db_url else prefix + "***"

    return {
        "backend": "ok",
        "database": "mongodb",
        "database_url": masked_url or "not set",
        "database_name": db_name or "not set",
        "connection_status": connection_status,
        "collections": collections,
    }


@app.post("/leads", response_model=dict)
def create_lead(lead: LeadIn):
    try:
        inserted_id = create_document("lead", lead)
        return {"id": inserted_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads", response_model=List[dict])
def list_leads(limit: int = 25):
    try:
        docs = get_documents("lead", {}, limit=limit)
        # Convert ObjectId to string
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
