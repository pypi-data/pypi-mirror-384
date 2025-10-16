import re
from typing import List, Union

from mcp.server.fastmcp import FastMCP

from .enums import Languages
from .client import BedcaClient
from .models import Food


mcp = FastMCP("bedca")


@mcp.tool()
async def find_ingredient_by_name(search_query: str, language: Languages = Languages.ES) -> str:
    """
    Find ingredients by name using a simple substring (pattern) search.

    ⚠️ This search is not semantic — it only looks for partial text matches.  
    To get better results, use a single, general word instead of full phrases.  
    For example:
      - Use "pollo" instead of "muslo de pollo"  
      - Use "wine" instead of "white wine"

    The function returns a list of matching ingredients and their IDs.  
    You will need the ID to retrieve detailed nutritional information later.

    Args:
        search_query: A single word or partial term to search for in ingredient names.
        language: The language to search in: ES (Spanish) or EN (English). Default is ES.

    Returns:
        A human-readable list of possible ingredient matches and their IDs,
        or a message indicating that no matches were found.
    """
    labels_by_lang = {
        Languages.ES: {
            "attr_name": "name_es",
            "labels": {
                "matches_found": f"Coincidencias posibles para '{search_query}':",
                "not_matches": f"No se encontraron coincidencias para '{search_query}'. Intenta de nuevo"
            }
        },
        Languages.EN: {
            "attr_name": "name_en",
            "labels": {
                "matches_found": f"Possible matches for '{search_query}':",
                "not_matches": f"Not matches found for '{search_query}'. Try again"
            }
        }
    }
    async with BedcaClient() as bedca:
        ingredients = await bedca.search_food_by_name_async(search_query, language)
    lang_conf = labels_by_lang.get(language, labels_by_lang[Languages.EN])
    labels = lang_conf["labels"]

    if not ingredients:
        return labels["not_matches"]

    attr_name = lang_conf["attr_name"]
    # ingredients_dicts = [{"id": i.id, "name": getattr(i, attr_name)} for i in ingredients]

    return "\n".join([labels["matches_found"], *[f"{getattr(i, attr_name)} (ID: {i.id})" for i in ingredients]])


def format_food_nutritional_value(food: Food, language: Languages = Languages.ES) -> str:
    """Return a localized formatted nutritional summary for a Food object."""

    labels_by_lang = {
        Languages.ES: {
            "title": f"Valor nutricional de '{food.name_es}':",
            "labels": {
                "energy": "Valor Energético",
                "fat": "Grasas",
                "carbohydrate": "Hidratos de Carbono",
                "fiber": "Fibra",
                "protein": "Proteínas",
                "salt": "Sal",
            },
        },
        Languages.EN: {
            "title": f"Nutritional value of '{food.name_en or food.name_es}':",
            "labels": {
                "energy": "Energy",
                "fat": "Fat",
                "carbohydrate": "Carbohydrates",
                "fiber": "Fiber",
                "protein": "Protein",
                "salt": "Salt",
            },
        },
    }

    if not food:
        return
    # Elegimos idioma, por defecto inglés
    lang_conf = labels_by_lang.get(language, labels_by_lang[Languages.EN])
    labels = lang_conf["labels"]

    # Mapeo de campos -> atributo de food.nutrients
    nutrient_map = {
        "energy": "energy",
        "fat": "fat",
        "carbohydrate": "carbohydrate",
        "fiber": "fiber",
        "protein": "protein",
        "salt": "sodium",  # “Sal” = sodio
    }

    # Generamos líneas con valores seguros
    lines = [lang_conf["title"]]
    for label_key, attr in nutrient_map.items():
        nutrient = getattr(food.nutrients, attr, None)
        value = str(nutrient) if nutrient else "N/A"
        lines.append(f"{labels[label_key]}: {value}")

    return "\n".join(lines)


@mcp.tool()
async def get_ingredient_nutritional_info(ingredient_id: int, language: Languages = Languages.ES) -> str:
    """
    Retrieve the nutritional information for a specific ingredient by its ID.

    To obtain the correct ingredient ID, use 'find_ingredient_by_name' first.  
    Then, provide that ID here to get the nutritional breakdown (energy, fat, protein, etc.).  
    Results are formatted in the selected language.

    Args:
        ingredient_id: The unique integer ID of the ingredient (from 'find_ingredient_by_name').
        language: The language for the nutritional information: ES (Spanish) or EN (English). Default is ES.

    Returns:
        A formatted summary of the ingredient's nutritional values,
        or a message if the ingredient ID was not found.
    """
    not_found = {
        Languages.ES: f"Ingrediente con ID {ingredient_id} no encontrado.",
        Languages.EN: f"Ingredient with ID {ingredient_id} not found.",
    }

    try:
        async with BedcaClient() as bedca:
            ingredient = await bedca.get_food_by_id_async(ingredient_id)
    except ValueError:
        return not_found[language]
    return format_food_nutritional_value(ingredient, language)


def main():
    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
