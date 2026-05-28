from langchain_tavily import TavilySearch
from config import settings
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

os.environ["TAVILY_API_KEY"] = settings.tavily_api_key

search_tool = TavilySearch(max_results=2)

async def get_grounding_data(recipe_title: str) -> dict:
    """Fetch grounding data in parallel before LLM call."""
    logger.info(f"🔎 Fetching grounding data for: {recipe_title}")
    grounding = {}

    if not recipe_title:
        logger.warning(f"⚠️ No recipe title provided for grounding")
        return grounding

    tasks = {
        "nutrition": search_tool.ainvoke({
            "query": f"{recipe_title} recipe nutrition facts calories protein carbs fat per serving"
        }),
        "cuisine": search_tool.ainvoke({
            "query": f"what cuisine is {recipe_title} origin type"
        }),
        "times": search_tool.ainvoke({
            "query": f"{recipe_title} recipe prep time cook time total time"
        })
    }

    try:
        logger.debug(f"📊 Running 3 parallel grounding searches")
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        keyed = dict(zip(tasks.keys(), results))

        for key, val in keyed.items():
            if not isinstance(val, Exception):
                print(f"\n[Tavily] {key} results:")
                if isinstance(val, dict) and "results" in val:
                    for r in val["results"]:
                        print(f"  URL: {r.get('url')}")
                        print(f"  Content: {r.get('content', '')[:150]}")
            else:
                print(f"[Tavily] {key} failed: {val}")

        if not isinstance(keyed.get("nutrition"), Exception):
            nutrition = _parse_nutrition_from_results(keyed["nutrition"])
            if nutrition:
                grounding["nutrition"] = nutrition
                logger.debug(f"✅ Nutrition data found: {nutrition}")

        if not isinstance(keyed.get("cuisine"), Exception):
            cuisine = _parse_cuisine_from_results(keyed["cuisine"], recipe_title)
            if cuisine:
                grounding["cuisine"] = cuisine
                logger.debug(f"✅ Cuisine data found: {cuisine}")

        if not isinstance(keyed.get("times"), Exception):
            times = _parse_times_from_results(keyed["times"])
            if times:
                grounding.update(times)
                logger.debug(f"✅ Time data found: {times}")

        logger.info(f"✅ Grounding data collected: {len(grounding)} fields")
    except Exception as e:
        logger.warning(f"⚠️ Error collecting grounding data: {str(e)}")

    return grounding


def _parse_nutrition_from_results(results) -> dict:
    import re

    content = ""
    if isinstance(results, dict) and "results" in results:
        for r in results["results"]:
            content += r.get("content", "") + " "
    else:
        content = str(results)

    nutrition = {}

    cal_match = re.search(
        r'(\d+)\s*calories|calories[:\s]+(\d+)|(\d+)\s*kcal',
        content, re.IGNORECASE
    )
    if cal_match:
        nutrition["calories"] = int(
            cal_match.group(1) or cal_match.group(2) or cal_match.group(3)
        )

    protein_match = re.search(
        r'(\d+\.?\d*)\s*g\s*protein|protein[:\s]+(\d+\.?\d*)\s*g',
        content, re.IGNORECASE
    )
    if protein_match:
        nutrition["protein"] = f"{protein_match.group(1) or protein_match.group(2)}g"
    else:
        pct_match = re.search(r'(\d+)%\s*protein', content, re.IGNORECASE)
        if pct_match and nutrition.get("calories"):
            grams = round((int(pct_match.group(1)) / 100) * nutrition["calories"] / 4)
            nutrition["protein"] = f"{grams}g"

    carb_match = re.search(
        r'(\d+\.?\d*)\s*g\s*carb|carb(?:ohydrate)?s?[:\s;]+(\d+\.?\d*)\s*g',
        content, re.IGNORECASE
    )
    if carb_match:
        nutrition["carbs"] = f"{carb_match.group(1) or carb_match.group(2)}g"
    else:
        pct_match = re.search(r'(\d+)%\s*carb', content, re.IGNORECASE)
        if pct_match and nutrition.get("calories"):
            grams = round((int(pct_match.group(1)) / 100) * nutrition["calories"] / 4)
            nutrition["carbs"] = f"{grams}g"

    fat_match = re.search(
        r'(\d+\.?\d*)\s*g\s*fat|(?<!\w)fat[:\s;]+(\d+\.?\d*)\s*g',
        content, re.IGNORECASE
    )
    if fat_match:
        nutrition["fat"] = f"{fat_match.group(1) or fat_match.group(2)}g"
    else:
        pct_match = re.search(r'(\d+)%\s*fat', content, re.IGNORECASE)
        if pct_match and nutrition.get("calories"):
            grams = round((int(pct_match.group(1)) / 100) * nutrition["calories"] / 9)
            nutrition["fat"] = f"{grams}g"

    return nutrition if len(nutrition) >= 2 else {}


def _parse_cuisine_from_results(results, title: str) -> str:
    content = ""
    if isinstance(results, dict) and "results" in results:
        for r in results["results"]:
            content += r.get("content", "") + " "
    else:
        content = str(results)

    content = content.lower()

    cuisines = [
        "italian", "mexican", "chinese", "japanese", "indian", "french",
        "american", "mediterranean", "thai", "greek", "spanish", "korean",
        "vietnamese", "middle eastern", "british", "german", "tex-mex",
        "southwest", "cajun", "creole", "fusion", "latin", "caribbean",
        "moroccan", "turkish", "persian", "lebanese", "filipino"
    ]

    for cuisine in cuisines:
        if cuisine in content:
            return cuisine.title()

    return ""


def _parse_times_from_results(results) -> dict:
    import re
    content = ""
    if isinstance(results, dict) and "results" in results:
        for r in results["results"]:
            content += r.get("content", "") + " "
    else:
        content = str(results)

    times = {}

    prep_match = re.search(
        r'prep(?:aration)?\s*time[:\s]+(\d+\s*(?:min|minute|hour|hr)s?)',
        content, re.IGNORECASE
    )
    if prep_match:
        times["prep_time"] = prep_match.group(1)

    cook_match = re.search(
        r'cook(?:ing)?\s*time[:\s]+(\d+\s*(?:min|minute|hour|hr)s?)',
        content, re.IGNORECASE
    )
    if cook_match:
        times["cook_time"] = cook_match.group(1)

    total_match = re.search(
        r'total\s*time[:\s]+(\d+\s*(?:min|minute|hour|hr)s?)',
        content, re.IGNORECASE
    )
    if total_match:
        times["total_time"] = total_match.group(1)

    return times