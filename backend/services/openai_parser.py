from typing import List, Dict
import re


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


def extract_products_from_text(raw_text: str) -> List[Dict]:
    """
    Temporary MVP parser.
    Later replace with OpenAI structured output.
    """
    text = raw_text.strip()

    price_match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", text)
    price = float(price_match.group(1)) if price_match else None

    quantity_match = re.search(r"\b(\d+)\b", text)
    quantity = int(quantity_match.group(1)) if quantity_match else None

    brand = None
    for candidate in ["Nike", "Adidas", "Puma", "Jordan", "New Balance"]:
        if candidate.lower() in text.lower():
            brand = candidate
            break

    product_name = text
    if brand:
        product_name = re.sub(brand, "", product_name, flags=re.IGNORECASE).strip(" -,")

    item = {
        "brand": brand,
        "product_name": product_name or text,
        "normalized_name": normalize_name(product_name or text),
        "size": None,
        "price": price,
        "quantity": quantity,
        "unit": None,
        "raw_json": {"source_text": raw_text},
    }

    return [item]