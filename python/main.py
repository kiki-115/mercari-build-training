import os
import logging
import pathlib
import hashlib
from fastapi import FastAPI, Form, HTTPException, Depends,File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
import json

# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"
items_file = pathlib.Path(__file__).parent.resolve() / 'items.json'

# 画像を保存し、ハッシュ化したファイル名を返す
def save_image(file: UploadFile) -> str:
    file_content = file.file.read()
    sha256_hash = hashlib.sha256(file_content).hexdigest()
    image_path = images / f"{sha256_hash}.jpg"
    
    with open(image_path, "wb") as f:
        f.write(file_content)
    
    return f"{sha256_hash}.jpg"

def get_db():
    if not db.exists():
        yield

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()


# STEP 5-1: set up the database connection
def setup_database():
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class HelloResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


class AddItemResponse(BaseModel):
    message: str


# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    image: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not category:
        raise HTTPException(status_code=400, detail="category is required")
    #if not image:
        #raise HTTPException(status_code=400, detail="image is required")

    image_name = save_image(image)

    insert_item(Item(name=name, category=category, image_name=image_name))
    return AddItemResponse(**{"message": f"item received: {name}"})


# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)


class Item(BaseModel):
    name: str
    category: str
    image_name: str


def insert_item(item: Item):
    # items.json が存在するなら既存データを読み込む
    if items_file.exists():
        with open(items_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
    else:
        data = {"items": []}

    data['items'].append(item.dict())

    # 更新されたデータをitems.json に書き込む
    with open(items_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print(f"Item added: {item.name}")


@app.get("/items")
def get_items():
    if not items_file.exists():
        raise HTTPException(status_code=404, detail="No items found")
    else:
        with open(items_file, 'r', encoding='utf-8') as file:
            data = json.load(file)    
        return {"items": data["items"]}

@app.get("/items/{items_id}")
def get_one_item(items_id: int):
    if not items_file.exists():
        raise HTTPException(status_code=404, detail="No items found")
    else:
        with open(items_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        items_id -= 1
        
        # items_id を整数に変換して、リストのインデックスとしてアクセス
        if items_id < 0 or items_id >= len(data["items"]):
            raise HTTPException(status_code=404, detail="Item not found")
        
        return data["items"][items_id] 