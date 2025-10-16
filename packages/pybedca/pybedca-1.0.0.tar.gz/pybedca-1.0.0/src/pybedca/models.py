"""Models for the BEDCA API client."""

from dataclasses import dataclass
from typing import Dict, Optional, Union

from .enums import BedcaComponent
from .values import Mass, Energy


@dataclass
class FoodValue:
    """Represents a nutritional value for a food component."""
    component: BedcaComponent
    value: Union[Mass, Energy, str]  # str for cases like 'trace'
    unit: str
    
    @classmethod
    def from_raw(cls, component: BedcaComponent, value: Union[float, str], unit: str) -> 'FoodValue':
        """Create a FoodValue instance from raw values."""
        if value == 'trace':
            processed_value = value
        elif component == BedcaComponent.ENERGY:
            processed_value = Energy.from_value(value, unit)
        else:
            # All other components are measured in mass units
            processed_value = Mass.from_value(value, unit)

        return cls(component=component, value=processed_value, unit=unit)
    
    def __str__(self) -> str:
        """Return string representation of the food value."""
        if isinstance(self.value, (Mass, Energy)):
            return str(self.value)
        if self.value.lower() == 'trace':
            return f"Traces {self.unit}"
        return f"{self.value} {self.unit}"


@dataclass
class FoodNutrients:
    """Contains all nutritional values for a food item."""
    # Proximales
    alcohol: FoodValue
    energy: FoodValue
    fat: FoodValue
    protein: FoodValue
    water: FoodValue

    # Hidratos de Carbono
    carbohydrate: FoodValue
    fiber: FoodValue

    # Grasas
    monounsaturated_fat: FoodValue
    polyunsaturated_fat: FoodValue
    saturated_fat: FoodValue
    cholesterol: FoodValue

    # Vitaminas
    vitamin_a: FoodValue
    vitamin_d: FoodValue
    vitamin_e: FoodValue
    folate: FoodValue
    niacin: FoodValue
    riboflavin: FoodValue
    thiamin: FoodValue
    vitamin_b12: FoodValue
    vitamin_b6: FoodValue
    vitamin_c: FoodValue

    # Minerales
    calcium: FoodValue
    iron: FoodValue
    potassium: FoodValue
    magnesium: FoodValue
    sodium: FoodValue
    phosphorus: FoodValue
    iodide: FoodValue
    selenium: FoodValue
    zinc: FoodValue


@dataclass
class FoodPreview:
    """Represents a food item in the BEDCA database."""
    id: str
    name_es: str
    name_en: str


@dataclass
class Food:
    """Represents a complete food item with all its nutritional values."""
    id: str
    name_es: str
    name_en: str
    scientific_name: Optional[str]
    nutrients: FoodNutrients