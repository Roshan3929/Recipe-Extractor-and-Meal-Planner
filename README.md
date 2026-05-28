# Recipe Extractor & Meal Planner

A full-stack application that accepts recipe blog URLs and automatically extracts structured recipe data using web scraping and LLM-powered extraction, with a meal planning feature that generates combined shopping lists across multiple recipes.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────────────────────────────────────────────┐
│   React UI  │────▶│                  FastAPI Backend                     │
│  (Vite)     │◀────│                                                      │
└─────────────┘     │  ┌───────────┐  ┌─────────┐  ┌──────────────────┐   │
                    │  │  Scraper  │─▶│   LLM   │─▶│   PostgreSQL     │   │
                    │  │ (BS4 +    │  │(Gemini) │  │  (8 normalized   │   │
                    │  │  JSON-LD) │  │         │  │   tables)        │   │
                    │  └───────────┘  └────┬────┘  └──────────────────┘   │
                    │                      │                               │
                    │               ┌──────┴──────┐                       │
                    │               │   Tavily    │                       │
                    │               │  Grounding  │                       │
                    │               └─────────────┘                       │
                    └──────────────────────────────────────────────────────┘
```

## Core Features

### Tab 1 — Recipe Extraction
- Accepts any recipe blog URL as input
- Scrapes page content using a three-tier strategy (JSON-LD → targeted HTML → full text fallback)
- Extracts structured recipe data via Gemini LLM with a 4-part engineered prompt (Persona, Task, Context, Format)
- Fills missing fields (nutrition, cuisine, cook times) using Tavily web search grounded in trusted sources
- Returns: title, cuisine, prep/cook/total time, servings, difficulty, ingredients (quantity/unit/item), step-by-step instructions, nutritional estimate, 3 substitutions, categorized shopping list, and 3 related recipe suggestions

### Tab 2 — Saved Recipes (History)
- Displays all previously extracted recipes in a sortable table
- Shows title, cuisine, difficulty (color-coded), and extraction date
- "Details" button opens a modal with the full structured recipe card
- Session-based user segregation — each user sees only their own history
- "Clear All" button to reset history for the current session

### Tab 3 — Meal Planner (Optional Feature)
- Select 3–5 saved recipes from history
- Generates a combined shopping list with merged quantities across all selected recipes
- Handles fraction parsing (1/2, 3/4), mixed numbers (1 1/2), and non-numeric quantities ("to taste", "a pinch")
- Groups items by category: produce, dairy, meat, bakery, pantry, spices
- Built using LangChain tool-calling architecture with three composable tools

---

## Technical Decisions & Beyond-Spec Enhancements

### Three-Tier Scraping Strategy
Most recipe sites embed JSON-LD structured data — machine-readable recipe metadata that is far cleaner than raw HTML. The scraper checks for JSON-LD first, then falls back to targeted recipe HTML sections, and finally to full page text extraction. This reduces noise sent to the LLM and improves extraction accuracy significantly.

### Grounded Enrichment via Tavily
Nutritional estimates from LLMs are unreliable — they hallucinate plausible but incorrect values. Instead of relying on the LLM alone, missing nutrition data is fetched from verified sources (MyNetDiary, USDA, Nutritionix) via Tavily search. The same approach applies to cuisine classification and cook times. Grounding data is passed into the LLM prompt as supplementary context so the model can incorporate it without overriding scraped data that already exists.

Tavily enrichment only runs when fields are actually missing (determined by `_get_missing_fields`), and only searches for the specific missing fields — so a recipe with complete JSON-LD triggers zero Tavily calls.

### Prompt Engineering
The extraction prompt follows a 4-part structure:
- **Persona**: Professional chef and culinary data analyst
- **Task**: Extract from scraped text, use grounding data for gaps, reason about difficulty and substitutions
- **Context**: Scraped text + grounding data + explicit rules for difficulty assessment, substitution generation, and shopping list categorization
- **Format**: Strict JSON schema with few-shot examples demonstrating expected output

Key design decisions in the prompt:
- Difficulty is reasoned by the LLM (ingredient count, technique complexity, time, equipment) rather than extracted as a keyword
- Substitutions follow a structured dietary pattern: one dairy-free, one healthier, one pantry-swap
- The prompt explicitly instructs "never hallucinate — return null if unknown and no grounding data available"

### Config-Driven Architecture
All tunable parameters (model name, temperature, scrape character limit, request timeout) are centralized in `config.py` using Pydantic Settings. Secrets live in `.env`, defaults live in code. Changing the LLM model or adjusting scraping limits requires zero code changes.

### Pydantic Schemas
Request and response data contracts are enforced via Pydantic models (`schemas.py`). FastAPI validates incoming payloads and outgoing responses at the framework level — wrong data types are caught automatically before reaching application logic.

### Async Throughout
Scraping uses `httpx` (async HTTP client) and LLM calls use LangChain's `ainvoke` — the server can handle concurrent extraction requests without blocking. Tavily enrichment searches run in parallel via `asyncio.gather`.

### Normalized Database Schema
Eight tables with foreign key constraints enforce referential integrity:
- `sessions` — user segregation
- `recipes` — core recipe identity + raw scraped text for re-processing
- `ingredients` — quantity/unit/item separated per spec requirement
- `instructions` — ordered steps
- `nutrition` — calorie/protein/carb/fat estimates
- `substitutions` — dietary alternatives
- `shopping_list` — items grouped by category
- `related_recipes` — suggested pairings

### Meal Planner Tool-Calling Architecture
The meal planner uses three composable LangChain `@tool` functions:
1. `fetch_recipe_ingredients` — reads from PostgreSQL
2. `merge_quantities` — combines duplicates with intelligent quantity parsing
3. `group_by_category` — organizes by shopping aisle

Tools are invoked directly in sequence for performance. The full LLM-driven ReAct loop with tool selection is architecturally supported but bypassed for this deterministic pipeline — a conscious engineering tradeoff documented here.

---

## Setup & Installation

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL running locally

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd recipe-extractor
```

Create `.env` in the project root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/recipes
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Get API keys:
- Gemini: https://aistudio.google.com → "Get API Key"
- Tavily: https://tavily.com → free tier

### 2. Create the PostgreSQL database

```bash
createdb recipes
```

### 3. Install and run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`. Tables are created automatically on first startup.

### 4. Install and run the frontend

```bash
cd frontend
npm install
npm run dev
```

The UI is available at `http://localhost:5173`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/extract` | Extract recipe from URL. Body: `{ "url": "...", "session_id": "..." }` |
| `GET` | `/recipes?session_id=...` | List all recipes for a session |
| `GET` | `/recipes/{id}?session_id=...` | Get full recipe details |
| `DELETE` | `/recipes/clear?session_id=...` | Clear all recipes for a session |
| `POST` | `/meal-plan` | Generate combined shopping list. Body: `{ "recipe_ids": [1,2,3], "session_id": "..." }` |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Auto-generated Swagger API documentation |

---

## Testing

### Sample URLs tested across different sites and cuisines

JSON outputs and URLs are saved in `sample_data/`.

### Error handling tested

- Invalid URL (not http/https) → 400 with descriptive message
- Non-recipe page (news article) → 422 "does not appear to contain a recipe"
- Non-HTML URL (PDF, image) → 422 "does not point to an HTML page"
- Site blocks request (403) → 422 "site blocks automated requests"
- LLM returns invalid JSON → 500 with retry-safe error
- Duplicate URL submission → returns cached result instantly
- Partial DB write failure → `db.rollback()` prevents corrupted data

---

## Project Structure

```
recipe-extractor/
├── .env                          # Secrets (not committed)
├── .gitignore
├── README.md
├── requirements.txt
├── sample_data/                  # Tested URLs and JSON outputs and UI screeshots 
│   ├── urls.txt
│   ├── recipe_1.json
│   ├── recipe_2.json
│   ├── recipe_3.json
│   ├── API Output/
│   └── UI Screenshots/
├── prompts/                      # LangChain prompt templates
│   └── recipe_extract.txt
├── backend/
│   ├── config.py                 # Centralized config (Pydantic Settings)
│   ├── database.py               # SQLAlchemy connection + session
│   ├── main.py                   # FastAPI app + CORS + router registration
│   ├── models.py                 # 8 SQLAlchemy table definitions
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── routes/
│   │   ├── recipes.py            # /extract, /recipes, /recipes/{id}, /recipes/clear
│   │   └── meal_plan.py          # /meal-plan
│   └── services/
│       ├── scraper.py            # Three-tier scraping + validation
│       ├── llm.py                # Gemini via LangChain + post-processing
│       ├── enrichment.py         # Tavily grounded search
│       └── meal_planner_agent.py # Tool-calling meal plan generator
├── frontend/
│   └── src/
│       ├── App.jsx               # Main app with 3 tabs
│       ├── index.css             # Global styles + fonts
│       ├── api/
│       │   └── client.js         # Axios API client + session management
│       └── components/
│           ├── RecipeCard.jsx     # Shared recipe display component
│           ├── HistoryTable.jsx   # Tab 2 table + clear button
│           ├── DetailsModal.jsx   # Reusable recipe modal
│           └── MealPlanner.jsx    # Tab 3 recipe selector + shopping list
```

---

## Scope Considerations

These are noted as conscious scope decisions for this submission:

- **Authentication**: Session-based UUID segregation is used. Production would replace with JWT authentication.
- **JavaScript-heavy sites**: Scraper uses `requests`/`httpx` + BeautifulSoup. Sites requiring JavaScript rendering would need Playwright/Selenium integration.
- **Rate limiting**: No API rate limiting is implemented. Production would add FastAPI middleware for request throttling.
- **Latency optimization**: Uses Gemini Flash-Lite for fastest inference, capped output tokens, HTTP/2 connection pooling, and trimmed input context. Production would add response streaming and context caching for large-scale deployments.
- **Caching**: Duplicate URLs return cached DB results. Production would add Redis for TTL-based cache invalidation.
- **Meal planner tools**: Tools are invoked directly in sequence for performance. The LLM-driven ReAct loop with dynamic tool selection is architecturally supported for more complex planning scenarios.
