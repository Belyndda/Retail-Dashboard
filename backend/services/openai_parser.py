import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_product_text(raw_text: str) -> dict:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": """
You are a retail product data cleaning assistant.

Extract ONE product offer from messy text.

Return only valid JSON matching the schema.

Rules:
- Complete obvious partial retail names.
- Fix spacing and typos.
- Example: "CanonG7X" should become "Canon PowerShot G7 X".
- Example: "IPhone 16 Pro Max" should become "iPhone 16 Pro Max".
- Do not duplicate the brand inside product_name.
- product_name should be the clean product name without brand repeated.
- normalized_name should be lowercase and searchable.
- For Apple products, brand must be "Apple", not "iPhone".
- For Canon G7X, brand must be "Canon".
- Ignore used, refurbished, renewed, pre-owned, or open-box wording.
- Convert prices like "1k" to 1000.
- Convert "$300" to 300.
- Extract quantity when mentioned.
- If no quantity is mentioned, use 1.
- If no unit is mentioned, use "each".
- Use null when unknown.
"""
            },
            {
                "role": "user",
                "content": raw_text,
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "product_extract",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "brand": {"type": ["string", "null"]},
                        "product_name": {"type": "string"},
                        "normalized_name": {"type": ["string", "null"]},
                        "size": {"type": ["string", "null"]},
                        "price": {"type": ["number", "null"]},
                        "quantity": {"type": ["integer", "null"]},
                        "unit": {"type": ["string", "null"]}
                    },
                    "required": [
                        "brand",
                        "product_name",
                        "normalized_name",
                        "size",
                        "price",
                        "quantity",
                        "unit"
                    ]
                },
                "strict": True
            }
        }
    )

    parsed = json.loads(response.output_text)

    if not parsed.get("quantity"):
        parsed["quantity"] = 1

    if not parsed.get("unit"):
        parsed["unit"] = "each"

    if parsed.get("product_name"):
        parsed["product_name"] = parsed["product_name"].strip()

    if parsed.get("brand"):
        parsed["brand"] = parsed["brand"].strip()

    if not parsed.get("normalized_name") and parsed.get("product_name"):
        parsed["normalized_name"] = parsed["product_name"].lower().strip()

    parsed["raw_json"] = {"original_text": raw_text}

    return parsed


