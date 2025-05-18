import os
from typing import List, Dict, Optional, Union
from enum import Enum

import httpx
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel, Field, conint, confloat
from dotenv import load_dotenv

from bmi_utils.bmi_classes import (
    BMIRequest,
    BMIResponse,
    BodyFrameRequest,
    BodyFrameResponse,
    BodyFatRequest,
    BodyFatResponse,
    MacroRequest,
    MacroResponse,
    FoodNutritionResponse,
    Gender,
    ActivityLevel,
    Goal,
    FrameSize
)
from bmi_utils.bmi_helpers import (
    get_bmi_category,
    get_body_fat_category,
    get_usda_api_key,
    get_openai_api_key
)
from bmi_utils.bmi_llm import get_food_item_from_llm


# Load environment variables from .env file
load_dotenv()


# Initialize FastAPI app
app = FastAPI(
    title="Health Information API",
    description="API for calculating various health metrics and nutritional information",
    version="1.0.0",
)


# Endpoints
@app.post(
    "/bmi",
    response_model=BMIResponse,
    tags=["Health Calculators"],
    operation_id="calculate_bmi",
    summary="Calculate BMI and determine the BMI category",
    description="Calculate BMI and determine the BMI category based on height and weight."
)
def calculate_bmi(request: BMIRequest):
    """Calculate BMI and determine the BMI category."""
    height_m = request.height_cm / 100
    bmi = request.weight_kg / (height_m * height_m)
    category = get_bmi_category(bmi)
    
    return BMIResponse(
        bmi=round(bmi, 2),
        category=category
    )


@app.post(
    "/body-frame",
    response_model=BodyFrameResponse,
    tags=["Health Calculators"],
    operation_id="calculate_body_frame",
    summary="Calculate body frame size",
    description="Calculate body frame size based on wrist circumference and height."
)
def calculate_body_frame(request: BodyFrameRequest):
    """Calculate body frame size based on wrist circumference and height."""
    # Calculate r value (height/wrist circumference)
    r = request.height_cm / request.wrist_circumference_cm
    
    if request.gender == Gender.MALE:
        if r > 10.4:
            frame_size = FrameSize.SMALL
        elif r < 9.6:
            frame_size = FrameSize.LARGE
        else:
            frame_size = FrameSize.MEDIUM
    else:  # Female
        if r > 11.0:
            frame_size = FrameSize.SMALL
        elif r < 10.1:
            frame_size = FrameSize.LARGE
        else:
            frame_size = FrameSize.MEDIUM
    
    return BodyFrameResponse(frame_size=frame_size)


@app.post(
    "/body-fat",
    response_model=BodyFatResponse,
    tags=["Health Calculators"],
    operation_id="calculate_body_fat",
    summary="Calculate body fat percentage and determine the body fat category",
    description="Calculate body fat percentage and determine the body fat category based on various metrics."
)
def calculate_body_fat(request: BodyFatRequest):
    """Calculate body fat percentage using the U.S. Navy method."""
    if request.gender == Gender.FEMALE and not request.hip_circumference_cm:
        raise HTTPException(
            status_code=400, 
            detail="Hip circumference is required for females"
        )
    
    height_m = request.height_cm / 100
    
    # U.S. Navy method
    if request.gender == Gender.MALE:
        body_fat = 495 / (1.0324 - 0.19077 * (
            (request.waist_circumference_cm - request.neck_circumference_cm) / 2.54
        ) + 0.15456 * (request.height_cm / 2.54)) - 450
    else:  # Female
        body_fat = 495 / (1.29579 - 0.35004 * (
            (request.waist_circumference_cm + request.hip_circumference_cm - request.neck_circumference_cm) / 2.54
        ) + 0.22100 * (request.height_cm / 2.54)) - 450
    
    category = get_body_fat_category(request.gender, body_fat)
    
    return BodyFatResponse(
        body_fat_percentage=round(body_fat, 2),
        category=category
    )


@app.post(
    "/macros",
    response_model=MacroResponse,
    tags=["Health Calculators"],
    operation_id="calculate_macros",
    summary="Calculate daily calorie and macronutrient targets",
    description="Calculate daily calorie and macronutrient targets based on various metrics."
)
def calculate_macros(request: MacroRequest):
    """Calculate daily calorie and macronutrient targets."""
    # Calculate BMR using Mifflin-St Jeor Equation
    if request.gender == Gender.MALE:
        bmr = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age + 5
    else:  # Female
        bmr = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age - 161
    
    # Apply activity multiplier
    activity_multipliers = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.LIGHT: 1.375,
        ActivityLevel.MODERATE: 1.55,
        ActivityLevel.ACTIVE: 1.725,
        ActivityLevel.VERY_ACTIVE: 1.9
    }
    
    tdee = bmr * activity_multipliers[request.activity_level]
    
    # Adjust for goal
    if request.goal == Goal.LOSE:
        calories = int(tdee * 0.8)  # 20% deficit
    elif request.goal == Goal.GAIN:
        calories = int(tdee * 1.1)  # 10% surplus
    else:  # Maintain
        calories = int(tdee)
    
    # Calculate macros
    # Protein: 1.8g per kg of lean body mass or 1.6g per kg of total weight if body fat unknown
    if request.body_fat_percentage is not None:
        lean_mass = request.weight_kg * (1 - request.body_fat_percentage / 100)
        protein_g = int(lean_mass * 1.8)
    else:
        protein_g = int(request.weight_kg * 1.6)
    
    # Fat: 25% of calories
    fat_g = int((calories * 0.25) / 9)
    
    # Remaining calories from carbs
    carbs_g = int((calories - (protein_g * 4) - (fat_g * 9)) / 4)
    
    return MacroResponse(
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g
    )


@app.get(
    "/food-nutrition",
    response_model=FoodNutritionResponse,
    tags=["Nutrition"],
    operation_id="calculate_food_nutrition",
    summary="Calculate the nutritional content of a list of food ingredients and amounts",
    description="Calculate the nutritional content of a list of food ingredients and amounts, using the USDA FoodData Central API."
)
async def calculate_food_nutrition(
    ingredients: List[str] = Query(..., description="List of food ingredients (e.g., 'apple', 'chicken breast')"),
    amounts: List[float] = Query(..., description="List of amounts in grams corresponding to each ingredient"),
    api_key: str = Depends(get_usda_api_key)
):
    """Calculate the nutritional content of a list of food ingredients and amounts."""
    if len(ingredients) != len(amounts):
        raise HTTPException(
            status_code=400,
            detail="The number of ingredients must match the number of amounts"
        )
    
    # Initialize totals
    total_calories = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    total_fiber = 0.0
    total_sugar = 0.0
    foods_data = []
    
    # USDA FoodData Central API base URL
    base_url = "https://api.nal.usda.gov/fdc/v1"
    
    async with httpx.AsyncClient() as client:
        for i, (ingredient, amount) in enumerate(zip(ingredients, amounts)):
            # Search for the food item
            search_url = f"{base_url}/foods/search"
            params = {
                "api_key": api_key,
                "query": ingredient,
                "dataType": "Foundation,SR Legacy",
                "pageSize": 25 # Get the first 25 foods that match
            }
            
            try:
                search_response = await client.get(search_url, params=params)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                if not search_data.get("foods") or len(search_data["foods"]) == 0:
                    foods_data.append({
                        "name": ingredient,
                        "amount_g": amount,
                        "calories": 0,
                        "protein_g": 0,
                        "carbs_g": 0,
                        "fat_g": 0,
                        "fiber_g": 0,
                        "sugar_g": 0,
                        "error": "Food not found"
                    })
                    continue

                # Check if OpenAI API key is available and use LLM to get the most likely food item
                if not get_openai_api_key():
                    food = search_data["foods"][0]
                else:
                    try:
                        chosen_index = get_food_item_from_llm(
                            ingredient,
                            [food["description"] for food in search_data["foods"]]
                        )["index"]
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Error from LLM: {e}")
                    if not chosen_index:
                        food = search_data["foods"][0]
                    else:
                        food = search_data["foods"][chosen_index]

                food_id = food["fdcId"]
                
                # Get detailed nutrition data
                detail_url = f"{base_url}/food/{food_id}"
                detail_params = {"api_key": api_key}
                
                detail_response = await client.get(detail_url, params=detail_params)
                detail_response.raise_for_status()
                food_detail = detail_response.json()
                
                # Extract nutrition data
                nutrients = food_detail.get("foodNutrients", [])
                
                # Initialize nutrient values
                calories = 0
                protein = 0
                carbs = 0
                fat = 0
                fiber = 0
                sugar = 0
                
                # Map nutrient IDs to their values
                # These IDs are based on USDA FoodData Central API
                for nutrient in nutrients:
                    nutrient_id = nutrient.get("nutrient", {}).get("id")
                    value = nutrient.get("amount", 0)
                    # print(f"{nutrient_id} / {nutrient.get('nutrient', {}).get('name')}: {value}")
                    
                    if nutrient_id == 2047:  # Energy (kcal)
                        calories = value
                    elif nutrient_id == 1008 and calories == 0.0:  # Energy (kcal) secondary
                        calories = value
                    elif nutrient_id == 1003:  # Protein
                        protein = value
                    elif nutrient_id == 1005:  # Carbohydrates
                        carbs = value
                    elif nutrient_id == 1004:  # Total fat
                        fat = value
                    elif nutrient_id == 1079:  # Fiber
                        fiber = value
                    elif nutrient_id == 2000:  # Total sugars
                        sugar = value
                
                # Calculate nutrition based on the amount
                serving_size = food_detail.get("servingSize", 100)
                serving_unit = food_detail.get("servingSizeUnit", "g")
                
                # Convert to 100g basis if serving size is not in grams
                if serving_unit.lower() != "g":
                    serving_size = 100
                
                # Calculate nutrition for the specified amount
                factor = amount / serving_size
                item_calories = calories * factor
                item_protein = protein * factor
                item_carbs = carbs * factor
                item_fat = fat * factor
                item_fiber = fiber * factor
                item_sugar = sugar * factor
                
                # Add to totals
                total_calories += item_calories
                total_protein += item_protein
                total_carbs += item_carbs
                total_fat += item_fat
                total_fiber += item_fiber
                total_sugar += item_sugar
                
                # Add food data
                foods_data.append({
                    "name": food.get("description", ingredient),
                    "amount_g": amount,
                    "calories": round(item_calories, 2),
                    "protein_g": round(item_protein, 2),
                    "carbs_g": round(item_carbs, 2),
                    "fat_g": round(item_fat, 2),
                    "fiber_g": round(item_fiber, 2),
                    "sugar_g": round(item_sugar, 2)
                })
                
            except Exception as e:
                foods_data.append({
                    "name": ingredient,
                    "amount_g": amount,
                    "calories": 0,
                    "protein_g": 0,
                    "carbs_g": 0,
                    "fat_g": 0,
                    "fiber_g": 0,
                    "sugar_g": 0,
                    "error": str(e)
                })
    
    return FoodNutritionResponse(
        total_calories=round(total_calories, 2),
        total_protein_g=round(total_protein, 2),
        total_carbs_g=round(total_carbs, 2),
        total_fat_g=round(total_fat, 2),
        total_fiber_g=round(total_fiber, 2),
        total_sugar_g=round(total_sugar, 2),
        foods=foods_data
    )


# Initialize FastAPI-MCP
mcp = FastApiMCP(
    app,
    name="Health Information API",
    description="API for calculating various health metrics and nutritional information",
    describe_all_responses=False,
    describe_full_response_schema=True
)
mcp.mount()


# Run the application with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("Shutting down...")