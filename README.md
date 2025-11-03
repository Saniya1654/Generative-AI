# 🤖 AI-Powered Recipe Assistant

A **Generative AI** project that can both suggest existing recipes and generate brand‑new ones based on your preferences, dietary restrictions, and available ingredients. It includes:
- A no‑server CLI (with interactive wizard)
- A FastAPI server (optional) exposing REST endpoints

## 🎯 Key Features

### AI-Powered Features
- ✨ **AI Recipe Generation**: Generate completely new, unique recipes using AI based on your ingredients and preferences
- 🔄 **AI Recipe Adaptation**: Adapt existing recipes to work with your available ingredients using intelligent substitutions
- 💡 **AI Cooking Tips**: Get personalized cooking tips and techniques for each recipe
- 🤖 **Dual AI Mode**: Works with OpenAI API or intelligent fallback generator

### Traditional Features
- 🎯 **Personalized Recommendations**: Get recipe suggestions from curated database
- 🥗 **Dietary Restrictions**: Filter by vegetarian, vegan, gluten-free, dairy-free, nut-free, low-carb, or keto
- 🥘 **Cuisine Preferences**: Choose from Italian, Indian, American, Japanese, Mexican, Mediterranean, Asian, or any
- 🍽️ **Meal Type**: Filter by Breakfast, Lunch, or Dinner
- 📊 **Difficulty Levels**: Easy, Medium, or Hard recipes
- 🧄 **Ingredient Matching**: Smart ingredient matching algorithm
- 📝 **Step-by-Step Instructions**: Detailed cooking instructions for each recipe
- 📱 **Responsive Design**: Beautiful, modern UI that works on all devices

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the recipe database (once):**
   ```bash
   python initialize_recipes.py
   ```

4. **Set up Google Gemini API (Optional but recommended):**
   - Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Set it as an environment variable:
     ```bash
     # Windows
     set GEMINI_API_KEY=your_api_key_here
     
     # Linux/Mac
     export GEMINI_API_KEY=your_api_key_here
     ```
   - Note: The system works without an API key using an intelligent fallback generator
   - Model: Uses Gemini 2.0 Flash Experimental by default (or 1.5 Flash as fallback)

## Usage

### No‑server (CLI)

- Interactive wizard (prompted input):
  ```bash
  python cli.py wizard
  ```

- Flags (one‑liners):
  - Recommend from local recipes
    ```bash
    python cli.py recommend --cuisine Indian --diet vegan --have rice tomatoes onions --top 3
    ```
  - Generate a brand‑new AI recipe
    ```bash
    python cli.py generate --meal Dinner --have rice egg "soy sauce"
    ```
  - Adapt an existing recipe by ID
    ```bash
    python cli.py adapt 1 --have zucchini basil pasta
    ```
  - Get AI cooking tips for a recipe
    ```bash
    python cli.py tips 1
    ```

### FastAPI server (optional)

- Start directly (no reload):
  ```bash
  python fastapi_app.py
  ```

- Or with auto‑reload (recommended during development):
  ```bash
  uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
  ```

- Test endpoints (Swagger UI):
  - Open `http://127.0.0.1:8000/docs`

- Example request body for POST `/api/recommend` or `/api/generate`:
  ```json
  {
    "preferences": { "cuisine": "Indian", "meal_type": "Dinner", "difficulty": "Easy" },
    "dietary_restrictions": ["vegan"],
    "available_ingredients": ["rice", "tomatoes", "onions", "garlic"]
  }
  ```

## How It Works

### AI‑Powered Recipe Generation

The system uses **Generative AI** to create recipes:

1. **Recipe Generation**: 
   - AI analyzes your available ingredients, preferences, and dietary restrictions
   - Generates a complete recipe with ingredients, steps, and cooking times
   - Uses OpenAI GPT models (if API key provided) or intelligent fallback generator

2. **Recipe Adaptation**:
   - AI intelligently substitutes ingredients in existing recipes
   - Adjusts cooking steps based on available ingredients
   - Maintains recipe integrity while working with what you have

3. **Cooking Tips**:
   - AI generates personalized tips based on recipe difficulty and type
   - Provides technique suggestions and best practices
   - Tailored to the specific recipe being viewed

### Matching Algorithm (Traditional Recipes)

- **Ingredient Matching (60% weight)**: Calculates how many recipe ingredients you have available
- **Preference Matching (40% weight)**: Matches cuisine, meal type, and difficulty preferences
- Results are sorted by combined relevance score

### AI Modes

- **Gemini Mode**: Requires API key, uses Google Gemini 2.0 Flash for high-quality recipe generation
- **Fallback Mode**: Works without API key, uses intelligent template-based generation

## Project Structure

```
.
├── ai_service.py           # AI service with Google Gemini and fallback generator
├── initialize_recipes.py   # Recipe database initialization
├── recipes.json            # Recipe database (generated)
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── cli.py                 # No‑server CLI (flags + interactive wizard)
└── fastapi_app.py         # FastAPI server
```

## Adding More Recipes

You can add more recipes by editing the `initialize_recipes.py` file and adding new recipe objects to the `recipes` list. Each recipe should include:

- `id`: Unique identifier
- `name`: Recipe name
- `cuisine`: Cuisine type
- `meal_type`: Breakfast, Lunch, or Dinner
- `difficulty`: Easy, Medium, or Hard
- `prep_time`: Preparation time in minutes
- `cook_time`: Cooking time in minutes
- `servings`: Number of servings
- `ingredients`: Array of ingredient names
- `steps`: Array of step-by-step instructions
- `dietary_info`: Object with dietary flags (vegetarian, vegan, gluten_free, etc.)
- `tags`: Array of tags for categorization

Then run `python initialize_recipes.py` again to regenerate the database.

## Technologies Used

- **Backend**: FastAPI (server) and Python CLI (no‑server)
- **AI/ML**: Google Gemini 2.0 Flash API (with fallback generator)
- **Storage**: JSON file-based database

## AI Implementation Details

- **ai_service.py**: Core AI service with Google Gemini integration and fallback
- **Gemini Integration**: Uses Gemini 2.0 Flash Experimental (or 1.5 Flash) for recipe generation
- **Fallback Generator**: Template-based AI that works without API keys
- **Smart Prompting**: Optimized prompts for recipe generation and adaptation
- **JSON Parsing**: Intelligent JSON extraction from AI responses

## Generate vs Recommend

- **Recommend**
  - Input: Preferences + dietary restrictions + available ingredients
  - Behavior: Filters and ranks recipes from the existing local dataset (`recipes.json`) using an ingredient‑match and preference‑match scoring algorithm
  - Output: Top matching existing recipes (no new recipe is created)

- **Generate**
  - Input: Preferences + dietary restrictions + available ingredients
  - Behavior: Uses Generative AI (Gemini) to create a brand‑new recipe tailored to your inputs (ingredients, cuisine, etc.)
  - Output: A newly generated recipe with ingredients, steps, times, and dietary flags (optionally followed by AI cooking tips)

## Future Enhancements

- User accounts and saved favorites
- Recipe rating and reviews
- Shopping list generation
- Nutrition information
- Image uploads for recipes
- Integration with grocery delivery services
- Machine learning for better recommendations

## License

This project is open source and available for educational purposes.

## Author

Created as a Gen AI Mini Project for recipe recommendation and cooking assistance.

