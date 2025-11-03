from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from ai_service import get_ai_generator

app = Flask(__name__)
CORS(app)

# Initialize AI generator
ai_generator = get_ai_generator()

# Load recipes from JSON file
def load_recipes():
    if os.path.exists('recipes.json'):
        with open('recipes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_recipes(recipes):
    with open('recipes.json', 'w', encoding='utf-8') as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)

# Check if recipe matches dietary restrictions
def matches_dietary_restrictions(recipe, restrictions):
    if not restrictions:
        return True
    
    recipe_tags = recipe.get('tags', [])
    recipe_dietary = recipe.get('dietary_info', {})
    
    # Check each restriction
    for restriction in restrictions:
        restriction_lower = restriction.lower()
        
        if restriction_lower == 'vegetarian':
            if not recipe_dietary.get('vegetarian', False) and 'vegetarian' not in recipe_tags:
                return False
        elif restriction_lower == 'vegan':
            if not recipe_dietary.get('vegan', False) and 'vegan' not in recipe_tags:
                return False
        elif restriction_lower == 'gluten-free':
            if not recipe_dietary.get('gluten_free', False) and 'gluten-free' not in recipe_tags:
                return False
        elif restriction_lower == 'dairy-free':
            if not recipe_dietary.get('dairy_free', False) and 'dairy-free' not in recipe_tags:
                return False
        elif restriction_lower == 'nut-free':
            if not recipe_dietary.get('nut_free', False) and 'nut-free' not in recipe_tags:
                return False
        elif restriction_lower == 'low-carb':
            if not recipe_dietary.get('low_carb', False) and 'low-carb' not in recipe_tags:
                return False
        elif restriction_lower == 'keto':
            if not recipe_dietary.get('keto', False) and 'keto' not in recipe_tags:
                return False
    
    return True

# Calculate match score based on available ingredients
def calculate_ingredient_match_score(recipe, available_ingredients):
    if not available_ingredients:
        return 1.0
    
    recipe_ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
    available_lower = [ing.lower() for ing in available_ingredients]
    
    # Count how many recipe ingredients are available
    matching = sum(1 for ing in recipe_ingredients if any(avail in ing or ing in avail for avail in available_lower))
    total = len(recipe_ingredients)
    
    if total == 0:
        return 0.0
    
    # Score: percentage of ingredients available
    # Bonus if all ingredients are available
    score = matching / total
    if matching == total:
        score = 1.0  # Perfect match
    
    return score

# Filter and rank recipes
def filter_recipes(recipes, preferences, dietary_restrictions, available_ingredients):
    filtered = []
    
    for recipe in recipes:
        # Check dietary restrictions
        if not matches_dietary_restrictions(recipe, dietary_restrictions):
            continue
        
        # Calculate ingredient match score
        match_score = calculate_ingredient_match_score(recipe, available_ingredients)
        
        # Check cuisine preference
        cuisine_match = True
        if preferences.get('cuisine'):
            recipe_cuisine = recipe.get('cuisine', '').lower()
            preferred_cuisine = preferences['cuisine'].lower()
            if preferred_cuisine not in recipe_cuisine:
                cuisine_match = False
        
        # Check meal type preference
        meal_type_match = True
        if preferences.get('meal_type'):
            recipe_meal_type = recipe.get('meal_type', '').lower()
            preferred_meal_type = preferences['meal_type'].lower()
            if preferred_meal_type not in recipe_meal_type:
                meal_type_match = False
        
        # Check difficulty preference
        difficulty_match = True
        if preferences.get('difficulty'):
            recipe_difficulty = recipe.get('difficulty', '').lower()
            preferred_difficulty = preferences['difficulty'].lower()
            if recipe_difficulty != preferred_difficulty:
                difficulty_match = False
        
        # Calculate final score (weighted)
        preference_score = 1.0
        if not cuisine_match:
            preference_score *= 0.7
        if not meal_type_match:
            preference_score *= 0.7
        if not difficulty_match:
            preference_score *= 0.8
        
        final_score = match_score * 0.6 + preference_score * 0.4
        
        filtered.append({
            'recipe': recipe,
            'score': final_score,
            'ingredient_match': match_score,
            'preference_match': preference_score
        })
    
    # Sort by score (highest first)
    filtered.sort(key=lambda x: x['score'], reverse=True)
    return filtered

@app.route('/')
def index():
    return jsonify({ 'service': 'Recipe Assistant API', 'status': 'ok' })

@app.route('/api/recipes', methods=['GET'])
def get_all_recipes():
    recipes = load_recipes()
    return jsonify(recipes)

@app.route('/api/recommend', methods=['POST'])
def recommend_recipes():
    data = request.json
    preferences = data.get('preferences', {})
    dietary_restrictions = data.get('dietary_restrictions', [])
    available_ingredients = data.get('available_ingredients', [])
    use_ai_generation = data.get('use_ai_generation', False)
    
    recipes = load_recipes()
    
    # If AI generation is requested and we have ingredients, generate a recipe
    ai_generated = None
    if use_ai_generation and available_ingredients:
        try:
            ai_generated = ai_generator.generate_recipe(
                preferences,
                dietary_restrictions,
                available_ingredients
            )
            # Add AI-generated recipe to the list
            recipes.append(ai_generated)
        except Exception as e:
            print(f"AI generation error: {e}")
    
    filtered = filter_recipes(recipes, preferences, dietary_restrictions, available_ingredients)
    
    # Return top 10 matches
    results = [item['recipe'] for item in filtered[:10]]
    
    return jsonify({
        'recipes': results,
        'total_matches': len(filtered),
        'ai_generated_included': ai_generated is not None
    })

@app.route('/api/recipe/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipes = load_recipes()
    recipe = next((r for r in recipes if r.get('id') == recipe_id), None)
    
    if recipe:
        return jsonify(recipe)
    else:
        return jsonify({'error': 'Recipe not found'}), 404

@app.route('/api/generate', methods=['POST'])
def generate_recipe():
    """Generate a new recipe using AI based on preferences and ingredients"""
    data = request.json
    preferences = data.get('preferences', {})
    dietary_restrictions = data.get('dietary_restrictions', [])
    available_ingredients = data.get('available_ingredients', [])
    
    try:
        generated_recipe = ai_generator.generate_recipe(
            preferences, 
            dietary_restrictions, 
            available_ingredients
        )
        return jsonify({
            'recipe': generated_recipe,
            'success': True,
            'message': 'Recipe generated successfully!'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/adapt/<int:recipe_id>', methods=['POST'])
def adapt_recipe(recipe_id):
    """Adapt an existing recipe using AI based on available ingredients"""
    recipes = load_recipes()
    recipe = next((r for r in recipes if r.get('id') == recipe_id), None)
    
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    data = request.json
    available_ingredients = data.get('available_ingredients', [])
    substitutions = data.get('substitutions', {})
    
    try:
        adapted_recipe = ai_generator.adapt_recipe(
            recipe,
            available_ingredients,
            substitutions
        )
        return jsonify({
            'recipe': adapted_recipe,
            'success': True,
            'message': 'Recipe adapted successfully!'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/tips/<int:recipe_id>', methods=['GET'])
def get_cooking_tips(recipe_id):
    """Get AI-generated cooking tips for a recipe"""
    recipes = load_recipes()
    recipe = next((r for r in recipes if r.get('id') == recipe_id), None)
    
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    try:
        tips = ai_generator.generate_cooking_tips(recipe)
        return jsonify({
            'tips': tips,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/ai-status', methods=['GET'])
def ai_status():
    """Check if AI features are available"""
    from ai_service import GEMINI_API_KEY
    # Check hardcoded key or environment variables
    api_key = GEMINI_API_KEY or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    has_gemini = api_key is not None and api_key.strip() != ''
    
    return jsonify({
        'has_gemini': has_gemini,
        'ai_available': True,  # Fallback AI always available
        'message': 'Google Gemini API enabled' if has_gemini else 'Using fallback AI generator'
    })

if __name__ == '__main__':
    # Initialize recipes if file doesn't exist
    if not os.path.exists('recipes.json'):
        from initialize_recipes import initialize_recipes
        initialize_recipes()
    
    app.run(debug=True, port=5000)

