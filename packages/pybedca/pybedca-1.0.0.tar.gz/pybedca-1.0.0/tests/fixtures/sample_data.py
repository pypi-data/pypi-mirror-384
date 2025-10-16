"""Sample data objects for pybedca tests."""

from typing import List

from pybedca.models import FoodPreview, Food, FoodNutrients, FoodValue
from pybedca.enums import BedcaComponent
from pybedca.values import Mass, Energy


def get_sample_food_previews() -> List[FoodPreview]:
    """Get sample FoodPreview objects based on search response."""
    return [
        FoodPreview(
            id="2597",
            name_es="Paella",
            name_en="Paella"
        ),
        FoodPreview(
            id="2596", 
            name_es="Paella marinera",
            name_en="Seafood paella"
        )
    ]


def get_sample_food_value() -> FoodValue:
    """Get a sample FoodValue object."""
    return FoodValue(
        component=BedcaComponent.PROTEIN,
        value=Mass.from_value(12.37, "g"),
        unit="g"
    )


def get_sample_energy_value() -> FoodValue:
    """Get a sample energy FoodValue object."""
    return FoodValue(
        component=BedcaComponent.ENERGY,
        value=Energy.from_value(719.15, "kJ"),
        unit="kJ"
    )


def get_sample_trace_value() -> FoodValue:
    """Get a sample trace FoodValue object."""
    return FoodValue(
        component=BedcaComponent.VITAMIN_D,
        value="trace",
        unit="ug"
    )


def get_sample_food_nutrients() -> FoodNutrients:
    """Get sample FoodNutrients with realistic values."""
    # Create default values for all nutrients
    default_mass = Mass.from_value(0.0, "g")
    default_energy = Energy.from_value(0.0, "kJ")
    
    return FoodNutrients(
        # Proximales
        alcohol=FoodValue(BedcaComponent.ALCOHOL, default_mass, "g"),
        energy=FoodValue(BedcaComponent.ENERGY, Energy.from_value(719.15, "kJ"), "kJ"),
        fat=FoodValue(BedcaComponent.FAT, Mass.from_value(5.74, "g"), "g"),
        protein=FoodValue(BedcaComponent.PROTEIN, Mass.from_value(12.37, "g"), "g"),
        water=FoodValue(BedcaComponent.WATER, Mass.from_value(63.95, "g"), "g"),
        
        # Hidratos de Carbono
        carbohydrate=FoodValue(BedcaComponent.CARBOHYDRATE, Mass.from_value(17.44, "g"), "g"),
        fiber=FoodValue(BedcaComponent.FIBER, Mass.from_value(0.5, "g"), "g"),
        
        # Grasas
        monounsaturated_fat=FoodValue(BedcaComponent.MONOUNSATURATED, Mass.from_value(2.98, "g"), "g"),
        polyunsaturated_fat=FoodValue(BedcaComponent.POLYUNSATURATED, Mass.from_value(0.75, "g"), "g"),
        saturated_fat=FoodValue(BedcaComponent.SATURATED, Mass.from_value(1.1, "g"), "g"),
        cholesterol=FoodValue(BedcaComponent.CHOLESTEROL, Mass.from_value(44.81, "mg"), "mg"),
        
        # Vitaminas
        vitamin_a=FoodValue(BedcaComponent.VITAMIN_A, Mass.from_value(11.12, "ug"), "ug"),
        vitamin_d=FoodValue(BedcaComponent.VITAMIN_D, "trace", "ug"),
        vitamin_e=FoodValue(BedcaComponent.VITAMIN_E, Mass.from_value(0.63, "mg"), "mg"),
        folate=FoodValue(BedcaComponent.FOLATE, Mass.from_value(11.75, "ug"), "ug"),
        niacin=FoodValue(BedcaComponent.NIACIN, Mass.from_value(4.21, "mg"), "mg"),
        riboflavin=FoodValue(BedcaComponent.RIBOFLAVIN, Mass.from_value(0.1, "mg"), "mg"),
        thiamin=FoodValue(BedcaComponent.THIAMIN, Mass.from_value(0.07, "mg"), "mg"),
        vitamin_b12=FoodValue(BedcaComponent.VITAMIN_B12, Mass.from_value(0.54, "ug"), "ug"),
        vitamin_b6=FoodValue(BedcaComponent.VITAMIN_B6, Mass.from_value(0.25, "mg"), "mg"),
        vitamin_c=FoodValue(BedcaComponent.VITAMIN_C, Mass.from_value(7.73, "mg"), "mg"),
        
        # Minerales
        calcium=FoodValue(BedcaComponent.CALCIUM, Mass.from_value(27.22, "mg"), "mg"),
        iron=FoodValue(BedcaComponent.IRON, Mass.from_value(1.28, "mg"), "mg"),
        potassium=FoodValue(BedcaComponent.POTASSIUM, Mass.from_value(123.81, "mg"), "mg"),
        magnesium=FoodValue(BedcaComponent.MAGNESIUM, Mass.from_value(21.23, "mg"), "mg"),
        sodium=FoodValue(BedcaComponent.SODIUM, Mass.from_value(47.83, "mg"), "mg"),
        phosphorus=FoodValue(BedcaComponent.PHOSPHORUS, Mass.from_value(72.11, "mg"), "mg"),
        iodide=FoodValue(BedcaComponent.IODIDE, Mass.from_value(14.29, "ug"), "ug"),
        selenium=FoodValue(BedcaComponent.SELENIUM, Mass.from_value(0.0, "ug"), "ug"),
        zinc=FoodValue(BedcaComponent.ZINC, Mass.from_value(0.98, "mg"), "mg"),
    )


def get_sample_food() -> Food:
    """Get a sample Food object with complete data."""
    return Food(
        id="2597",
        name_es="Paella",
        name_en="Paella",
        scientific_name="",
        nutrients=get_sample_food_nutrients()
    )
