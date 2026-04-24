from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.supabase_client import supabase
from services.openai_parser import parse_product_text
from services.serp import find_cheapest_retail_result

router = APIRouter(prefix="/upload", tags=["upload"])


class TextUploadRequest(BaseModel):
    raw_text: str
    user_id: str | None = None


@router.post("/text")
def upload_text(payload: TextUploadRequest):
    upload_id = None
    product_id = None

    try:
        safe_user_id = None if payload.user_id in [None, "", "NULL", "null"] else payload.user_id

        upload_result = supabase.table("uploads").insert({
            "user_id": safe_user_id,
            "source_type": "text",
            "raw_text": payload.raw_text,
            "status": "processing"
        }).execute()

        if not upload_result.data:
            raise HTTPException(status_code=500, detail="Failed to create upload row")

        upload_id = upload_result.data[0]["id"]

        product = parse_product_text(payload.raw_text)

        product_result = supabase.table("products").insert({
            "upload_id": upload_id,
            "brand": product.get("brand"),
            "product_name": product.get("product_name"),
            "normalized_name": product.get("normalized_name"),
            "size": product.get("size"),
            "price": product.get("price"),
            "quantity": product.get("quantity"),
            "unit": product.get("unit"),
            "raw_json": product.get("raw_json"),
            "serp_status": "pending"
        }).execute()

        if not product_result.data:
            raise HTTPException(status_code=500, detail="Failed to create product row")

        product_row = product_result.data[0]
        product_id = product_row["id"]

        print("RUNNING SERP FOR:", product)

        try:
            serp_result = find_cheapest_retail_result(product)
            print("SERP RESULT:", serp_result)

            update_result = supabase.table("products").update({
                "competitor_price": serp_result.get("competitor_price"),
                "competitor_url": serp_result.get("competitor_url"),
                "serp_status": serp_result.get("serp_status", "done")
            }).eq("id", product_id).execute()

            if update_result.data:
                product_row = update_result.data[0]

        except Exception as serp_error:
            print("SERP ERROR:", serp_error)

            update_result = supabase.table("products").update({
                "serp_status": "error"
            }).eq("id", product_id).execute()

            if update_result.data:
                product_row = update_result.data[0]

        supabase.table("uploads").update({
            "status": "done",
            "error_msg": None
        }).eq("id", upload_id).execute()

        return {
            "success": True,
            "upload_id": upload_id,
            "product": product_row
        }

    except Exception as e:
        print("UPLOAD ERROR:", e)

        if upload_id:
            try:
                supabase.table("uploads").update({
                    "status": "error",
                    "error_msg": str(e)
                }).eq("id", upload_id).execute()
            except Exception:
                pass

        raise HTTPException(status_code=500, detail=str(e))