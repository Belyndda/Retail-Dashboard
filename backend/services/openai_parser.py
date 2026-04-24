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
                "content": (
                    "Extract retail product data from messy text. "
                    "Return only valid JSON matching the schema."
                ),
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
    parsed["raw_json"] = {"original_text": raw_text}
    return parsed