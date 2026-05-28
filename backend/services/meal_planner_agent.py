import json
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from config import settings
from database import SessionLocal
import models
import logging

logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    google_api_key=settings.gemini_api_key,
    temperature=0.1
)

# --- Tools ---

@tool
def fetch_recipe_ingredients(recipe_ids: str) -> str:
    """
    Fetch ingredients for a list of recipe IDs from the database.
    Input: comma-separated recipe IDs e.g. '1,2,3'
    Output: JSON list of ingredients with recipe title, quantity, unit, item
    """
    db = SessionLocal()
    try:
        ids = [int(id.strip()) for id in recipe_ids.split(",")]
        result = []
        for recipe_id in ids:
            recipe = db.query(models.Recipe).filter_by(id=recipe_id).first()
            if not recipe:
                continue
            ingredients = db.query(models.Ingredient).filter_by(
                recipe_id=recipe_id
            ).all()
            for ing in ingredients:
                result.append({
                    "recipe_title": recipe.title,
                    "recipe_id": recipe_id,
                    "quantity": ing.quantity or "",
                    "unit": ing.unit or "",
                    "item": ing.item or ""
                })
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@tool
def merge_quantities(ingredients_json: str) -> str:
    """
    Merge duplicate ingredients across recipes by combining quantities.
    Input: JSON string of ingredients list from fetch_recipe_ingredients
    Output: JSON list of merged ingredients
    """
    try:
        ingredients = json.loads(ingredients_json)
        merged = {}

        for ing in ingredients:
            item = ing.get("item", "").lower().strip()
            unit = ing.get("unit", "").lower().strip()
            quantity_str = ing.get("quantity", "").strip()

            quantity, quantity_label = _parse_quantity(quantity_str)
            key = f"{item}|{unit}"

            if key in merged:
                if quantity > 0:
                    merged[key]["quantity"] += quantity
                merged[key]["recipes"].append(ing.get("recipe_title", ""))
                # keep non-numeric label if no numeric quantity exists
                if not merged[key]["has_numeric"] and quantity_label:
                    merged[key]["quantity_label"] = quantity_label
                if quantity > 0:
                    merged[key]["has_numeric"] = True
            else:
                merged[key] = {
                    "item": ing.get("item", ""),
                    "unit": ing.get("unit", ""),
                    "quantity": quantity,
                    "quantity_label": quantity_label,
                    "has_numeric": quantity > 0,
                    "recipes": [ing.get("recipe_title", "")]
                }

        result = []
        for val in merged.values():
            qty = val["quantity"]

            # format display quantity
            if val["has_numeric"]:
                qty_str = str(int(qty)) if qty == int(qty) else str(round(qty, 2))
            elif val["quantity_label"]:
                # use the original label e.g. "to taste", "a pinch"
                qty_str = val["quantity_label"]
            else:
                qty_str = "as needed"

            result.append({
                "item": val["item"],
                "unit": val["unit"],
                "quantity": qty_str,
                "recipes": list(set(val["recipes"]))
            })

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})

def _parse_quantity(quantity_str: str) -> tuple[float, str]:
    """
    Parse a quantity string into a numeric value and a display label.
    Returns (numeric_value, original_label)
    numeric_value is 0 if not parseable
    """
    if not quantity_str:
        return 0, ""

    q = quantity_str.strip().lower()

    # handle non-numeric labels — return 0 and keep original
    non_numeric = [
        "to taste", "as needed", "a pinch", "pinch", "dash",
        "handful", "a handful", "some", "optional", "garnish",
        "a few", "few", "splash", "drizzle"
    ]
    if any(label in q for label in non_numeric):
        return 0, quantity_str

    # handle fractions e.g. "1/2", "3/4"
    try:
        if "/" in q:
            parts = q.split("/")
            return float(parts[0]) / float(parts[1]), ""
    except (ValueError, ZeroDivisionError):
        pass

    # handle mixed numbers e.g. "1 1/2"
    try:
        parts = q.split()
        if len(parts) == 2 and "/" in parts[1]:
            whole = float(parts[0])
            frac_parts = parts[1].split("/")
            frac = float(frac_parts[0]) / float(frac_parts[1])
            return whole + frac, ""
    except (ValueError, ZeroDivisionError):
        pass

    # handle ranges e.g. "2-3" — take the lower bound
    try:
        if "-" in q:
            return float(q.split("-")[0].strip()), ""
    except ValueError:
        pass

    # plain number
    try:
        return float(q), ""
    except ValueError:
        # anything else — keep as label
        return 0, quantity_str


@tool
def group_by_category(ingredients_json: str) -> str:
    """
    Group merged ingredients by shopping category.
    Input: JSON string of merged ingredients
    Output: JSON object grouped by category
    """
    try:
        ingredients = json.loads(ingredients_json)

        categories = {
            "produce": [
                "onion", "garlic", "tomato", "lemon", "lime",
                "carrot", "celery", "potato", "mushroom", "spinach",
                "lettuce", "cucumber", "zucchini", "apple", "banana",
                "basil", "parsley", "cilantro", "ginger", "jalapeno",
                "avocado", "broccoli", "corn", "pepper"
            ],
            "dairy": [
                "butter", "milk", "cream", "cheese", "yogurt",
                "egg", "eggs", "mozzarella", "parmesan", "cheddar",
                "sour cream", "cream cheese"
            ],
            "meat": [
                "chicken", "beef", "pork", "lamb", "turkey", "bacon",
                "sausage", "shrimp", "salmon", "tuna", "fish"
            ],
            "bakery": [
                "bread", "flour", "baguette", "roll", "pita",
                "tortilla", "wrap", "bun"
            ],
            "pantry": [
                "oil", "olive oil", "vinegar", "sugar", "salt",
                "broth", "stock", "sauce", "pasta", "rice",
                "tomato paste", "honey", "coconut milk", "soy sauce"
            ],
            "spices": [
                "pepper", "cumin", "paprika", "oregano", "thyme",
                "rosemary", "cinnamon", "turmeric", "chili", "cayenne",
                "bay leaf", "nutmeg", "coriander"
            ]
        }

        grouped = {}
        for ing in ingredients:
            item_lower = ing.get("item", "").lower()
            assigned = False
            for category, keywords in categories.items():
                if any(kw in item_lower for kw in keywords):
                    grouped.setdefault(category, []).append(ing)
                    assigned = True
                    break
            if not assigned:
                grouped.setdefault("other", []).append(ing)

        return json.dumps(grouped)
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- Tool registry ---
TOOLS = {
    "fetch_recipe_ingredients": fetch_recipe_ingredients,
    "merge_quantities": merge_quantities,
    "group_by_category": group_by_category
}

# bind tools to LLM so it knows what's available
llm_with_tools = llm.bind_tools(list(TOOLS.values()))


async def generate_meal_plan(recipe_ids: list[int]) -> dict:
    try:
        ids_str = ", ".join(str(id) for id in recipe_ids)

        # call tools directly — no LLM overhead for deterministic sequence
        ingredients_json = fetch_recipe_ingredients.invoke(ids_str)
        ingredients_data = json.loads(ingredients_json)
        if "error" in ingredients_data:
            return ingredients_data

        merged_json = merge_quantities.invoke(ingredients_json)
        merged_data = json.loads(merged_json)
        if "error" in merged_data:
            return merged_data

        grouped_json = group_by_category.invoke(merged_json)
        result = json.loads(grouped_json)

        if "error" in result:
            return result

        return result

    except Exception as e:
        return {"error": str(e)}