import csv
import io
import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File,Form, HTTPException

load_dotenv()

from fastapi.responses import JSONResponse

SHOP_NAME = os.getenv("SHOP_NAME")
API_KEY = os.getenv("SHOPIFY_API_KEY")
PASSWORD = os.getenv("SHOPIFY_API_PASSWORD")
API_VERSION = "2023-10"

HEADERS = {
    "Content-Type": "application/json"
}

BASE_URL = f"https://{API_KEY}:{PASSWORD}@{SHOP_NAME}/admin/api/{API_VERSION}"

app = FastAPI()

def get_variant_id_by_sku(sku: str):
    url = f"https://{SHOP_NAME}/admin/api/{API_VERSION}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": PASSWORD
    }
    query = """
    query ($sku: String!) {
      productVariants(first: 1, query: $sku) {
        edges {
          node {
            id
            sku
            title
            product {
              title
            }
          }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {
            "sku": f"sku:{sku}"
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        return None

    data = response.json()
    try:
        node = data["data"]["productVariants"]["edges"][0]["node"]
        variant_gid = node["id"]
        variant_id = variant_gid.split("/")[-1]
        return {
            "variant_id": variant_id,
            "title": node["title"],
            "product_title": node["product"]["title"]
        }
    except (IndexError, KeyError):
        return None

@app.post("/api/py/reserve_stock")
async def reserve_stock(
    file: UploadFile = File(...),
    password: str = Form(...)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    if password != os.getenv("PASSWORD"):
        raise HTTPException(status_code=403, detail="Invalid password")
    contents = await file.read()
    csvfile = io.StringIO(contents.decode("utf-8"))
    reader = csv.DictReader(csvfile)

    line_items = []

    for row in reader:
        sku = row.get("SKU", "").strip()
        qty = int(row.get("Unavailable") or 0)

        if not sku or qty <= 0:
            continue

        variant_data = get_variant_id_by_sku(sku)
        if not variant_data:
            continue

        line_items.append({
            "variant_id": variant_data["variant_id"],
            "quantity": qty,
            "title": row.get("Title", "").strip(),
            "sku": sku
        })

    if not line_items:
        return JSONResponse(status_code=400, content={"message": "No valid items to reserve."})

    payload = {
        "draft_order": {
            "note": "Monkey Deal",
            "tags": "Internal, Monkey Deal",
            "line_items": line_items,
            "use_customer_default_address": True,
            "customer": {
                "first_name": "Monkey",
                "last_name": "Deal",
                "email": "monkey@deal.com"
            }
        }
    }

    url = f"{BASE_URL}/draft_orders.json"
    response = requests.post(url, json=payload, headers=HEADERS)

    if response.ok:
        draft_order = response.json().get("draft_order", {})
        return {
            "message": "Draft order created successfully.",
            "order_name": draft_order.get("name"),
            "admin_url": f"https://{SHOP_NAME}/admin/draft_orders/{draft_order.get('id')}"
        }
    else:
        return JSONResponse(status_code=500, content={"error": response.json()})

@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}