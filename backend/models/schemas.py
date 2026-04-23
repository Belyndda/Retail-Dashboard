from pydantic import BaseModel
from typing import Optional, List, Any


class TextUploadRequest(BaseModel):
    raw_text: str
    user_id: Optional[str] = None


class ProductItem(BaseModel):
    brand: Optional[str] = None
    product_name: str
    normalized_name: Optional[str] = None
    size: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    raw_json: Optional[Any] = None


class ProcessResponse(BaseModel):
    upload_id: str
    products_inserted: int
    products: List[ProductItem]