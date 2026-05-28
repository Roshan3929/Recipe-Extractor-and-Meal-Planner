from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from schemas import MealPlanRequest, MealPlanResponse
from services.meal_planner_agent import generate_meal_plan
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/meal-plan", response_model=MealPlanResponse)
async def create_meal_plan(payload: MealPlanRequest, db: Session = Depends(get_db)):
    logger.info(f"\n🍽️ ====== NEW MEAL PLAN REQUEST ======")
    logger.info(f"📱 Session ID: {payload.session_id}")
    logger.info(f"🔢 Recipe count: {len(payload.recipe_ids)}")
    
    if len(payload.recipe_ids) < 3:
        logger.warning(f"❌ Not enough recipes selected (minimum 3)")
        raise HTTPException(status_code=400, detail="Select at least 3 recipes")
    if len(payload.recipe_ids) > 5:
        logger.warning(f"❌ Too many recipes selected (maximum 5)")
        raise HTTPException(status_code=400, detail="Maximum 5 recipes allowed")

    # verify all recipes belong to this session
    for recipe_id in payload.recipe_ids:
        recipe = db.query(models.Recipe).filter_by(
            id=recipe_id,
            session_id=payload.session_id
        ).first()
        if not recipe:
            logger.error(f"🔴 Recipe {recipe_id} not found in session {payload.session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Recipe {recipe_id} not found in your history"
            )

    logger.info(f"✅ All recipes verified")
    logger.info(f"📊 Generating meal plan...")
    
    result = await generate_meal_plan(payload.recipe_ids)

    if "error" in result:
        logger.error(f"🔴 Meal plan generation failed: {result['error']}")
        logger.info(f"🔄 ====== MEAL PLAN FAILED ======\n")
        raise HTTPException(status_code=500, detail=result["error"])

    logger.info(f"✅ Meal plan generated successfully")
    logger.info(f"🎉 ====== MEAL PLAN COMPLETE ======\n")
    return MealPlanResponse(
        recipe_ids=payload.recipe_ids,
        combined_shopping_list=result,
        total_recipes=len(payload.recipe_ids)
    )