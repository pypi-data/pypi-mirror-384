"""XML parser for BEDCA API responses."""

import xml.etree.ElementTree as ET

from .enums import BedcaAttribute, BedcaComponent
from .models import Food, FoodNutrients, FoodValue

COMPONENT_TO_FIELD_MAP = {
    BedcaComponent.ALCOHOL: 'alcohol',
    BedcaComponent.ENERGY: 'energy',
    BedcaComponent.FAT: 'fat',
    BedcaComponent.PROTEIN: 'protein',
    BedcaComponent.WATER: 'water',
    BedcaComponent.CARBOHYDRATE: 'carbohydrate',
    BedcaComponent.FIBER: 'fiber',
    BedcaComponent.MONOUNSATURATED: 'monounsaturated_fat',
    BedcaComponent.POLYUNSATURATED: 'polyunsaturated_fat',
    BedcaComponent.SATURATED: 'saturated_fat',
    BedcaComponent.CHOLESTEROL: 'cholesterol',
    BedcaComponent.VITAMIN_A: 'vitamin_a',
    BedcaComponent.VITAMIN_D: 'vitamin_d',
    BedcaComponent.VITAMIN_E: 'vitamin_e',
    BedcaComponent.FOLATE: 'folate',
    BedcaComponent.NIACIN: 'niacin',
    BedcaComponent.RIBOFLAVIN: 'riboflavin',
    BedcaComponent.THIAMIN: 'thiamin',
    BedcaComponent.VITAMIN_B12: 'vitamin_b12',
    BedcaComponent.VITAMIN_B6: 'vitamin_b6',
    BedcaComponent.VITAMIN_C: 'vitamin_c',
    BedcaComponent.CALCIUM: 'calcium',
    BedcaComponent.IRON: 'iron',
    BedcaComponent.POTASSIUM: 'potassium',
    BedcaComponent.MAGNESIUM: 'magnesium',
    BedcaComponent.SODIUM: 'sodium',
    BedcaComponent.PHOSPHORUS: 'phosphorus',
    BedcaComponent.IODIDE: 'iodide',
    BedcaComponent.SELENIUM: 'selenium',
    BedcaComponent.ZINC: 'zinc',
}



def parse_food_value(value_element: ET.Element) -> tuple[BedcaComponent, FoodValue]:
    """Parse a food value from an XML element."""
    try:
        component = BedcaComponent(value_element.find('c_eng_name').text)
    except ValueError:
        # Skip components that are not in our enum
        return None
    
    value_type = value_element.find(BedcaAttribute.VALUE_TYPE)
    if value_type is not None and value_type.text == 'TR':
        value = 'trace'
    else:
        value_text = value_element.find(BedcaAttribute.BEST_LOCATION).text
        try:
            value = float(value_text) if value_text else 0.0
        except (ValueError, TypeError):
            value = 0.0
    
    unit = value_element.find(BedcaAttribute.VALUE_UNIT).text

    food_value = FoodValue.from_raw(
        component=component,
        value=value,
        unit=unit
    )

    return component, food_value


def parse_food(element: ET.Element) -> Food:
    """Parse a food item from an XML element."""
    # Initialize default values for all nutrients
    default_value = FoodValue(component=None, value=0.0, unit='')
    nutrient_values = {comp: default_value for comp in COMPONENT_TO_FIELD_MAP.values()}

    # Parse all food values
    for value_element in element.findall('foodvalue'):
        result = parse_food_value(value_element)
        if result is None:
            continue
        
        component, food_value = result
        if component in COMPONENT_TO_FIELD_MAP:
            field_name = COMPONENT_TO_FIELD_MAP[component]
            nutrient_values[field_name] = food_value

    # Create food nutrients object
    nutrients = FoodNutrients(**nutrient_values)

    # Create and return the food object with safe attribute extraction
    def safe_text(element, attribute):
        """Safely extract text from an element, returning empty string if None."""
        found = element.find(attribute)
        return found.text if found is not None else ""
    
    return Food(
        id=safe_text(element, BedcaAttribute.ID),
        name_es=safe_text(element, BedcaAttribute.SPANISH_NAME),
        name_en=safe_text(element, BedcaAttribute.ENGLISH_NAME),
        scientific_name=safe_text(element, BedcaAttribute.SCIENTIFIC_NAME),
        nutrients=nutrients
    )


def parse_food_response(xml_string: str) -> Food:
    """Parse the food response from the BEDCA API."""
    root = ET.fromstring(xml_string)
    food_element = root.find('food')
    if food_element is None:
        raise ValueError("No food element found in XML")
    
    food = parse_food(food_element)
    
    # Check if the food has meaningful data (non-empty ID)
    if not food.id or food.id.strip() == "":
        raise ValueError("Food not found or invalid food ID")
    
    return food
