# Pydantic models (request/response shapes)
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime


# --- Request Schemas ---

class ExtractRequest(BaseModel):
    url: str
    session_id: str


# --- Component Schemas ---

class IngredientSchema(BaseModel):
    quantity: Optional[str] = None
    unit: Optional[str] = None
    item: Optional[str] = None

class InstructionSchema(BaseModel):
    step_number: int
    instruction_text: str

class NutritionSchema(BaseModel):
    calories: Optional[int] = None
    protein: Optional[str] = None
    carbs: Optional[str] = None
    fat: Optional[str] = None


# --- Response Schemas ---

class RecipeResponse(BaseModel):
    id: int
    url: str
    title: Optional[str] = None
    cuisine: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    ingredients: List[IngredientSchema] = []
    instructions: List[InstructionSchema] = []
    nutrition_estimate: Optional[NutritionSchema] = None
    substitutions: List[str] = []
    shopping_list: Dict[str, List[str]] = {}
    related_recipes: List[str] = []

    class Config:
        from_attributes = True


class RecipeListItem(BaseModel):
    id: int
    title: Optional[str] = None
    cuisine: Optional[str] = None
    difficulty: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    recipes: List[RecipeListItem]
    total: int


class MealPlanRequest(BaseModel):
    recipe_ids: List[int]
    session_id: str

class MealPlanResponse(BaseModel):
    recipe_ids: List[int]
    combined_shopping_list: Dict[str, List[dict]]
    total_recipes: int