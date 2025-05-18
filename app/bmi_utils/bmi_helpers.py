import os
from fastapi import HTTPException
from .bmi_classes import Gender

def get_bmi_category(bmi: float) -> str:
    """Determine BMI category based on BMI value."""
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal weight"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def get_body_fat_category(gender: Gender, body_fat_percentage: float) -> str:
    """Determine body fat category based on gender and body fat percentage."""
    if gender == Gender.MALE:
        if body_fat_percentage < 6:
            return "Essential fat"
        elif 6 <= body_fat_percentage < 14:
            return "Athletic"
        elif 14 <= body_fat_percentage < 18:
            return "Fitness"
        elif 18 <= body_fat_percentage < 25:
            return "Average"
        else:
            return "Obese"
    else:  # Female
        if body_fat_percentage < 16:
            return "Essential fat"
        elif 16 <= body_fat_percentage < 24:
            return "Athletic"
        elif 24 <= body_fat_percentage < 31:
            return "Fitness"
        elif 31 <= body_fat_percentage < 39:
            return "Average"
        else:
            return "Obese"


def get_usda_api_key() -> str:
    """Get USDA API key from environment variable or use a default for development."""
    api_key = os.environ.get("USDA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="USDA API key not configured")
    return api_key