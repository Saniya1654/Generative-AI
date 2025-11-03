import json
import os
import argparse
from typing import List, Dict, Any

from ai_service import get_ai_generator


def load_recipes() -> List[Dict[str, Any]]:
	if os.path.exists('recipes.json'):
		with open('recipes.json', 'r', encoding='utf-8') as f:
			return json.load(f)
	return []


def matches_dietary_restrictions(recipe: Dict[str, Any], restrictions: List[str]) -> bool:
	if not restrictions:
		return True
	recipe_tags = recipe.get('tags', [])
	recipe_dietary = recipe.get('dietary_info', {})
	for restriction in restrictions:
		r = restriction.lower()
		if r == 'vegetarian' and (not recipe_dietary.get('vegetarian', False) and 'vegetarian' not in recipe_tags):
			return False
		if r == 'vegan' and (not recipe_dietary.get('vegan', False) and 'vegan' not in recipe_tags):
			return False
		if r == 'gluten-free' and (not recipe_dietary.get('gluten_free', False) and 'gluten-free' not in recipe_tags):
			return False
		if r == 'dairy-free' and (not recipe_dietary.get('dairy_free', False) and 'dairy-free' not in recipe_tags):
			return False
		if r == 'nut-free' and (not recipe_dietary.get('nut_free', False) and 'nut-free' not in recipe_tags):
			return False
		if r == 'low-carb' and (not recipe_dietary.get('low_carb', False) and 'low-carb' not in recipe_tags):
			return False
		if r == 'keto' and (not recipe_dietary.get('keto', False) and 'keto' not in recipe_tags):
			return False
	return True


def calculate_ingredient_match_score(recipe: Dict[str, Any], available_ingredients: List[str]) -> float:
	if not available_ingredients:
		return 1.0
	recipe_ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
	available_lower = [ing.lower() for ing in available_ingredients]
	matching = sum(1 for ing in recipe_ingredients if any(av in ing or ing in av for av in available_lower))
	total = len(recipe_ingredients)
	if total == 0:
		return 0.0
	score = matching / total
	if matching == total:
		score = 1.0
	return score


def filter_recipes(recipes: List[Dict[str, Any]], preferences: Dict[str, Any], dietary_restrictions: List[str], available_ingredients: List[str]) -> List[Dict[str, Any]]:
	filtered = []
	for recipe in recipes:
		if not matches_dietary_restrictions(recipe, dietary_restrictions):
			continue
		match_score = calculate_ingredient_match_score(recipe, available_ingredients)
		cuisine_match = True
		if preferences.get('cuisine'):
			recipe_cuisine = recipe.get('cuisine', '').lower()
			preferred_cuisine = preferences['cuisine'].lower()
			if preferred_cuisine not in recipe_cuisine:
				cuisine_match = False
		meal_type_match = True
		if preferences.get('meal_type'):
			recipe_meal_type = recipe.get('meal_type', '').lower()
			preferred_meal_type = preferences['meal_type'].lower()
			if preferred_meal_type not in recipe_meal_type:
				meal_type_match = False
		difficulty_match = True
		if preferences.get('difficulty'):
			recipe_difficulty = recipe.get('difficulty', '').lower()
			preferred_difficulty = preferences['difficulty'].lower()
			if recipe_difficulty != preferred_difficulty:
				difficulty_match = False
		preference_score = 1.0
		if not cuisine_match:
			preference_score *= 0.7
		if not meal_type_match:
			preference_score *= 0.7
		if not difficulty_match:
			preference_score *= 0.8
		final_score = match_score * 0.6 + preference_score * 0.4
		filtered.append({ 'recipe': recipe, 'score': final_score, 'ingredient_match': match_score, 'preference_match': preference_score })
	filtered.sort(key=lambda x: x['score'], reverse=True)
	return filtered


def print_recipe(recipe: Dict[str, Any]) -> None:
	print(f"\n=== {recipe.get('name', 'Recipe')} ===")
	print(f"Cuisine: {recipe.get('cuisine','N/A')}  |  Meal: {recipe.get('meal_type','N/A')}  |  Difficulty: {recipe.get('difficulty','N/A')}")
	print(f"Prep: {recipe.get('prep_time',0)} min  |  Cook: {recipe.get('cook_time',0)} min  |  Servings: {recipe.get('servings','N/A')}")
	dietary = recipe.get('dietary_info', {})
	if dietary:
		flags = [k.replace('_','-') for k,v in dietary.items() if v]
		print("Dietary:", ", ".join(flags))
	print("\nIngredients:")
	for ing in recipe.get('ingredients', []):
		print(f" - {ing}")
	print("\nSteps:")
	for i, step in enumerate(recipe.get('steps', []), start=1):
		print(f" {i}. {step}")


def main():
	parser = argparse.ArgumentParser(description='Recipe Assistant CLI (no server)')
	sub = parser.add_subparsers(dest='cmd')

	# recommend
	p_reco = sub.add_parser('recommend', help='Recommend recipes from local database')
	p_reco.add_argument('--cuisine', default='', help='Cuisine preference')
	p_reco.add_argument('--meal', dest='meal_type', default='', help='Meal type (Breakfast/Lunch/Dinner)')
	p_reco.add_argument('--difficulty', default='', help='Difficulty (Easy/Medium/Hard)')
	p_reco.add_argument('--diet', nargs='*', default=[], help='Dietary restrictions (e.g., vegan gluten-free)')
	p_reco.add_argument('--have', nargs='*', default=[], help='Available ingredients')
	p_reco.add_argument('--top', type=int, default=5, help='How many to show')

	# generate
	p_gen = sub.add_parser('generate', help='Generate a new recipe using AI')
	p_gen.add_argument('--cuisine', default='', help='Cuisine preference')
	p_gen.add_argument('--meal', dest='meal_type', default='', help='Meal type')
	p_gen.add_argument('--difficulty', default='', help='Difficulty')
	p_gen.add_argument('--diet', nargs='*', default=[], help='Dietary restrictions')
	p_gen.add_argument('--have', nargs='*', default=[], help='Available ingredients')

	# adapt
	p_adapt = sub.add_parser('adapt', help='Adapt an existing recipe by ID using AI')
	p_adapt.add_argument('id', type=int, help='Recipe ID to adapt')
	p_adapt.add_argument('--have', nargs='*', default=[], help='Available ingredients')

	# tips
	p_tips = sub.add_parser('tips', help='Get AI cooking tips for a recipe by ID')
	p_tips.add_argument('id', type=int, help='Recipe ID')

	args = parser.parse_args()

	ai = get_ai_generator()
	recipes = load_recipes()

	if args.cmd == 'recommend':
		preferences = { 'cuisine': args.cuisine, 'meal_type': args.meal_type, 'difficulty': args.difficulty }
		filtered = filter_recipes(recipes, preferences, args.diet, args.have)
		if not filtered:
			print('No matching recipes found.')
			return
		for item in filtered[: max(1, args.top)]:
			print_recipe(item['recipe'])
		return

	if args.cmd == 'generate':
		preferences = { 'cuisine': args.cuisine, 'meal_type': args.meal_type, 'difficulty': args.difficulty }
		recipe = ai.generate_recipe(preferences, args.diet, args.have)
		print_recipe(recipe)
		return

	if args.cmd == 'adapt':
		recipe = next((r for r in recipes if r.get('id') == args.id), None)
		if not recipe:
			print('Recipe not found.')
			return
		adapted = ai.adapt_recipe(recipe, args.have, substitutions={})
		print_recipe(adapted)
		return

	if args.cmd == 'tips':
		recipe = next((r for r in recipes if r.get('id') == args.id), None)
		if not recipe:
			print('Recipe not found.')
			return
		tips = ai.generate_cooking_tips(recipe)
		print('\nCooking Tips:')
		for i, tip in enumerate(tips, start=1):
			print(f" {i}. {tip}")
		return

	# default: show help
	parser.print_help()


if __name__ == '__main__':
	main()


