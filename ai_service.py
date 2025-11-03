"""
AI Service for Generative Recipe Features
Supports Google Gemini API with fallback to template-based generator
"""
import os
import json
import re

# Hardcoded API key (for demo purposes - in production, use environment variables)
GEMINI_API_KEY = ""

# Try to import Google Generative AI, but allow fallback if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Fallback: Use a simple rule-based generator if no API key
class FallbackAIGenerator:
    """Fallback AI generator using template-based approach"""
    
    def generate_recipe(self, preferences, dietary_restrictions, available_ingredients):
        """Generate a basic recipe using templates"""
        cuisine = preferences.get('cuisine', 'International')
        meal_type = preferences.get('meal_type', 'Dinner')
        difficulty = preferences.get('difficulty', 'Easy')
        
        # Determine dietary info
        is_vegan = 'vegan' in dietary_restrictions
        is_vegetarian = 'vegetarian' in dietary_restrictions or is_vegan
        is_gluten_free = 'gluten-free' in dietary_restrictions
        is_dairy_free = 'dairy-free' in dietary_restrictions or is_vegan
        
        # Create a recipe name
        base_name = f"{cuisine} {meal_type}"
        if is_vegetarian:
            base_name = f"Vegetarian {base_name}"
        if is_gluten_free:
            base_name = f"Gluten-Free {base_name}"
        
        recipe_name = f"{base_name} Bowl" if meal_type == 'Lunch' else f"{base_name} Dish"
        
        # Generate ingredients list (use available + some common ones)
        ingredients = available_ingredients[:5] if available_ingredients else [
            "olive oil", "garlic", "salt", "pepper"
        ]
        
        # Add common ingredients based on cuisine
        cuisine_ingredients = {
            "Italian": ["tomatoes", "basil", "parmesan cheese"],
            "Indian": ["curry powder", "turmeric", "cumin"],
            "Japanese": ["soy sauce", "ginger", "sesame oil"],
            "Mexican": ["cilantro", "lime", "cumin"],
            "Mediterranean": ["lemon", "oregano", "olives"],
        }
        
        if cuisine in cuisine_ingredients:
            ingredients.extend(cuisine_ingredients[cuisine][:2])
        
        # Generate steps
        steps = [
            f"Prepare all ingredients. Wash and chop vegetables if needed.",
            f"Heat oil in a pan over medium heat. Add aromatics and cook until fragrant.",
            f"Add main ingredients and cook for 5-7 minutes until tender.",
            f"Season with salt, pepper, and spices to taste.",
            f"Stir everything together and cook for another 2-3 minutes.",
            f"Serve hot, garnished with fresh herbs if available."
        ]
        
        # Estimate times
        prep_time = 10 if difficulty == "Easy" else 15 if difficulty == "Medium" else 20
        cook_time = 15 if difficulty == "Easy" else 25 if difficulty == "Medium" else 35
        
        return {
            "id": 9999,  # High ID for AI-generated recipes
            "name": recipe_name,
            "cuisine": cuisine,
            "meal_type": meal_type,
            "difficulty": difficulty,
            "prep_time": prep_time,
            "cook_time": cook_time,
            "servings": 4,
            "ingredients": list(set(ingredients)),  # Remove duplicates
            "steps": steps,
            "dietary_info": {
                "vegetarian": is_vegetarian,
                "vegan": is_vegan,
                "gluten_free": is_gluten_free,
                "dairy_free": is_dairy_free,
                "nut_free": True,
                "low_carb": "low-carb" in dietary_restrictions,
                "keto": "keto" in dietary_restrictions
            },
            "tags": dietary_restrictions + ["ai-generated"],
            "ai_generated": True
        }
    
    def adapt_recipe(self, recipe, available_ingredients, substitutions):
        """Adapt a recipe with substitutions"""
        adapted = recipe.copy()
        adapted_ingredients = adapted.get('ingredients', []).copy()
        
        # Apply substitutions
        for old_ing, new_ing in substitutions.items():
            adapted_ingredients = [
                new_ing if ing.lower() == old_ing.lower() else ing
                for ing in adapted_ingredients
            ]
        
        # Replace unavailable ingredients with available ones
        for i, ing in enumerate(adapted_ingredients):
            if ing.lower() not in [ai.lower() for ai in available_ingredients]:
                if available_ingredients:
                    adapted_ingredients[i] = available_ingredients[0]
        
        adapted['ingredients'] = adapted_ingredients
        adapted['name'] = f"{adapted['name']} (Adapted)"
        adapted['ai_generated'] = True
        
        return adapted
    
    def generate_cooking_tips(self, recipe):
        """Generate cooking tips for a recipe"""
        difficulty = recipe.get('difficulty', 'Easy')
        meal_type = recipe.get('meal_type', 'Dinner')
        
        tips = [
            "Always prep your ingredients before you start cooking (mise en place).",
            f"For {difficulty.lower()} recipes, read through all steps before beginning.",
            f"Taste and adjust seasoning as you cook, not just at the end.",
        ]
        
        if meal_type == 'Breakfast':
            tips.append("Prep can be done the night before to save morning time.")
        elif meal_type == 'Dinner':
            tips.append("Let proteins rest for a few minutes after cooking for better juiciness.")
        
        return tips


class GeminiGenerator:
    """Google Gemini-powered recipe generator"""
    
    def __init__(self):
        # Use hardcoded API key or try environment variables as fallback
        api_key = GEMINI_API_KEY or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        genai.configure(api_key=api_key)
        # Use Gemini 2.0 Flash Experimental (or fallback to 1.5 Flash)
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except:
            # Fallback to 1.5 Flash if 2.0 is not available
            self.model_name = 'gemini-1.5-flash'
            self.model = genai.GenerativeModel(self.model_name)
    
    def _parse_json_from_response(self, response_text):
        """Extract JSON from AI response"""
        if not response_text:
            return None
            
        # Try to find JSON in the response (handle both single and multi-line)
        # Look for JSON object - handle nested structures
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group()
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON array for tips
        json_array_match = re.search(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', response_text, re.DOTALL)
        if json_array_match:
            try:
                json_str = json_array_match.group()
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # If no JSON found, return None
        return None
    
    def generate_recipe(self, preferences, dietary_restrictions, available_ingredients):
        """Generate a recipe using Google Gemini"""
        restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "none"
        ingredients_text = ", ".join(available_ingredients) if available_ingredients else "use common pantry items"
        
        prompt = f"""You are an expert chef and recipe developer. Generate a detailed recipe in JSON format.

Specifications:
- Cuisine: {preferences.get('cuisine', 'Any')}
- Meal Type: {preferences.get('meal_type', 'Any')}
- Difficulty: {preferences.get('difficulty', 'Any')}
- Dietary Restrictions: {restrictions_text}
- Available Ingredients: {ingredients_text}

IMPORTANT: Return ONLY a valid JSON object with this exact structure, no additional text:

{{
    "name": "Recipe Name",
    "cuisine": "Cuisine type",
    "meal_type": "Breakfast/Lunch/Dinner",
    "difficulty": "Easy/Medium/Hard",
    "prep_time": 15,
    "cook_time": 20,
    "servings": 4,
    "ingredients": ["ingredient1", "ingredient2"],
    "steps": ["Step 1", "Step 2"],
    "dietary_info": {{
        "vegetarian": true,
        "vegan": false,
        "gluten_free": false,
        "dairy_free": false,
        "nut_free": true,
        "low_carb": false,
        "keto": false
    }},
    "tags": ["tag1", "tag2"],
    "ai_generated": true
}}

Make sure the recipe uses the available ingredients when possible. Generate a creative and delicious recipe."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=2000,
                )
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            recipe_data = self._parse_json_from_response(response_text)
            
            if recipe_data:
                recipe_data['id'] = 9999
                return recipe_data
            else:
                # Fallback if parsing fails
                print(f"Failed to parse JSON from Gemini response: {response_text[:200]}")
                return FallbackAIGenerator().generate_recipe(preferences, dietary_restrictions, available_ingredients)
        
        except Exception as e:
            print(f"Gemini API error: {e}")
            return FallbackAIGenerator().generate_recipe(preferences, dietary_restrictions, available_ingredients)
    
    def adapt_recipe(self, recipe, available_ingredients, substitutions):
        """Adapt a recipe using Google Gemini"""
        recipe_text = json.dumps(recipe, indent=2)
        ingredients_text = ", ".join(available_ingredients) if available_ingredients else "use what's available"
        subs_text = ", ".join([f"{k} -> {v}" for k, v in substitutions.items()]) if substitutions else "none"
        
        prompt = f"""You are an expert chef. Adapt the following recipe to use these available ingredients and substitutions.

Available Ingredients: {ingredients_text}
Substitutions: {subs_text}

Original Recipe:
{recipe_text}

IMPORTANT: Return ONLY the adapted recipe as valid JSON with the same structure. Make smart substitutions and adjust cooking steps accordingly. Return only JSON, no additional text."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000,
                )
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            adapted_data = self._parse_json_from_response(response_text)
            
            if adapted_data:
                adapted_data['ai_generated'] = True
                adapted_data['id'] = recipe.get('id', 9999)
                return adapted_data
            else:
                print(f"Failed to parse JSON from Gemini response: {response_text[:200]}")
                return FallbackAIGenerator().adapt_recipe(recipe, available_ingredients, substitutions)
        
        except Exception as e:
            print(f"Gemini API error: {e}")
            return FallbackAIGenerator().adapt_recipe(recipe, available_ingredients, substitutions)
    
    def generate_cooking_tips(self, recipe):
        """Generate personalized cooking tips using Google Gemini"""
        recipe_summary = f"{recipe.get('name', 'Recipe')} - {recipe.get('cuisine', '')} {recipe.get('meal_type', '')} - Difficulty: {recipe.get('difficulty', '')}"
        
        prompt = f"""You are a professional chef. Provide 5 helpful cooking tips for this recipe.

Recipe: {recipe_summary}
Ingredients: {', '.join(recipe.get('ingredients', [])[:10])}
Cooking time: {recipe.get('cook_time', 0)} minutes

IMPORTANT: Return ONLY a JSON array of strings, no additional text: ["tip1", "tip2", "tip3", "tip4", "tip5"]"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=800,
                )
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            tips_data = self._parse_json_from_response(response_text)
            
            if tips_data and isinstance(tips_data, list):
                return tips_data
            else:
                return FallbackAIGenerator().generate_cooking_tips(recipe)
        
        except Exception as e:
            print(f"Gemini API error: {e}")
            return FallbackAIGenerator().generate_cooking_tips(recipe)


def get_ai_generator():
    """Get the appropriate AI generator (Gemini or fallback)"""
    # Use hardcoded API key or try environment variables as fallback
    api_key = GEMINI_API_KEY or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    
    if GEMINI_AVAILABLE and api_key:
        try:
            return GeminiGenerator()
        except Exception as e:
            print(f"Failed to initialize Gemini generator: {e}")
            return FallbackAIGenerator()
    else:
        return FallbackAIGenerator()

