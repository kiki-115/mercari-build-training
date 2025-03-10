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
#items_file = pathlib.Path(__file__).parent.resolve() / 'items.json'

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

def insert_item(name: str, category: str, image_name: str, db: sqlite3.Connection):
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO items (name, category, image_name)
        VALUES (?, ?, ?)
    ''', (name, category, image_name))
    db.commit()


def get_all_items(db: sqlite3.Connection):
    cursor = db.cursor()
    cursor.execute('SELECT * FROM items')
    rows = cursor.fetchall()
    return rows

@app.get("/items")
def get_items(db: sqlite3.Connection = Depends(get_db)):
    items = get_all_items(db)
    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    return {"items": [dict(item) for item in items]}  # データベースの行を辞書形式に変換して返す


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

    insert_item(name, category, image_name, db)
    return AddItemResponse(**{"message": f"item received: {name}"})

    
@app.get("/items/{items_id}")
def get_one_item(items_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # items_id を使って、商品を取得するSQLクエリを実行
    cursor.execute('SELECT * FROM items WHERE id = ?', (items_id,))
    item = cursor.fetchone()  # 1件の結果を取得

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # item は sqlite3.Row 型のオブジェクトなので、辞書形式に変換して返す
    return dict(item)

@app.get("/search")
def search_items(keyword: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()

    # キーワードを含む商品を検索する SQL クエリ
    cursor.execute('SELECT * FROM items WHERE name LIKE ?', ('%' + keyword + '%',))
    items = cursor.fetchall()

    if not items:
        raise HTTPException(status_code=404, detail="No items found matching the keyword")

    # 検索結果を辞書形式に変換して返す
    result = [{"name": item["name"], "category": item["category"], "image_name": item["image_name"]} for item in items]
    return {"items": result}
