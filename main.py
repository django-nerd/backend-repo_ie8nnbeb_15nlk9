import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Product, Feedback

app = FastAPI(title="ZenSupply API", description="Backend for the ZenSupply Minecraft Donut SMP IRL Store")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "ZenSupply backend is live"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
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
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Products API
@app.post("/api/products", response_model=dict)
async def create_product(product: Product):
    try:
        new_id = create_document("product", product)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products", response_model=List[dict])
async def list_products(category: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    try:
        filter_query = {}
        if category:
            filter_query["category"] = category
        if q:
            filter_query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"tags": {"$elemMatch": {"$regex": q, "$options": "i"}}}
            ]
        docs = get_documents("product", filter_query, limit)
        # Convert ObjectId to string
        for d in docs:
            if d.get("_id"):
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        doc["id"] = str(doc.pop("_id"))
        return doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Feedback API
@app.post("/api/feedback", response_model=dict)
async def create_feedback(feedback: Feedback):
    try:
        new_id = create_document("feedback", feedback)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feedback", response_model=List[dict])
async def list_feedback(limit: int = 20):
    try:
        docs = get_documents("feedback", {}, limit)
        for d in docs:
            if d.get("_id" ):
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def seed_or_update_products_on_startup():
    """
    Ensure the three core products exist and have the latest pricing/variants.
    Upsert by SKU so existing docs get updated to requested prices.
    """
    try:
        # Pricing per user request
        spawner_unit = 0.025
        shulker_price = 40.0
        money_per_million = 0.03
        elytra_price = 10.0  # updated to $10

        catalog = [
            {
                "sku": "SPAWNER-SKELETON",
                "doc": {
                    "title": "Skeleton Spawner",
                    "description": "Farm bones and arrows. Choose single units or grab a full shulker.",
                    "price": spawner_unit,
                    "category": "Spawners",
                    "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1200&auto=format&fit=crop",
                    "tags": ["spawner", "skeleton", "farm", "shulker"],
                    "in_stock": True,
                    "variants": [
                        {"name": "Single", "type": "option", "price": spawner_unit},
                        {"name": "Shulker (27x)", "type": "bundle", "bundle_qty": 27, "price": shulker_price}
                    ],
                    "updated_at": datetime.utcnow(),
                }
            },
            {
                "sku": "MONEY-PACK",
                "doc": {
                    "title": "Money",
                    "description": "Boost your balance instantly with IRL store credits.",
                    "price": money_per_million,
                    "category": "Money",
                    "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=1200&auto=format&fit=crop",
                    "tags": ["money", "cash", "balance"],
                    "in_stock": True,
                    # Remove variants as requested; quantity will represent millions
                    "variants": [],
                    "updated_at": datetime.utcnow(),
                }
            },
            {
                "sku": "ELYTRA-BASE",
                "doc": {
                    "title": "Elytra",
                    "description": "Soar across the server with an Elytra.",
                    "price": elytra_price,
                    "category": "Kits",
                    "image_url": "https://images.unsplash.com/photo-1606117331651-0c9f0c1f2b2e?q=80&w=1200&auto=format&fit=crop",
                    "tags": ["elytra", "flight", "wings"],
                    "in_stock": True,
                    "variants": [
                        {"name": "Standard", "type": "option", "price": elytra_price},
                        {"name": "Elytra Shulker Box", "type": "bundle", "price": 50.0}
                    ],
                    "updated_at": datetime.utcnow(),
                }
            },
        ]

        for item in catalog:
            sku = item["sku"]
            doc = { **item["doc"], "sku": sku }
            existing = db["product"].find_one({"sku": sku})
            if existing:
                db["product"].update_one({"_id": existing["_id"]}, {"$set": doc})
            else:
                doc["created_at"] = datetime.utcnow()
                db["product"].insert_one(doc)

    except Exception as e:
        # Log but don't crash startup
        print(f"Seed/update error: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
