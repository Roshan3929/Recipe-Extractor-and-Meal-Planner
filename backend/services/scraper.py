import httpx
from bs4 import BeautifulSoup
from config import settings
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


RECIPE_KEYWORDS = [
    "ingredients", "instructions", "prep time", "cook time",
    "servings", "recipe", "tablespoon", "teaspoon", "preheat"
]

_client = httpx.AsyncClient(
    headers=HEADERS,
    timeout=settings.request_timeout,
    follow_redirects=True,
    http2=True  # HTTP/2 for lower latency
)

async def scrape_recipe(url: str) -> str:
    logger.info(f"🔍 Starting recipe scrape for URL: {url}")
    # validate URL format before making any request
    if not url.startswith(("http://", "https://")):
        logger.warning(f"❌ Invalid URL format: {url}")
        raise ValueError("Invalid URL — must start with http:// or https://")

    try:
        
        logger.debug(f"📡 Sending HTTP request to {url}")
        response = await _client.get(url)
        response.raise_for_status()
        logger.info(f"✅ HTTP request successful (status {response.status_code})")

        # check content type — reject PDFs, images, non-HTML
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            logger.warning(f"❌ Invalid content type: {content_type}")
            raise ValueError(f"URL does not point to an HTML page (got {content_type})")

        soup = BeautifulSoup(response.text, "html.parser")
        logger.debug(f"🍜 Parsing HTML content")

        # strategy 1: JSON-LD
        json_ld = _extract_json_ld(soup)
        if json_ld and len(json_ld) > 200:
            logger.info(f"✅ Recipe extraction succeeded via JSON-LD ({len(json_ld)} chars)")
            return json_ld

        # strategy 2: targeted HTML
        logger.debug(f"📋 Trying targeted HTML extraction")
        targeted = _extract_targeted(soup)
        if targeted and len(targeted) > 200:
            text = targeted
            logger.info(f"✅ Recipe extracted via targeted HTML ({len(text)} chars)")
        else:
            # strategy 3: full text fallback
            logger.debug(f"📄 Falling back to full text extraction")
            text = _extract_full_text(soup)
            logger.info(f"✅ Recipe extracted via full text ({len(text)} chars)")

        # reject if page doesn't look like a recipe
        if not _is_recipe_page(text):
            logger.warning(f"❌ Content doesn't appear to be a recipe page")
            raise ValueError(
                "This page does not appear to contain a recipe. "
                "Please provide a direct link to a recipe page."
            )

        logger.info(f"✅ Scraping complete - {len(text)} chars scraped")
        return text[:settings.scrape_char_limit]

    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout after {settings.request_timeout}s")
        raise ValueError(f"Request timed out after {settings.request_timeout}s — the site may be slow or unavailable")
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        logger.error(f"🌐 HTTP Error {status}")
        if status == 404:
            raise ValueError("Recipe page not found (404) — check the URL is correct")
        elif status == 403:
            raise ValueError("Access denied (403) — this site blocks automated requests")
        elif status == 429:
            raise ValueError("Rate limited (429) — too many requests to this site")
        else:
            raise ValueError(f"Failed to fetch page (HTTP {status})")
    except httpx.ConnectError:
        logger.error(f"🔌 Connection error")
        raise ValueError("Could not connect — check the URL or your internet connection")
    except ValueError:
        raise  # re-raise our own errors as-is
    except Exception as e:
        logger.error(f"⚠️ Unexpected scraping error: {str(e)}")
        raise ValueError(f"Unexpected scraping error: {str(e)}")



def _extract_json_ld(soup: BeautifulSoup) -> str:
    """Extract JSON-LD structured recipe data — most accurate when available."""
    import json
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string or "")
            # handle both single object and @graph array
            if isinstance(data, list):
                data = next((d for d in data if d.get("@type") == "Recipe"), None)
            elif data.get("@graph"):
                data = next((d for d in data["@graph"] if d.get("@type") == "Recipe"), None)
            if data and data.get("@type") == "Recipe":
                return json.dumps(data, indent=2)
        except Exception:
            continue
    return ""


def _extract_targeted(soup: BeautifulSoup) -> str:
    """Target recipe-specific HTML sections to reduce noise."""
    sections = []

    # remove noise
    for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "aside"]):
        tag.decompose()

    # look for common recipe section patterns
    for selector in [
        "article", "main", ".recipe", ".recipe-card",
        "#recipe", ".wprm-recipe", ".tasty-recipe",
        "[class*='recipe']", "[id*='recipe']"
    ]:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator="\n", strip=True)
            if len(text) > 100:
                sections.append(text)
                break

    if not sections:
        return ""

    lines = [l for l in sections[0].splitlines() if l.strip()]
    return "\n".join(lines)


def _extract_full_text(soup: BeautifulSoup) -> str:
    """Fallback: clean full page text."""
    for tag in soup(["script", "style", "nav", "footer", "header", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [l for l in text.splitlines() if l.strip()]
    return "\n".join(lines)

def _extract_title_hint(text: str, url: str = "") -> str:
    """Extract a recipe title from scraped text or URL."""
    import re
    import json as json_lib

    # Strategy 1: URL slug — most reliable
    if url:
        url_title = extract_title_from_url(url)
        if url_title and len(url_title.split()) >= 2:
            return url_title

    # Strategy 2: parse JSON-LD
    try:
        data = json_lib.loads(text)
        title = _find_recipe_title(data)
        if title and _is_valid_title(title):
            return title
    except (json_lib.JSONDecodeError, TypeError):
        pass

    # Strategy 3: regex for headline
    for field in ["headline", "title"]:
        match = re.search(rf'"{field}"\s*:\s*"([^"]+)"', text)
        if match and _is_valid_title(match.group(1)):
            return match.group(1)

    return ""

def _find_recipe_title(data) -> str:
    """Recursively find the Recipe type object and return its name."""
    if isinstance(data, dict):
        obj_type = data.get("@type")
        is_recipe = obj_type == "Recipe" or (
            isinstance(obj_type, list) and "Recipe" in obj_type
        )
        if is_recipe:
            name = data.get("name") or data.get("headline") or ""
            print(f"[DEBUG] Found Recipe object, name: '{name}'")
            print(f"[DEBUG] All top-level keys: {list(data.keys())[:10]}")
            return name
        

def _is_valid_title(text: str) -> bool:
    """Check if extracted text actually looks like a recipe title."""
    lower = text.lower()
    bad_patterns = [
        "preparation", "prep time", "cook time", "total time",
        "http", "difficulty", "minute", "hour", "easy", "medium",
        "hard", "calorie", "serving", "yield", "ingredients",
        "instructions", "makes about", "cup", "tbsp", "tsp",
        "tablespoon", "teaspoon", "ounce", "gram", "ml",
        "i used", "optional", "raw ", "fresh ",
        "to taste", "a pinch", "as needed", "salt", "pepper",
        "sugar", "water", "oil", "butter"
    ]
    if any(kw in lower for kw in bad_patterns):
        return False
    
    # reject if it looks like "ingredient - quantity" format
    if " - " in text and any(c.isdigit() for c in text):
        return False
    
    # reject if too short to be a real title
    if len(text.split()) < 2:
        return False
    
    return len(text) < 100



def extract_title_from_url(url: str) -> str:
    """Extract a readable title from the URL slug as final fallback."""
    from urllib.parse import urlparse

    path = urlparse(url).path.strip("/")
    # get the last meaningful segment
    segments = [s for s in path.split("/") if s]
    if not segments:
        return ""

    slug = segments[-1]
    # clean the slug: remove file extensions, IDs
    slug = slug.split(".")[0]  # remove .html etc
    slug = slug.replace("-", " ").replace("_", " ")

    # remove trailing numbers/IDs
    import re
    slug = re.sub(r'\b\d+\b', '', slug).strip()

    # capitalize properly
    title = " ".join(word.capitalize() for word in slug.split())

    return title if len(title) > 3 else ""

def _needs_enrichment(text: str) -> bool:
    """
    Check if JSON-LD has complete data — if so skip Tavily entirely.
    JSON-LD sites like allrecipes, recipetineats have everything already.
    """
    text_lower = text.lower()
    has_nutrition = "calories" in text_lower
    has_time = "cooktime" in text_lower or "totaltime" in text_lower
    has_cuisine = "recipecuisine" in text_lower or "cuisine" in text_lower
    return not (has_nutrition and has_time and has_cuisine)

def _is_recipe_page(text: str) -> bool:
    text_lower = text.lower()
    matches = sum(1 for kw in RECIPE_KEYWORDS if kw in text_lower)
    return matches >= 3

if __name__ == "__main__":
    import asyncio
    text = asyncio.run(scrape_recipe("https://www.mycookingjourney.com/appam-vegetable-stew-kerala/"))
    print(text[:-1])