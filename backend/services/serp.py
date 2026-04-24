import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

BAD_WORDS = [
    "refurb", "refurbished", "renewed", "open box", "open-box",
    "used", "pre-owned", "second hand", "b-stock", "grade",
    "remanufactured", "seller refurbished",
]

ACCESSORY_WORDS = [
    "case", "bag", "charger", "battery", "strap", "screen protector",
    "lens cap", "tripod", "mount", "cover", "cable", "adapter",
    "skin", "protector", "accessory", "replacement", "parts",
]


def extract_price(result: dict):
    price = result.get("extracted_price")

    if isinstance(price, (int, float)):
        return float(price)

    price_text = str(result.get("price") or "")
    cleaned = (
        price_text
        .replace("USD", "")
        .replace("$", "")
        .replace(",", "")
        .replace("/month", "")
        .replace("Delivered", "")
        .strip()
    )

    try:
        return float(cleaned)
    except ValueError:
        return None


def build_query(product: dict) -> str:
    brand = str(product.get("brand") or "").strip()
    name = str(product.get("product_name") or product.get("normalized_name") or "").strip()
    size = str(product.get("size") or "").strip()
    unit = str(product.get("unit") or "").strip()

    if brand and brand.lower() in name.lower():
        query = name
    else:
        query = f"{brand} {name}".strip()

    if size:
        query += f" {size}"

    if unit and unit.lower() not in ["each", "piece", "pieces", "unit", "units"]:
        query += f" {unit}"

    return query.strip()


def get_name_tokens(product: dict):
    product_name = str(
        product.get("product_name")
        or product.get("normalized_name")
        or ""
    ).lower()

    ignore_tokens = {
        "camera", "cameras", "each", "piece", "pieces",
        "unit", "units", "pack", "packs", "the", "and",
    }

    tokens = (
        product_name
        .replace("-", " ")
        .replace("/", " ")
        .replace(",", " ")
        .split()
    )

    return [
        token for token in tokens
        if len(token) > 2 and token not in ignore_tokens
    ]


def find_cheapest_retail_result(product: dict):
    if not SERPAPI_KEY:
        return {
            "competitor_price": None,
            "competitor_url": None,
            "serp_status": "missing_key"
        }

    query = build_query(product)
    print("SERP QUERY:", query)

    if not query:
        return {
            "competitor_price": None,
            "competitor_url": None,
            "serp_status": "no_query"
        }

    params = {
        "engine": "google_shopping",
        "q": query,
        "tbs": "vw:l,mr:1,new:1",
        "api_key": SERPAPI_KEY,
        "num": 20,
    }

    response = requests.get(
        "https://serpapi.com/search.json",
        params=params,
        timeout=20,
    )

    print("SERP STATUS CODE:", response.status_code)

    data = response.json()

    if "error" in data:
        print("SERP API ERROR:", data["error"])
        return {
            "competitor_price": None,
            "competitor_url": None,
            "serp_status": "api_error"
        }

    results = data.get("shopping_results", [])
    print("SERP RESULTS COUNT:", len(results))

    brand = str(product.get("brand") or "").lower()
    tokens = get_name_tokens(product)

    try:
        your_price = float(product.get("price")) if product.get("price") is not None else None
    except Exception:
        your_price = None

    eligible = []

    for result in results:
        title = str(result.get("title") or "").lower()
        source = str(result.get("source") or result.get("store") or "").lower()
        link = (
        result.get("direct_link")
            or result.get("merchant_link")
            or result.get("seller_link")
            or result.get("source_link")
            or result.get("link")
            or result.get("product_link")
            or ""
        )

        results = data.get("shopping_results", [])
        if results:
            print("FIRST RAW SERP RESULT:", results[0])
        print("SERP RESULTS COUNT:", len(results))

        if results:
            print("FIRST SERP RESULT:", results[0])

        combined_text = f"{title} {source} {link}".lower()

        if any(word in combined_text for word in BAD_WORDS):
            continue

        if any(word in title for word in ACCESSORY_WORDS):
            continue

        if brand and brand not in title:
            continue

        matched_tokens = [token for token in tokens if token in title]

        if tokens and len(matched_tokens) < max(1, len(tokens) // 2):
            continue

        price = extract_price(result)

        if price is None:
            continue

        if your_price and price < your_price * 0.25:
            continue

        if not link:
            continue

        eligible.append({
            "store": result.get("source") or result.get("store"),
            "price": price,
            "url": link,
            "title": result.get("title"),
        })

    print("ELIGIBLE RESULTS:", eligible)

    if not eligible:
        return {
            "competitor_price": None,
            "competitor_url": None,
            "serp_status": "no_clean_results"
        }

    best = sorted(eligible, key=lambda x: x["price"])[0]

    return {
        "competitor_price": best["price"],
        "competitor_url": best["url"],
        "serp_status": "done"
    }