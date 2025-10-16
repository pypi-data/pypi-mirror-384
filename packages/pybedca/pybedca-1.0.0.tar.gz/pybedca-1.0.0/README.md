# pybedca

Python client library for the BEDCA API (Base de Datos Española de Composición de Alimentos - Spanish Food Composition Database). This library provides a clean, Pythonic interface to query the BEDCA database and parse XML responses into structured Python objects with proper nutritional data handling.

## Features

- 🥗 **Complete Food Database Access**: Query the comprehensive Spanish food composition database
- 🔍 **Flexible Search**: Search foods by name in Spanish or English
- 📊 **Rich Nutritional Data**: Access detailed nutritional information including macronutrients, vitamins, and minerals
- 🔄 **Unit Conversions**: Automatic handling of different measurement units (grams, milligrams, micrograms, kJ, kcal)
- 🐍 **Pythonic API**: Clean, intuitive interface with proper type hints
- 📝 **Structured Data**: Well-defined data models for easy data manipulation

## Installation

Install pybedca using pip:

```bash
pip install pybedca
```

For development with testing dependencies:

```bash
pip install pybedca[test]
```

## Quick Start

```python
from pybedca import BedcaClient

# Initialize the client
client = BedcaClient()

# Search for foods by name
paella_foods = client.search_food_by_name("paella")
print(f"Found {len(paella_foods)} paella recipes")

# Get detailed nutritional information
if paella_foods:
    food_id = int(paella_foods[0].id)
    detailed_food = client.get_food_by_id(food_id)
    
    print(f"Food: {detailed_food.name_es}")
    print(f"Energy: {detailed_food.nutrients.energy}")
    print(f"Protein: {detailed_food.nutrients.protein}")
    print(f"Carbohydrates: {detailed_food.nutrients.carbohydrate}")
```

## Usage Examples

### Searching for Foods

#### Search by Spanish Name
```python
from pybedca import BedcaClient
from pybedca.enums import Languages

client = BedcaClient()

# Search in Spanish (default)
results = client.search_food_by_name("arroz")
for food in results:
    print(f"ID: {food.id}, Spanish: {food.name_es}, English: {food.name_en}")
```

#### Search by English Name
```python
# Search in English
results = client.search_food_by_name("rice", language=Languages.EN)
for food in results:
    print(f"ID: {food.id}, Spanish: {food.name_es}, English: {food.name_en}")
```

### Getting Detailed Food Information

```python
# Get detailed nutritional information for a specific food
food = client.get_food_by_id(2597)  # Paella

print(f"Food: {food.name_es} ({food.name_en})")
print(f"Scientific name: {food.scientific_name}")

# Access nutritional information
nutrients = food.nutrients
print(f"\nNutritional Information (per 100g):")
print(f"Energy: {nutrients.energy}")
print(f"Protein: {nutrients.protein}")
print(f"Fat: {nutrients.fat}")
print(f"Carbohydrates: {nutrients.carbohydrate}")
print(f"Fiber: {nutrients.fiber}")

# Access vitamins
print(f"\nVitamins:")
print(f"Vitamin C: {nutrients.vitamin_c}")
print(f"Vitamin A: {nutrients.vitamin_a}")
print(f"Vitamin E: {nutrients.vitamin_e}")

# Access minerals
print(f"\nMinerals:")
print(f"Calcium: {nutrients.calcium}")
print(f"Iron: {nutrients.iron}")
print(f"Sodium: {nutrients.sodium}")
```

### Working with Nutritional Values

The library provides rich value objects that handle unit conversions automatically:

```python
food = client.get_food_by_id(2597)

# Energy values can be accessed in different units
energy = food.nutrients.energy.value
print(f"Energy: {energy.kcal} kcal")  # Kilocalories
print(f"Energy: {energy.kj} kJ")     # Kilojoules

# Mass values support unit conversion
protein = food.nutrients.protein.value
print(f"Protein: {protein.to_unit('g')} g")      # Grams
print(f"Protein: {protein.to_unit('mg')} mg")    # Milligrams

# Handle trace amounts
vitamin_d = food.nutrients.vitamin_d
if vitamin_d.value == 'trace':
    print("Vitamin D: Trace amounts")
else:
    print(f"Vitamin D: {vitamin_d}")
```

### Getting All Foods

```python
# Get all available foods (this may take a while and return many results)
all_foods = client.get_all_foods()
print(f"Total foods in database: {len(all_foods)}")

# Filter foods by name pattern
rice_foods = [food for food in all_foods if 'arroz' in food.name_es.lower()]
print(f"Rice-related foods: {len(rice_foods)}")
```

## API Reference

### BedcaClient

The main client class for interacting with the BEDCA API.

#### Methods

##### `__init__()`
Initialize a new BEDCA client.

##### `get_all_foods() -> List[FoodPreview]`
Retrieve all food items from the BEDCA database.

**Returns:** List of `FoodPreview` objects containing basic food information.

##### `search_food_by_name(search_query: str, language: Languages = Languages.ES) -> List[FoodPreview]`
Search for foods by name.

**Parameters:**
- `search_query`: The search term
- `language`: Search language (Spanish or English)

**Returns:** List of `FoodPreview` objects matching the search criteria.

##### `get_food_by_id(food_id: int) -> Food`
Get detailed nutritional information for a specific food.

**Parameters:**
- `food_id`: The unique identifier of the food item

**Returns:** `Food` object with complete nutritional data.

### Data Models

#### FoodPreview
Basic food information returned by search operations.

**Attributes:**
- `id: str` - Unique food identifier
- `name_es: str` - Spanish name
- `name_en: str` - English name

#### Food
Complete food information with nutritional data.

**Attributes:**
- `id: str` - Unique food identifier
- `name_es: str` - Spanish name
- `name_en: str` - English name
- `scientific_name: Optional[str]` - Scientific name
- `nutrients: FoodNutrients` - Nutritional information

#### FoodNutrients
Comprehensive nutritional information.

**Attributes:**
- **Macronutrients:** `energy`, `protein`, `fat`, `carbohydrate`, `fiber`, `water`, `alcohol`
- **Fats:** `saturated_fat`, `monounsaturated_fat`, `polyunsaturated_fat`, `cholesterol`
- **Vitamins:** `vitamin_a`, `vitamin_d`, `vitamin_e`, `vitamin_c`, `thiamin`, `riboflavin`, `niacin`, `vitamin_b6`, `vitamin_b12`, `folate`
- **Minerals:** `calcium`, `iron`, `magnesium`, `phosphorus`, `potassium`, `sodium`, `zinc`, `selenium`, `iodide`

#### FoodValue
Represents a nutritional value with proper unit handling.

**Attributes:**
- `component: BedcaComponent` - The nutritional component
- `value: Union[Mass, Energy, str]` - The value (with unit conversion support)
- `unit: str` - The original unit

### Value Types

#### Mass
Handles mass-based nutritional values with unit conversion.

**Methods:**
- `to_unit(unit: str) -> Decimal` - Convert to specified unit
- `value -> Decimal` - Get value in original unit

#### Energy
Handles energy values with automatic kJ/kcal conversion.

**Properties:**
- `kcal -> Decimal` - Value in kilocalories
- `kj -> Decimal` - Value in kilojoules

## Error Handling

The library raises appropriate exceptions for common error scenarios:

```python
from pybedca import BedcaClient
import requests

client = BedcaClient()

try:
    food = client.get_food_by_id(999999)  # Non-existent ID
except requests.HTTPError as e:
    print(f"HTTP error: {e}")
except ValueError as e:
    print(f"Data parsing error: {e}")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -e .[test]`
3. Run tests: `pytest`
4. Check coverage: `pytest --cov=src/pybedca --cov-report=html`

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with coverage
pytest --cov=src/pybedca --cov-report=html
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- BEDCA (Base de Datos Española de Composición de Alimentos) for providing the comprehensive food composition database
- The Spanish Agency for Food Safety and Nutrition (AESAN) for maintaining the BEDCA database
