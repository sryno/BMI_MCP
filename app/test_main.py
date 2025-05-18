import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from main import app

client = TestClient(app)

# Mock environment variable for tests
os.environ["USDA_API_KEY"] = "test_api_key"

def test_calculate_bmi():
    """Test the BMI calculation endpoint."""
    response = client.post(
        "/bmi",
        json={"weight_kg": 70, "height_cm": 175}
    )
    assert response.status_code == 200
    data = response.json()
    assert "bmi" in data
    assert "category" in data
    assert data["bmi"] == pytest.approx(22.86, 0.01)
    assert data["category"] == "Normal weight"

def test_calculate_body_frame():
    """Test the body frame size calculation endpoint."""
    # Test for male
    response = client.post(
        "/body-frame",
        json={
            "wrist_circumference_cm": 18,
            "height_cm": 180,
            "gender": "male"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "frame_size" in data
    assert data["frame_size"] == "medium"
    
    # Test for female
    response = client.post(
        "/body-frame",
        json={
            "wrist_circumference_cm": 15,
            "height_cm": 170,
            "gender": "female"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "frame_size" in data
    assert data["frame_size"] == "small"

def test_calculate_body_fat():
    """Test the body fat percentage calculation endpoint."""
    # Test for male
    response = client.post(
        "/body-fat",
        json={
            "gender": "male",
            "age": 30,
            "weight_kg": 80,
            "height_cm": 180,
            "neck_circumference_cm": 38,
            "waist_circumference_cm": 85,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "body_fat_percentage" in data
    assert "category" in data
    
    # Test for female (should fail without hip circumference)
    response = client.post(
        "/body-fat",
        json={
            "gender": "female",
            "age": 30,
            "weight_kg": 65,
            "height_cm": 165,
            "neck_circumference_cm": 32,
            "waist_circumference_cm": 70,
        }
    )
    assert response.status_code == 400
    
    # Test for female with hip circumference
    response = client.post(
        "/body-fat",
        json={
            "gender": "female",
            "age": 30,
            "weight_kg": 65,
            "height_cm": 165,
            "neck_circumference_cm": 32,
            "waist_circumference_cm": 70,
            "hip_circumference_cm": 95
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "body_fat_percentage" in data
    assert "category" in data

def test_calculate_macros():
    """Test the macronutrient calculation endpoint."""
    response = client.post(
        "/macros",
        json={
            "gender": "male",
            "age": 30,
            "weight_kg": 80,
            "height_cm": 180,
            "activity_level": "moderate",
            "goal": "maintain"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "calories" in data
    assert "protein_g" in data
    assert "carbs_g" in data
    assert "fat_g" in data
    
    # Test with body fat percentage
    response = client.post(
        "/macros",
        json={
            "gender": "female",
            "age": 30,
            "weight_kg": 65,
            "height_cm": 165,
            "activity_level": "light",
            "goal": "lose",
            "body_fat_percentage": 25
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "calories" in data
    assert "protein_g" in data
    assert "carbs_g" in data
    assert "fat_g" in data

@patch('httpx.AsyncClient')
def test_calculate_food_nutrition(mock_client):
    """Test the food nutrition calculation endpoint."""
    # Mock the httpx.AsyncClient
    mock_client_instance = AsyncMock()
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    # Mock the search response
    mock_search_response = MagicMock()
    mock_search_response.raise_for_status = MagicMock()
    mock_search_response.json.return_value = {
        "foods": [
            {
                "fdcId": 123456,
                "description": "Apples, red delicious, with skin, raw"
            }
        ]
    }
    
    # Mock the detail response
    mock_detail_response = MagicMock()
    mock_detail_response.raise_for_status = MagicMock()
    mock_detail_response.json.return_value = {
        "foodNutrients": [
            {"nutrient": {"id": 2047}, "amount": 61.79},  # Calories
            {"nutrient": {"id": 1003}, "amount": 0.19},  # Protein
            {"nutrient": {"id": 1005}, "amount": 14.78},  # Carbs
            {"nutrient": {"id": 1004}, "amount": 0.21},  # Fat
            {"nutrient": {"id": 1079}, "amount": 2.04},  # Fiber
            {"nutrient": {"id": 2000}, "amount": 12.22}  # Sugar
        ],
        "servingSize": 100,
        "servingSizeUnit": "g"
    }
    
    # Set up the mock responses
    mock_client_instance.get.side_effect = [mock_search_response, mock_detail_response]
    
    # Make the request
    response = client.get(
        "/food-nutrition",
        params={
            "ingredients": ["red delicious apple"],
            "amounts": [150]
        }
    )
    print(response.json())
    
    assert response.status_code == 200
    data = response.json()
    assert "total_calories" in data
    assert "total_protein_g" in data
    assert "total_carbs_g" in data
    assert "total_fat_g" in data
    assert "total_fiber_g" in data
    assert "total_sugar_g" in data
    assert "foods" in data
    assert len(data["foods"]) == 1
    
    # Check calculations (150g of apple)
    assert data["total_calories"] == pytest.approx(92.68, 0.1)  # 61.79 * 1.5
    assert data["total_protein_g"] == pytest.approx(0.28, 0.1)  # 0.19 * 1.5
    assert data["total_carbs_g"] == pytest.approx(22.17, 0.1)  # 14.78 * 1.5
    assert data["total_fat_g"] == pytest.approx(0.32, 0.1)  # 0.21 * 1.5
    assert data["total_fiber_g"] == pytest.approx(3.06, 0.1)  # 2.04 * 1.5
    assert data["total_sugar_g"] == pytest.approx(18.33, 0.1)  # 12.22 * 1.5

if __name__ == "__main__":
    pytest.main(["-v", "test_main.py"])