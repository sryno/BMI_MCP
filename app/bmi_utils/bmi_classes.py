from typing import List, Dict, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, conint, confloat


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class Goal(str, Enum):
    MAINTAIN = "maintain"
    LOSE = "lose"
    GAIN = "gain"


class FrameSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class BMIRequest(BaseModel):
    weight_kg: confloat(gt=0) = Field(..., description="Weight in kilograms")
    height_cm: confloat(gt=0) = Field(..., description="Height in centimeters")


class BMIResponse(BaseModel):
    bmi: float = Field(..., description="Body Mass Index")
    category: str = Field(..., description="BMI Category")


class BodyFrameRequest(BaseModel):
    wrist_circumference_cm: confloat(gt=0) = Field(..., description="Wrist circumference in centimeters")
    height_cm: confloat(gt=0) = Field(..., description="Height in centimeters")
    gender: Gender = Field(..., description="Gender")


class BodyFrameResponse(BaseModel):
    frame_size: FrameSize = Field(..., description="Body frame size")


class BodyFatRequest(BaseModel):
    gender: Gender = Field(..., description="Gender")
    age: conint(ge=18) = Field(..., description="Age in years")
    weight_kg: confloat(gt=0) = Field(..., description="Weight in kilograms")
    height_cm: confloat(gt=0) = Field(..., description="Height in centimeters")
    neck_circumference_cm: confloat(gt=0) = Field(..., description="Neck circumference in centimeters")
    waist_circumference_cm: confloat(gt=0) = Field(..., description="Waist circumference in centimeters")
    hip_circumference_cm: Optional[confloat(gt=0)] = Field(None, description="Hip circumference in centimeters (required for females)")


class BodyFatResponse(BaseModel):
    body_fat_percentage: float = Field(..., description="Body fat percentage")
    category: str = Field(..., description="Body fat category")


class MacroRequest(BaseModel):
    gender: Gender = Field(..., description="Gender")
    age: conint(ge=18) = Field(..., description="Age in years")
    weight_kg: confloat(gt=0) = Field(..., description="Weight in kilograms")
    height_cm: confloat(gt=0) = Field(..., description="Height in centimeters")
    activity_level: ActivityLevel = Field(..., description="Activity level")
    goal: Goal = Field(..., description="Weight goal")
    body_fat_percentage: Optional[confloat(ge=0, le=100)] = Field(None, description="Body fat percentage if known")


class MacroResponse(BaseModel):
    calories: int = Field(..., description="Daily calorie target")
    protein_g: int = Field(..., description="Daily protein target in grams")
    carbs_g: int = Field(..., description="Daily carbohydrates target in grams")
    fat_g: int = Field(..., description="Daily fat target in grams")


class FoodNutritionResponse(BaseModel):
    total_calories: float = Field(..., description="Total calories")
    total_protein_g: float = Field(..., description="Total protein in grams")
    total_carbs_g: float = Field(..., description="Total carbohydrates in grams")
    total_fat_g: float = Field(..., description="Total fat in grams")
    total_fiber_g: float = Field(..., description="Total fiber in grams")
    total_sugar_g: float = Field(..., description="Total sugar in grams")
    foods: List[Dict] = Field(..., description="Nutrition details for each food item")
