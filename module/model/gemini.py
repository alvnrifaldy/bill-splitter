import base64
import json
import os
import re
from typing import Dict, Any

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

PROMPT = """
You are given an image of a receipt. Extract all purchase information into the following JSON format:

{
  "items": [
    {
      "name": <item_name>,
      "quantity": <count>,
      "unit_price": <price_per_item>,
      "total_price": <price_per_item * count>
    }
  ],
  "subtotal": <sum of all item total_price before tax>,
  "tax": <tax_value_or_0>,
  "service_charge": <service_value_or_0>,
  "others": <other_additional_fees_if_any_or_0>,
  "total": <grand_total_as_shown_in_receipt>
}

Rules:
- If the receipt shows a single price per item and a quantity, compute unit_price = total_price / quantity.
- Always return strict JSON only, no explanation.
"""

class GeminiModel:
    def __init__(self, api_key: str, model: str = 'gemini-2.5-flash', temperature = 0.0):
        self.llm = ChatGoogleGenerativeAI(model=model, temperature=temperature, google_api_key=api_key)

    def extract(self, image_path: str) -> Dict[str, Any]:
        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')

        data_uri = f"data:image/jpeg;base64,{encoded}"

        message = HumanMessage(content=[
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": data_uri}
        ])

        response = self.llm.invoke([message])

        try:
            text = response.content.strip()
        except:
            text = response.candidates[0].content.parts[0].text.strip()

        print("\n======= RAW GEMINI OUTPUT =======")
        print(text)
        print("=================================\n")

        clean = (
            text.replace('```json', '')
                .replace('```', '')
                .strip()
        )

        print("\n======= CLEANED OUTPUT =======")
        print(clean)
        print("=================================\n")

        match = re.search(r"\{[\s\S]*\}", clean)
        if not match:
            raise ValueError("Model output does not contain valid JSON:\n" + clean)

        json_text = match.group(0).strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            print('\n❌ JSON Decode Error:\n', json_text)
            raise

def normalized_receipt(parsed: dict) -> dict:
    out = {
        'items': [],
        'subtotal': 0,
        'tax': 0,
        'service_charge': 0,
        'others': 0,
        'total': 0
    }
    if 'items' in parsed:
        item_src = parsed ['items']
    elif 'menus' in parsed:
        item_src = parsed['menus']
    else:
        item_src = parsed.get('data') or parsed.get('lines') or []
    for it in item_src:
        name = it.get('name') or it.get('item') or ''
        qty = it.get('quantity') or it.get('qty') or 1
        total_price = it.get('total_price') or it.get('price') or 0
        unit_price = it.get('unit_price') or None
        try: 
            qty = int(qty)
        except:
            qty = 1
        
        try:
            total_price = int(total_price)
        except:
            total_price = 0
        if unit_price is None and qty > 0:
            unit_price = total_price // qty
        out['items'].append({
            'name': name,
            'quantity': qty,
            'unit_price': unit_price,
            'total_price': total_price
        })
        out['subtotal'] += total_price
    out['subtotal'] = parsed.get('subtotal', out['subtotal']) or out['subtotal']
    out['tax'] = parsed.get('tax', 0)
    out['service_charge'] = parsed.get('service_charge', parsed.get('service', 0))
    out['others'] = parsed.get('others', 0)
    out['total'] = parsed.get('total', out['subtotal'] + out['tax'] + out['service_charge'] + out['others'])
    return out