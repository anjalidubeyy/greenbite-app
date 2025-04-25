from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import re
from thefuzz import process
from ingredients import extract_ingredients, load_dataset
from emissions import load_emissions_data, match_ingredients_with_emissions, calculate_total_impact, calculate_emissions_equivalence
from sustainability import get_sustainability_score 
from sustainability_comparison import compare_sustainability


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

@app.before_request
def handle_preflight_requests():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight request handled"})
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response, 200

# Load datasets with error handling
try:
    RECIPES_DATASET = load_dataset("C:/greenbite/datasets/filtered_recipes_1m.csv.gz")
    EMISSIONS_DATASET = load_emissions_data("C:/greenbite/datasets/Food_Product_Emissions.csv")
    print("✅ Datasets loaded successfully!")
except Exception as e:
    print(f"❌ Dataset loading error: {e}")
    RECIPES_DATASET, EMISSIONS_DATASET = None, None  # Gracefully handle loading failures

@app.route("/search", methods=["POST"])
def search():
    """Extract ingredients from the query and find matching recipes."""
    try:
        print(f"🔥 Raw request data: {request.data}")  # Debug request data
        data = request.get_json(silent=True)
        print(f"🔥 Parsed JSON: {data}")  # Debug parsed JSON

        if not data or "query" not in data or not isinstance(data["query"], str):
            print("❌ Invalid request format received!")
            return jsonify({"error": "Invalid request format"}), 400

        query = data["query"].strip()
        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400

        print(f"✅ Query received: {query}")

        # Extract ingredients using `ingredients.py`
        if RECIPES_DATASET is None:
            return jsonify({"error": "Recipes dataset not loaded"}), 500

        extracted_ingredients, matched_titles = extract_ingredients(query, RECIPES_DATASET)
        print(f"🔍 Extracted Ingredients: {extracted_ingredients}")
        print(f"📌 Matched Titles: {matched_titles}")

        if not extracted_ingredients:
            return jsonify({"error": "No ingredients recognized"}), 400

        # Clean the extracted ingredients
        cleaned_ingredients = []
        for ingredients in extracted_ingredients:
            # Remove unnecessary quotes, brackets, and any non-alphanumeric characters
            cleaned = re.sub(r'[^\w\s,]', '', str(ingredients))  # Clean unwanted characters
            cleaned = cleaned.replace('"', '').replace('[', '').replace(']', '')  # Clean extra quotes and brackets
            cleaned_ingredients.append([ingredient.strip() for ingredient in cleaned.split(',')])

        # Combine cleaned ingredients with matched titles
        response = [
            {"title": title, "ingredients": ingredients}
            for title, ingredients in zip(matched_titles, cleaned_ingredients)
        ]

        return jsonify({"recipes": response}), 200

    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/emissions", methods=["POST"])
def emissions():
    """Calculate emissions breakdown and total emissions for given ingredients."""
    try:
        print(f"🔥 Raw request data: {request.data}")  # Debug request data
        data = request.get_json(silent=True)
        print(f"🔥 Parsed JSON: {data}")  # Debug parsed JSON

        if not data or "ingredients" not in data or not isinstance(data["ingredients"], list):
            print("❌ Invalid request format!")
            return jsonify({"error": "Invalid request format"}), 400

        ingredients = [ing.strip() for ing in data["ingredients"] if isinstance(ing, str) and ing.strip()]

        if not ingredients:
            print("⚠ No valid ingredients found!")
            return jsonify({"breakdown": {}, "total_emissions": 0}), 200  

        print(f"✅ Ingredients received: {ingredients}")

        # Match ingredients with emissions data
        if EMISSIONS_DATASET is None:
            return jsonify({"error": "Emissions dataset not loaded"}), 500

        matched_ingredients = match_ingredients_with_emissions(ingredients, EMISSIONS_DATASET)
        if not matched_ingredients:
            print("⚠ No matching ingredients found in emissions dataset!")
            return jsonify({"breakdown": {}, "total_emissions": 0}), 200  

        print(f"🔍 Matched Ingredients: {matched_ingredients}")

        # Calculate total impact
        total_impact, total_emissions = calculate_total_impact(matched_ingredients)
        print(f"📊 Total Impact: {total_impact}, Total Emissions: {total_emissions}")

        # Calculate emissions equivalence
        emissions_equivalence_data = calculate_emissions_equivalence(total_emissions)
        print(f"📊 Emissions Equivalence Data: {emissions_equivalence_data}")

        response = {
            "breakdown": {key: round(value, 3) for key, value in total_impact.items()},
            "total_emissions": round(total_emissions, 2),
            "emissions_equivalence": emissions_equivalence_data
        }

        print("📌 Computed Emissions Data:", response)
        return jsonify(response), 200

    except Exception as e:
        print(f"❌ Emissions error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/predict", methods=["POST"])
def predict():
    """Predict sustainability score based on emissions data."""
    try:
        print(f"🔥 Raw request data: {request.data}")  # Debug request data
        data = request.get_json(silent=True)
        print(f"🔥 Parsed JSON: {data}")  # Debug parsed JSON

        if not data:
            print("❌ Invalid request format!")
            return jsonify({"error": "Invalid request format"}), 400

        # Extract emissions data - handle both direct values and breakdown format
        emissions_data = {}
        
        # Check if we have direct emissions values
        if all(key in data for key in ["land_use_change", "feed", "farm", "processing", "transport", "packaging", "retail", "total_land_to_retail"]):
            emissions_data = {
                "land_use_change": float(data.get("land_use_change", 0)),
                "feed": float(data.get("feed", 0)),
                "farm": float(data.get("farm", 0)),
                "processing": float(data.get("processing", 0)),
                "transport": float(data.get("transport", 0)),
                "packaging": float(data.get("packaging", 0)),
                "retail": float(data.get("retail", 0)),
                "total_land_to_retail": float(data.get("total_land_to_retail", 0))
            }
        # Check if we have a breakdown format
        elif "breakdown" in data:
            breakdown = data["breakdown"]
            emissions_data = {
                "land_use_change": float(breakdown.get("Land Use Change", 0)),
                "feed": float(breakdown.get("Feed", 0)),
                "farm": float(breakdown.get("Farm", 0)),
                "processing": float(breakdown.get("Processing", 0)),
                "transport": float(breakdown.get("Transport", 0)),
                "packaging": float(breakdown.get("Packaging", 0)),
                "retail": float(breakdown.get("Retail", 0)),
                "total_land_to_retail": float(breakdown.get("Total from Land to Retail", 0))
            }
        else:
            print("❌ No valid emissions data found in request!")
            return jsonify({"error": "No valid emissions data found"}), 400

        print(f"✅ Emissions data received: {emissions_data}")

        # Calculate total emissions
        total_emissions = sum(emissions_data.values())
        
        # Calculate sustainability score based on total emissions
        # Lower total emissions = higher sustainability score
        max_emissions = 50.0  # Assume max emissions is 50 kg CO2e
        min_emissions = 0.1   # Assume min emissions is 0.1 kg CO2e
        
        if total_emissions <= min_emissions:
            sustainability_score = 5.0  # Maximum score for very low emissions
        elif total_emissions >= max_emissions:
            sustainability_score = 1.0  # Minimum score for very high emissions
        else:
            # Linear scaling between min and max emissions
            sustainability_score = 5.0 - ((total_emissions - min_emissions) / (max_emissions - min_emissions)) * 4.0

        # Cap sustainability score at 5.0
        sustainability_score = min(5.0, float(sustainability_score))

        print(f"📈 Sustainability Score: {sustainability_score}")

        response = {
            "sustainability_score": sustainability_score
        }

        print("📌 Computed Sustainability Score:", response)
        return jsonify(response), 200

    except Exception as e:
        print(f"❌ Predict error: {str(e)}")
        return jsonify({"error": str(e)}), 500

from sustainability import get_sustainability_score  # Import your existing function

@app.route('/compare-dishes', methods=['POST'])
def compare_dishes():
    """Compare two dishes and return their sustainability metrics."""
    try:
        data = request.get_json()
        print(f"🔥 Received request data: {data}")  # Debug log

        # Validate input
        if not data or 'dish1' not in data or 'dish2' not in data:
            return jsonify({"error": "Both dish names are required"}), 400

        dish1_name = data['dish1'].strip()
        dish2_name = data['dish2'].strip()

        if not dish1_name or not dish2_name:
            return jsonify({"error": "Both dish names cannot be empty"}), 400

        print(f"🔍 Searching for dishes: {dish1_name} and {dish2_name}")  # Debug log

        # Extract ingredients for both dishes
        dish1_ingredients, dish1_titles = extract_ingredients(dish1_name, RECIPES_DATASET)
        dish2_ingredients, dish2_titles = extract_ingredients(dish2_name, RECIPES_DATASET)

        if not dish1_ingredients or not dish2_ingredients:
            return jsonify({"error": "Could not find recipes for one or both dishes"}), 404

        # Get first recipe for each dish
        dish1 = {
            'title': dish1_titles[0] if dish1_titles else dish1_name,
            'ingredients': dish1_ingredients[0]
        }
        dish2 = {
            'title': dish2_titles[0] if dish2_titles else dish2_name,
            'ingredients': dish2_ingredients[0]
        }

        print(f"📝 Dish 1: {dish1}")  # Debug log
        print(f"📝 Dish 2: {dish2}")  # Debug log

        # Calculate sustainability scores
        dish1_score = get_sustainability_score(dish1['ingredients'])
        dish2_score = get_sustainability_score(dish2['ingredients'])

        # Calculate emissions for ingredients
        dish1_emissions = match_ingredients_with_emissions(dish1['ingredients'], EMISSIONS_DATASET)
        dish2_emissions = match_ingredients_with_emissions(dish2['ingredients'], EMISSIONS_DATASET)

        # Calculate total emissions
        _, dish1_total_emissions = calculate_total_impact(dish1_emissions)
        _, dish2_total_emissions = calculate_total_impact(dish2_emissions)

        # Calculate emissions equivalence for both dishes
        dish1_equivalence = calculate_emissions_equivalence(dish1_total_emissions)
        dish2_equivalence = calculate_emissions_equivalence(dish2_total_emissions)

        # Cap sustainability scores at 5.0
        dish1_score = min(5.0, float(dish1_score)) if isinstance(dish1_score, (int, float)) else 3.0
        dish2_score = min(5.0, float(dish2_score)) if isinstance(dish2_score, (int, float)) else 3.0

        # Prepare response
        result = {
            'dish1': {
                'title': dish1['title'],
                'ingredients': [{'name': ing, 'emission': dish1_emissions.get(ing, {}).get('Total Global Average GHG Emissions per kg', 0)} for ing in dish1['ingredients']],
                'sustainability_score': dish1_score,
                'total_emissions': dish1_total_emissions,
                'emissions_equivalence': dish1_equivalence
            },
            'dish2': {
                'title': dish2['title'],
                'ingredients': [{'name': ing, 'emission': dish2_emissions.get(ing, {}).get('Total Global Average GHG Emissions per kg', 0)} for ing in dish2['ingredients']],
                'sustainability_score': dish2_score,
                'total_emissions': dish2_total_emissions,
                'emissions_equivalence': dish2_equivalence
            },
            'comparison_result': f"{'Dish 1' if dish1_score > dish2_score else 'Dish 2'} is more sustainable."
        }

        print(f"✅ Comparison result: {result}")  # Debug log
        return jsonify(result), 200

    except Exception as e:
        print(f"❌ Error in compare_dishes: {str(e)}")  # Debug log
        return jsonify({"error": f"Failed to compare dishes: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
