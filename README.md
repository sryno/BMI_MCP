# Health Information API

A FastAPI application that provides various health and nutrition calculators using FastAPI-MCP.

## Features

- BMI Calculator
- Body Frame Size Calculator
- Body Fat Percentage Calculator (U.S. Navy Method)
- Macronutrient Calculator
- Food Nutrition Calculator (using USDA FoodData Central API)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bmi_calc.git
cd bmi_calc
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# For the USDA FoodData Central API
# Get your API key from https://fdc.nal.usda.gov/api-key-signup.html
export USDA_API_KEY="your_api_key_here"

# (Optional) For the OpenAI API
export OPENAI_API_KEY="your_api_key_here"
```

## Running the Application

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the application is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### BMI Calculator

**Endpoint:** `POST /bmi`

Calculate Body Mass Index (BMI) based on weight and height.

**Request Body:**
```json
{
  "weight_kg": 70,
  "height_cm": 175
}
```

**Response:**
```json
{
  "bmi": 22.86,
  "category": "Normal weight"
}
```

### Body Frame Size Calculator

**Endpoint:** `POST /body-frame`

Determine body frame size based on wrist circumference and height.

**Request Body:**
```json
{
  "wrist_circumference_cm": 18,
  "height_cm": 180,
  "gender": "male"
}
```

**Response:**
```json
{
  "frame_size": "MEDIUM"
}
```

### Body Fat Percentage Calculator

**Endpoint:** `POST /body-fat`

Calculate body fat percentage using the U.S. Navy method.

**Request Body (Male):**
```json
{
  "gender": "male",
  "age": 30,
  "weight_kg": 80,
  "height_cm": 180,
  "neck_circumference_cm": 38,
  "waist_circumference_cm": 85
}
```

**Request Body (Female):**
```json
{
  "gender": "female",
  "age": 30,
  "weight_kg": 65,
  "height_cm": 165,
  "neck_circumference_cm": 32,
  "waist_circumference_cm": 70,
  "hip_circumference_cm": 95
}
```

**Response:**
```json
{
  "body_fat_percentage": 15.3,
  "category": "Fitness"
}
```

### Macronutrient Calculator

**Endpoint:** `POST /macros`

Calculate daily calorie and macronutrient targets.

**Request Body:**
```json
{
  "gender": "male",
  "age": 30,
  "weight_kg": 80,
  "height_cm": 180,
  "activity_level": "moderate",
  "goal": "maintain",
  "body_fat_percentage": 15
}
```

**Response:**
```json
{
  "calories": 2800,
  "protein_g": 122,
  "carbs_g": 350,
  "fat_g": 78
}
```

### Food Nutrition Calculator

**Endpoint:** `GET /food-nutrition`

Calculate the nutritional content of a list of food ingredients and amounts.

**Query Parameters:**
- `ingredients`: List of food ingredients (e.g., 'apple', 'chicken breast')
- `amounts`: List of amounts in grams corresponding to each ingredient

**Example Request:**
```
GET /food-nutrition?ingredients=apple&ingredients=chicken%20breast&amounts=100&amounts=150
```

**Response:**
```json
{
  "total_calories": 278.5,
  "total_protein_g": 31.45,
  "total_carbs_g": 14.8,
  "total_fat_g": 8.7,
  "total_fiber_g": 2.4,
  "total_sugar_g": 10.4,
  "foods": [
    {
      "name": "Apple, raw",
      "amount_g": 100,
      "calories": 52,
      "protein_g": 0.3,
      "carbs_g": 13.8,
      "fat_g": 0.2,
      "fiber_g": 2.4,
      "sugar_g": 10.4
    },
    {
      "name": "Chicken, breast, meat only, cooked, roasted",
      "amount_g": 150,
      "calories": 226.5,
      "protein_g": 31.15,
      "carbs_g": 1,
      "fat_g": 8.5,
      "fiber_g": 0,
      "sugar_g": 0
    }
  ]
}
```

## Running Tests

```bash
pytest -v
```

## License

MIT