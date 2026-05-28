# All SQLAlchemy table definitions
from database import Base
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from datetime import datetime

class Session(Base):
    __tablename__ = "sessions"
    session_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.session_id"))
    url = Column(String, nullable=False)
    title = Column(String)
    cuisine = Column(String)
    prep_time = Column(String)
    cook_time = Column(String)
    total_time = Column(String)
    servings = Column(Integer)
    difficulty = Column(String)
    raw_scraped_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    quantity = Column(String)
    unit = Column(String)
    item = Column(String)

class Instruction(Base):
    __tablename__ = "instructions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    step_number = Column(Integer)
    instruction_text = Column(Text)

class Nutrition(Base):
    __tablename__ = "nutrition"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    calories = Column(Integer)
    protein = Column(String)
    carbs = Column(String)
    fat = Column(String)

class Substitution(Base):
    __tablename__ = "substitutions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    substitution_text = Column(Text)

class ShoppingListItem(Base):
    __tablename__ = "shopping_list"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    category = Column(String)
    item = Column(String)

class RelatedRecipe(Base):
    __tablename__ = "related_recipes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    related_title = Column(String)