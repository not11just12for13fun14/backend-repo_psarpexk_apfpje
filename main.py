import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Photo, Purchase

app = FastAPI(title="Photo Bank API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PhotoFilters(BaseModel):
    themes: Optional[List[str]] = None
    orientation: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    q: Optional[str] = None

@app.get("/")
def health():
    return {"status": "ok", "service": "photo-bank"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

@app.get("/api/photos")
def list_photos(
    themes: Optional[str] = Query(None, description="Comma-separated themes"),
    orientation: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    q: Optional[str] = Query(None, description="Search in title/description/tags")
):
    """Public catalog with filters"""
    if db is None:
        return []

    filt = {"is_public": True}

    if themes:
        theme_list = [t.strip() for t in themes.split(",") if t.strip()]
        if theme_list:
            filt["themes"] = {"$in": theme_list}
    if orientation:
        filt["orientation"] = orientation
    price_cond = {}
    if min_price is not None:
        price_cond["$gte"] = float(min_price)
    if max_price is not None:
        price_cond["$lte"] = float(max_price)
    if price_cond:
        filt["price"] = price_cond
    if q:
        regex = {"$regex": q, "$options": "i"}
        filt["$or"] = [
            {"title": regex},
            {"description": regex},
            {"tags": regex}
        ]

    docs = get_documents("photo", filt, limit=60)
    # Convert ObjectId
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["id"] = str(d["_id"])
            del d["_id"]
    return docs

class PhotoCreate(Photo):
    pass

@app.post("/api/seller/photos")
def create_photo(photo: PhotoCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    inserted_id = create_document("photo", photo)
    return {"id": inserted_id}

@app.get("/api/seller/photos")
def list_my_photos(seller_id: Optional[str] = Query(None)):
    if db is None:
        return []
    filt = {"seller_id": seller_id} if seller_id else {}
    docs = get_documents("photo", filt, limit=100)
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["id"] = str(d["_id"])
            del d["_id"]
    return docs

@app.get("/schema")
def get_schema():
    # Let the built-in viewer discover collections and fields
    return {
        "user": User.model_json_schema(),
        "photo": Photo.model_json_schema(),
        "purchase": Purchase.model_json_schema(),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
