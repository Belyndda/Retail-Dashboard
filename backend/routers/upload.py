from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.supabase_client import supabase
import re

router = APIRouter(prefix="/upload", tags=["upload"])


class TextUploadRequest(BaseModel):
    raw_text: str
    user_id: str | None = None


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


def extract_product_from_text(raw_text: str) -> dict:
    text = raw_text.strip()

    # Only capture price when prefixed with $
    price_match = re.search(r"\$(\d+(?:\.\d{1,2})?)", text)
    price = float(price_match.group(1)) if price_match else None

    brand = None
    for candidate in ["Nike", "Adidas", "Puma", "Jordan", "New Balance"]:
        if candidate.lower() in text.lower():
            brand = candidate
            break

    size_match = re.search(r"size\s*([A-Za-z0-9\.]+)", text, re.IGNORECASE)
    size = size_match.group(1) if size_match else None

    quantity_match = re.search(r"\bqty\s*(\d+)\b|\bquantity\s*(\d+)\b", text, re.IGNORECASE)
    quantity = None
    if quantity_match:
        quantity = int(quantity_match.group(1) or quantity_match.group(2))

    product_name = text

    if brand:
        product_name = re.sub(brand, "", product_name, flags=re.IGNORECASE).strip(" -,")

    if size:
        product_name = re.sub(
            rf"size\s*{re.escape(size)}",
            "",
            product_name,
            flags=re.IGNORECASE
        ).strip(" -,")

    if price is not None:
        product_name = re.sub(r"\$\d+(?:\.\d{1,2})?", "", product_name).strip(" -,")

    if quantity is not None:
        product_name = re.sub(
            r"\bqty\s*\d+\b|\bquantity\s*\d+\b",
            "",
            product_name,
            flags=re.IGNORECASE
        ).strip(" -,")

    product_name = re.sub(r"\s+", " ", product_name).strip(" -,")
    if not product_name:
        product_name = text

    return {
        "brand": brand,
        "product_name": product_name,
        "normalized_name": normalize_name(product_name),
        "size": size,
        "price": price,
        "quantity": quantity,
        "unit": None,
        "raw_json": {
            "original_text": raw_text
        }
    }


@router.post("/text")
def upload_text(payload: TextUploadRequest):
    try:
        upload_result = supabase.table("uploads").insert({
            "user_id": payload.user_id,
            "source_type": "text",
            "raw_text": payload.raw_text,
            "status": "processing"
        }).execute()

        if not upload_result.data:
            raise HTTPException(status_code=500, detail="Failed to create upload row")

        upload_id = upload_result.data[0]["id"]

        product = extract_product_from_text(payload.raw_text)

        product_result = supabase.table("products").insert({
            "upload_id": upload_id,
            "brand": product["brand"],
            "product_name": product["product_name"],
            "normalized_name": product["normalized_name"],
            "size": product["size"],
            "price": product["price"],
            "quantity": product["quantity"],
            "unit": product["unit"],
            "raw_json": product["raw_json"]
        }).execute()

        supabase.table("uploads").update({
            "status": "done"
        }).eq("id", upload_id).execute()

        return {
            "success": True,
            "upload_id": upload_id,
            "product": product_result.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))