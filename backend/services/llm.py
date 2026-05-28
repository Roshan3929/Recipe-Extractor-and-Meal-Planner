import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pathlib import Path
from config import settings
import logging
import re

logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    google_api_key=settings.gemini_api_key,
    temperature=settings.llm_temperature,
    max_output_tokens=settings.max_output_tokens,
)

prompt_path = Path(__file__).parent.parent / "prompts" / "recipe_extract.txt"
prompt_template = prompt_path.read_text()

recipe_prompt = PromptTemplate(
    input_variables=["scraped_text", "grounding_data"],
    template=prompt_template
)

recipe_chain = recipe_prompt | llm

REQUIRED_FIELDS = ["title", "ingredients", "instructions"]

async def extract_recipe(scraped_text: str, grounding_data: dict = None) -> dict:
    try:
        grounding_str = json.dumps(grounding_data, indent=2) if grounding_data else "No grounding data available."
        result = await recipe_chain.ainvoke({
            "scraped_text": scraped_text,
            "grounding_data": grounding_str
        })
        
        # handle content being a list or string
        content = result.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        
        clean = content.strip().replace("```json", "").replace("```", "").strip()

        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("LLM did not return a JSON object")
        clean = clean[start:end]

        data = json.loads(clean)
        data = _validate_recipe_data(data)
        data = _clean_recipe_data(data)
        return data

    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {str(e)}")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"LLM call failed: {str(e)}")

def _clean_time(value: str) -> str:
    """Convert ISO 8601 duration to readable format. PT20M -> 20 mins, PT1H30M -> 1 hr 30 mins"""
    if not value or not isinstance(value, str):
        return value
    
    if not value.startswith("PT"):
        return value
    
    hours = re.search(r'(\d+)H', value)
    minutes = re.search(r'(\d+)M', value)
    
    parts = []
    if hours:
        h = int(hours.group(1))
        parts.append(f"{h} hr{'s' if h > 1 else ''}")
    if minutes:
        m = int(minutes.group(1))
        parts.append(f"{m} min{'s' if m > 1 else ''}")
    
    return " ".join(parts) if parts else value


def _clean_recipe_data(data: dict) -> dict:
    """Post-process LLM output to fix common format issues."""
    for field in ["prep_time", "cook_time", "total_time"]:
        if data.get(field):
            data[field] = _clean_time(data[field])
    return data


def _validate_recipe_data(data: dict) -> dict:
    """Validate LLM output has minimum required fields."""
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"LLM response missing required field: {field}")

    # ensure ingredients are properly structured
    ingredients = data.get("ingredients") or []
    if isinstance(ingredients, list):
        cleaned = []
        for ing in ingredients:
            if isinstance(ing, dict):
                cleaned.append(ing)
            elif isinstance(ing, str):
                # handle case where LLM returns strings instead of dicts
                cleaned.append({"quantity": "", "unit": "", "item": ing})
        data["ingredients"] = cleaned

    # ensure instructions are properly structured
    instructions = data.get("instructions") or []
    if isinstance(instructions, list):
        cleaned = []
        for i, ins in enumerate(instructions):
            if isinstance(ins, dict):
                cleaned.append(ins)
            elif isinstance(ins, str):
                cleaned.append({"step_number": i + 1, "instruction_text": ins})
        data["instructions"] = cleaned

    # ensure difficulty is valid
    if data.get("difficulty") not in ["easy", "medium", "hard"]:
        data["difficulty"] = "medium"

    # ensure shopping_list is a dict
    if not isinstance(data.get("shopping_list"), dict):
        data["shopping_list"] = {}

    # ensure substitutions is a list
    if not isinstance(data.get("substitutions"), list):
        data["substitutions"] = []

    # ensure related_recipes is a list
    if not isinstance(data.get("related_recipes"), list):
        data["related_recipes"] = []

    return data