from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
from sqlalchemy.orm import Session
from database import get_db
import models
from services.scraper import scrape_recipe, _extract_title_hint, extract_title_from_url, _needs_enrichment
from services.llm import extract_recipe
from services.enrichment import get_grounding_data
from schemas import ExtractRequest, RecipeResponse, RecipeListResponse, RecipeListItem
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

# centralized error response structure
def error_response(status_code: int, message: str, detail: str = None):
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "detail": detail or message
        }
    )

@router.post("/extract", response_model=RecipeResponse)
async def extract(payload: ExtractRequest, db: Session = Depends(get_db)):
    url = payload.url
    session_id = payload.session_id
    logger.info(f"\n🔄 ====== NEW EXTRACTION REQUEST ======")
    logger.info(f"📱 Session ID: {session_id}")
    logger.info(f"🔗 URL: {url}")

    # validate session_id is not empty
    if not session_id.strip():
        logger.warning(f"❌ Invalid session ID")
        raise error_response(400, "Invalid session ID")

    # basic URL validation
    if not url.strip():
        logger.warning(f"❌ Empty URL provided")
        raise error_response(400, "URL cannot be empty")

    # ensure session exists
    try:
        session = db.query(models.Session).filter_by(session_id=session_id).first()
        if not session:
            session = models.Session(session_id=session_id)
            db.add(session)
            db.commit()
            logger.info(f"✅ New session created: {session_id}")
        else:
            logger.info(f"✅ Existing session found: {session_id}")
    except Exception as e:
        logger.error(f"🔴 Database error creating session: {e}")
        raise error_response(500, "Database error", str(e))

    # return cached result
    existing = db.query(models.Recipe).filter_by(
        url=url, session_id=session_id
    ).first()
    if existing:
        logger.info(f"💾 Recipe found in cache - returning cached result")
        logger.info(f"🔄 ====== EXTRACTION COMPLETE (CACHED) ======\n")
        return build_response(existing, db)

    # scrape with detailed error
    try:
        logger.info(f"\n📝 Step 1: Scraping website...")
        raw_text = await scrape_recipe(url)
    except ValueError as e:
        logger.error(f"🔴 Scraping failed: {str(e)}")
        logger.info(f"🔄 ====== EXTRACTION FAILED ======\n")
        raise error_response(422, str(e))

    # extract title hint for grounding
    recipe_title = _extract_title_hint(raw_text, url)
    if not recipe_title:
        recipe_title = extract_title_from_url(url)
    print(f"[DEBUG] Final title hint: '{recipe_title}'")

    needs_grounding = _needs_enrichment(raw_text)

    logger.info(f"📖 Extracted title hint: {recipe_title}")

    # grounding + LLM — wrap together
    try:
        logger.info(f"\n📝 Step 2: Fetching grounding data...")
        grounding = await get_grounding_data(recipe_title) if needs_grounding else {}
        logger.info(f"\n📝 Step 3: Extracting recipe with LLM...")
        data = await extract_recipe(raw_text, grounding)
    except ValueError as e:
        logger.error(f"🔴 Extraction failed: {str(e)}")
        logger.info(f"🔄 ====== EXTRACTION FAILED ======\n")
        raise error_response(500, "Recipe extraction failed", str(e))

    # save to DB — wrap entire block in try/except
    try:
        logger.info(f"\n📝 Step 4: Saving to database...")
        recipe = models.Recipe(
            session_id=session_id,
            url=url,
            title=data.get("title"),
            cuisine=data.get("cuisine"),
            prep_time=data.get("prep_time"),
            cook_time=data.get("cook_time"),
            total_time=data.get("total_time"),
            servings=data.get("servings"),
            difficulty=data.get("difficulty"),
            raw_scraped_text=raw_text
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        logger.info(f"✅ Recipe saved (ID: {recipe.id}) - {recipe.title}")

        ingredients = data.get("ingredients") or []
        for ing in ingredients:
            db.add(models.Ingredient(
                recipe_id=recipe.id,
                quantity=ing.get("quantity"),
                unit=ing.get("unit"),
                item=ing.get("item")
            ))
        logger.debug(f"✅ Saved {len(ingredients)} ingredients")

        instructions = data.get("instructions") or []
        for ins in instructions:
            db.add(models.Instruction(
                recipe_id=recipe.id,
                step_number=ins.get("step_number"),
                instruction_text=ins.get("instruction_text")
            ))
        logger.debug(f"✅ Saved {len(instructions)} instructions")

        nutrition = data.get("nutrition_estimate") or {}
        db.add(models.Nutrition(
            recipe_id=recipe.id,
            calories=nutrition.get("calories"),
            protein=nutrition.get("protein"),
            carbs=nutrition.get("carbs"),
            fat=nutrition.get("fat")
        ))
        logger.debug(f"✅ Saved nutrition data")

        substitutions = data.get("substitutions") or []
        for sub in substitutions:
            db.add(models.Substitution(
                recipe_id=recipe.id,
                substitution_text=sub
            ))
        logger.debug(f"✅ Saved {len(substitutions)} substitutions")

        shopping_list = data.get("shopping_list") or {}
        if isinstance(shopping_list, dict):
            for category, items in shopping_list.items():
                if isinstance(items, list):
                    for item in items:
                        db.add(models.ShoppingListItem(
                            recipe_id=recipe.id,
                            category=category,
                            item=item
                        ))
        logger.debug(f"✅ Saved shopping list data")

        related_recipes = data.get("related_recipes") or []
        for related in related_recipes:
            db.add(models.RelatedRecipe(
                recipe_id=recipe.id,
                related_title=related
            ))
        logger.debug(f"✅ Saved {len(related_recipes)} related recipes")

        db.commit()
        logger.info(f"✅ All recipe data saved successfully")

    except Exception as e:
        db.rollback()  # critical — undo partial saves on failure
        logger.error(f"🔴 Database save error for URL {url}: {e}")
        logger.info(f"🔄 ====== EXTRACTION FAILED ======\n")
        raise error_response(500, "Failed to save recipe to database", str(e))

    logger.info(f"🎉 ====== EXTRACTION COMPLETE ======\n")
    return build_response(recipe, db)

@router.delete("/recipes/clear")
async def clear_history(session_id: str, db: Session = Depends(get_db)):
    """Clear all saved recipes for the current session."""
    try:
        recipes = db.query(models.Recipe).filter_by(session_id=session_id).all()

        if not recipes:
            return {"message": "No recipes to clear", "deleted": 0}

        count = 0
        for recipe in recipes:
            db.query(models.RelatedRecipe).filter_by(recipe_id=recipe.id).delete()
            db.query(models.ShoppingListItem).filter_by(recipe_id=recipe.id).delete()
            db.query(models.Substitution).filter_by(recipe_id=recipe.id).delete()
            db.query(models.Nutrition).filter_by(recipe_id=recipe.id).delete()
            db.query(models.Instruction).filter_by(recipe_id=recipe.id).delete()
            db.query(models.Ingredient).filter_by(recipe_id=recipe.id).delete()
            db.delete(recipe)
            count += 1

        db.commit()
        return {"message": f"Cleared {count} recipes", "deleted": count}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

def build_response(recipe: models.Recipe, db: Session) -> RecipeResponse:
    ingredients = db.query(models.Ingredient).filter_by(recipe_id=recipe.id).all()
    instructions = db.query(models.Instruction).filter_by(
        recipe_id=recipe.id
    ).order_by(models.Instruction.step_number).all()
    nutrition = db.query(models.Nutrition).filter_by(recipe_id=recipe.id).first()
    substitutions = db.query(models.Substitution).filter_by(recipe_id=recipe.id).all()
    shopping = db.query(models.ShoppingListItem).filter_by(recipe_id=recipe.id).all()
    related = db.query(models.RelatedRecipe).filter_by(recipe_id=recipe.id).all()

    shopping_grouped: Dict[str, List[str]] = {}
    for item in shopping:
        shopping_grouped.setdefault(item.category, []).append(item.item)

    return RecipeResponse(
        id=recipe.id,
        url=recipe.url,
        title=recipe.title,
        cuisine=recipe.cuisine,
        prep_time=recipe.prep_time,
        cook_time=recipe.cook_time,
        total_time=recipe.total_time,
        servings=recipe.servings,
        difficulty=recipe.difficulty,
        ingredients=[
            {"quantity": i.quantity, "unit": i.unit, "item": i.item}
            for i in ingredients
        ],
        instructions=[
            {"step_number": i.step_number, "instruction_text": i.instruction_text}
            for i in instructions
        ],
        nutrition_estimate={
            "calories": nutrition.calories,
            "protein": nutrition.protein,
            "carbs": nutrition.carbs,
            "fat": nutrition.fat
        } if nutrition else None,
        substitutions=[s.substitution_text for s in substitutions],
        shopping_list=shopping_grouped,
        related_recipes=[r.related_title for r in related]
    )


@router.get("/recipes", response_model=RecipeListResponse)
async def get_history(session_id: str, db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).filter_by(
        session_id=session_id
    ).order_by(models.Recipe.created_at.desc()).all()

    return RecipeListResponse(
        recipes=[RecipeListItem.model_validate(r) for r in recipes],
        total=len(recipes)
    )


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: int, session_id: str, db: Session = Depends(get_db)):
    recipe = db.query(models.Recipe).filter_by(
        id=recipe_id, session_id=session_id
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return build_response(recipe, db)


