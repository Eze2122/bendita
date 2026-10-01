from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import requests


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    price: Optional[float] = None
    category: str = "Accesorios"
    audience: str = "ambos"
    stock: Optional[int] = None
    images: List[str] = []
    variants: List[str] = []
    is_new: bool = False
    is_featured: bool = False
    is_sale: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str

STORAGE_BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
STORAGE_URL = STORAGE_BASE.rstrip("/") + "/objstore/api/v1/storage"
storage_key = None
APP_NAME = "bendita-accesorios"

def init_storage(force=False):
    global storage_key
    if storage_key and not force:
        return storage_key
    response = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")}, timeout=30)
    response.raise_for_status()
    storage_key = response.json()["storage_key"]
    return storage_key

def upload_object(path, data, content_type):
    response = requests.put(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": init_storage(), "Content-Type": content_type}, data=data, timeout=120)
    response.raise_for_status()
    return response.json()

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

@api_router.get("/products", response_model=List[Product])
async def list_products():
    return await db.products.find({"deleted": {"$ne": True}}, {"_id": 0, "deleted": 0}).sort("created_at", -1).to_list(1000)

@api_router.post("/products", response_model=Product)
async def create_product(product: Product):
    doc = product.model_dump()
    await db.products.insert_one(doc)
    return product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product: Product):
    doc = product.model_dump(); doc["id"] = product_id
    result = await db.products.replace_one({"id": product_id}, doc)
    if not result.matched_count:
        raise HTTPException(404, "Producto no encontrado")
    return Product(**doc)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    result = await db.products.update_one({"id": product_id}, {"$set": {"deleted": True}})
    if not result.matched_count:
        raise HTTPException(404, "Producto no encontrado")
    return {"ok": True}

DEFAULT_CATEGORIES = ["Mujer", "Hombre", "Aros", "Collares", "Cadenitas", "Anillos", "Pulseras", "Dijes", "Accesorios", "Próximamente"]

@api_router.get("/categories", response_model=List[Category])
async def list_categories():
    if await db.categories.count_documents({}) == 0:
        await db.categories.insert_many([{"id": str(uuid.uuid4()), "name": name, "slug": name.lower().replace(" ", "-")} for name in DEFAULT_CATEGORIES])
    return await db.categories.find({}, {"_id": 0}).sort("name", 1).to_list(100)

@api_router.post("/categories", response_model=Category)
async def create_category(category: Category):
    await db.categories.insert_one(category.model_dump())
    return category

@api_router.put("/categories/{category_id}", response_model=Category)
async def update_category(category_id: str, category: Category):
    doc = category.model_dump(); doc["id"] = category_id
    result = await db.categories.replace_one({"id": category_id}, doc)
    if not result.matched_count: raise HTTPException(404, "Categoría no encontrada")
    return Category(**doc)

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    result = await db.categories.delete_one({"id": category_id})
    if not result.deleted_count: raise HTTPException(404, "Categoría no encontrada")
    return {"ok": True}

@api_router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "Solo se permiten imágenes")
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(400, "La imagen no puede superar 8 MB")
    ext = (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg").lower()
    path = f"{APP_NAME}/uploads/{uuid.uuid4()}.{ext}"
    try:
        result = upload_object(path, data, file.content_type or "image/jpeg")
    except Exception as exc:
        logger.exception("Storage upload failed")
        raise HTTPException(502, f"No se pudo guardar la imagen: {exc}")
    await db.files.insert_one({"path": result["path"], "content_type": file.content_type, "deleted": False})
    return {"url": f"/api/files/{result['path']}", "path": result["path"]}

@api_router.get("/files/{path:path}")
async def get_file(path: str):
    from fastapi.responses import Response
    record = await db.files.find_one({"path": path, "deleted": False}, {"_id": 0})
    if not record: raise HTTPException(404, "Imagen no encontrada")
    try:
        response = requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": init_storage()}, timeout=60)
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(502, f"No se pudo leer la imagen: {exc}")
    return Response(response.content, media_type=record.get("content_type", "image/jpeg"))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()