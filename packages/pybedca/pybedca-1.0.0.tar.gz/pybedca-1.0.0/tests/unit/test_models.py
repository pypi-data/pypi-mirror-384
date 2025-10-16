"""Unit tests for the data models module."""

import pytest
from decimal import Decimal

from pybedca.models import FoodValue, FoodNutrients, FoodPreview, Food
from pybedca.enums import BedcaComponent
from pybedca.values import Mass, Energy


class TestFoodValue:
    """Tests for the FoodValue model."""

    def test_food_value_creation_with_mass(self):
        """Test creating a FoodValue with mass value."""
        mass = Mass.from_value(10.5, "g")
        food_value = FoodValue(
            component=BedcaComponent.PROTEIN,
            value=mass,
            unit="g"
        )
        
        assert food_value.component == BedcaComponent.PROTEIN
        assert isinstance(food_value.value, Mass)
        assert food_value.unit == "g"

    def test_food_value_creation_with_energy(self):
        """Test creating a FoodValue with energy value."""
        energy = Energy.from_value(500, "kJ")
        food_value = FoodValue(
            component=BedcaComponent.ENERGY,
            value=energy,
            unit="kJ"
        )
        
        assert food_value.component == BedcaComponent.ENERGY
        assert isinstance(food_value.value, Energy)
        assert food_value.unit == "kJ"

    def test_food_value_creation_with_trace(self):
        """Test creating a FoodValue with trace value."""
        food_value = FoodValue(
            component=BedcaComponent.VITAMIN_D,
            value="trace",
            unit="ug"
        )
        
        assert food_value.component == BedcaComponent.VITAMIN_D
        assert food_value.value == "trace"
        assert food_value.unit == "ug"

    def test_food_value_from_raw_mass(self):
        """Test creating FoodValue from raw mass values."""
        food_value = FoodValue.from_raw(
            component=BedcaComponent.PROTEIN,
            value=12.37,
            unit="g"
        )
        
        assert food_value.component == BedcaComponent.PROTEIN
        assert isinstance(food_value.value, Mass)
        assert food_value.unit == "g"
        assert food_value.value.value == Decimal("12.37")

    def test_food_value_from_raw_energy(self):
        """Test creating FoodValue from raw energy values."""
        food_value = FoodValue.from_raw(
            component=BedcaComponent.ENERGY,
            value=719.15,
            unit="kJ"
        )
        
        assert food_value.component == BedcaComponent.ENERGY
        assert isinstance(food_value.value, Energy)
        assert food_value.unit == "kJ"

    def test_food_value_from_raw_trace(self):
        """Test creating FoodValue from raw trace values."""
        food_value = FoodValue.from_raw(
            component=BedcaComponent.VITAMIN_D,
            value="trace",
            unit="ug"
        )
        
        assert food_value.component == BedcaComponent.VITAMIN_D
        assert food_value.value == "trace"
        assert food_value.unit == "ug"

    def test_food_value_string_representation_mass(self):
        """Test string representation of FoodValue with mass."""
        food_value = FoodValue.from_raw(
            component=BedcaComponent.PROTEIN,
            value=12.37,
            unit="g"
        )
        
        str_repr = str(food_value)
        assert "12.37" in str_repr
        assert "g" in str_repr

    def test_food_value_string_representation_energy(self):
        """Test string representation of FoodValue with energy."""
        food_value = FoodValue.from_raw(
            component=BedcaComponent.ENERGY,
            value=719.15,
            unit="kJ"
        )
        
        str_repr = str(food_value)
        assert "kcal" in str_repr  # Energy displays in kcal by default

    def test_food_value_string_representation_trace(self):
        """Test string representation of FoodValue with trace."""
        food_value = FoodValue.from_raw(
            component=BedcaComponent.VITAMIN_D,
            value="trace",
            unit="ug"
        )
        
        str_repr = str(food_value)
        assert "trace" in str_repr.lower() or "traces" in str_repr.lower()
        assert "ug" in str_repr

    def test_food_value_string_representation_other_string(self):
        """Test string representation of FoodValue with other string values."""
        food_value = FoodValue(
            component=BedcaComponent.PROTEIN,
            value="unknown",
            unit="g"
        )
        
        str_repr = str(food_value)
        assert "unknown" in str_repr
        assert "g" in str_repr


class TestFoodPreview:
    """Tests for the FoodPreview model."""

    def test_food_preview_creation(self):
        """Test creating a FoodPreview object."""
        preview = FoodPreview(
            id="2597",
            name_es="Paella",
            name_en="Paella"
        )
        
        assert preview.id == "2597"
        assert preview.name_es == "Paella"
        assert preview.name_en == "Paella"

    def test_food_preview_with_different_names(self):
        """Test FoodPreview with different Spanish and English names."""
        preview = FoodPreview(
            id="2596",
            name_es="Paella marinera",
            name_en="Seafood paella"
        )
        
        assert preview.id == "2596"
        assert preview.name_es == "Paella marinera"
        assert preview.name_en == "Seafood paella"


class TestFoodNutrients:
    """Tests for the FoodNutrients model."""

    def test_food_nutrients_creation(self, sample_food_nutrients):
        """Test creating a FoodNutrients object."""
        nutrients = sample_food_nutrients
        
        # Test proximales
        assert isinstance(nutrients.energy, FoodValue)
        assert isinstance(nutrients.protein, FoodValue)
        assert isinstance(nutrients.fat, FoodValue)
        assert isinstance(nutrients.water, FoodValue)
        assert isinstance(nutrients.alcohol, FoodValue)
        
        # Test carbohydrates
        assert isinstance(nutrients.carbohydrate, FoodValue)
        assert isinstance(nutrients.fiber, FoodValue)
        
        # Test fats
        assert isinstance(nutrients.saturated_fat, FoodValue)
        assert isinstance(nutrients.monounsaturated_fat, FoodValue)
        assert isinstance(nutrients.polyunsaturated_fat, FoodValue)
        assert isinstance(nutrients.cholesterol, FoodValue)
        
        # Test vitamins
        assert isinstance(nutrients.vitamin_a, FoodValue)
        assert isinstance(nutrients.vitamin_c, FoodValue)
        assert isinstance(nutrients.vitamin_d, FoodValue)
        assert isinstance(nutrients.vitamin_e, FoodValue)
        assert isinstance(nutrients.thiamin, FoodValue)
        assert isinstance(nutrients.riboflavin, FoodValue)
        assert isinstance(nutrients.niacin, FoodValue)
        assert isinstance(nutrients.vitamin_b6, FoodValue)
        assert isinstance(nutrients.vitamin_b12, FoodValue)
        assert isinstance(nutrients.folate, FoodValue)
        
        # Test minerals
        assert isinstance(nutrients.calcium, FoodValue)
        assert isinstance(nutrients.iron, FoodValue)
        assert isinstance(nutrients.potassium, FoodValue)
        assert isinstance(nutrients.magnesium, FoodValue)
        assert isinstance(nutrients.sodium, FoodValue)
        assert isinstance(nutrients.phosphorus, FoodValue)
        assert isinstance(nutrients.iodide, FoodValue)
        assert isinstance(nutrients.selenium, FoodValue)
        assert isinstance(nutrients.zinc, FoodValue)

    def test_food_nutrients_component_mapping(self, sample_food_nutrients):
        """Test that nutrients have correct component mappings."""
        nutrients = sample_food_nutrients
        
        assert nutrients.energy.component == BedcaComponent.ENERGY
        assert nutrients.protein.component == BedcaComponent.PROTEIN
        assert nutrients.fat.component == BedcaComponent.FAT
        assert nutrients.carbohydrate.component == BedcaComponent.CARBOHYDRATE
        assert nutrients.vitamin_c.component == BedcaComponent.VITAMIN_C
        assert nutrients.calcium.component == BedcaComponent.CALCIUM

    def test_food_nutrients_value_types(self, sample_food_nutrients):
        """Test that nutrients have correct value types."""
        nutrients = sample_food_nutrients
        
        # Energy should be Energy type
        assert isinstance(nutrients.energy.value, Energy)
        
        # Mass nutrients should be Mass type
        assert isinstance(nutrients.protein.value, Mass)
        assert isinstance(nutrients.calcium.value, Mass)
        
        # Trace values should be strings
        assert nutrients.vitamin_d.value == "trace"


class TestFood:
    """Tests for the Food model."""

    def test_food_creation(self, sample_food):
        """Test creating a Food object."""
        food = sample_food
        
        assert food.id == "2597"
        assert food.name_es == "Paella"
        assert food.name_en == "Paella"
        assert food.scientific_name == ""
        assert isinstance(food.nutrients, FoodNutrients)

    def test_food_with_scientific_name(self):
        """Test Food object with scientific name."""
        nutrients = FoodNutrients(
            # Create minimal nutrients for test
            **{attr: FoodValue(None, Mass.from_value(0, "g"), "g") 
               for attr in [
                   'alcohol', 'energy', 'fat', 'protein', 'water',
                   'carbohydrate', 'fiber', 'monounsaturated_fat',
                   'polyunsaturated_fat', 'saturated_fat', 'cholesterol',
                   'vitamin_a', 'vitamin_d', 'vitamin_e', 'folate',
                   'niacin', 'riboflavin', 'thiamin', 'vitamin_b12',
                   'vitamin_b6', 'vitamin_c', 'calcium', 'iron',
                   'potassium', 'magnesium', 'sodium', 'phosphorus',
                   'iodide', 'selenium', 'zinc'
               ]}
        )
        # Override energy with proper Energy type
        nutrients.energy = FoodValue(BedcaComponent.ENERGY, Energy.from_value(0, "kJ"), "kJ")
        
        food = Food(
            id="123",
            name_es="Arroz",
            name_en="Rice",
            scientific_name="Oryza sativa",
            nutrients=nutrients
        )
        
        assert food.scientific_name == "Oryza sativa"

    def test_food_nutrient_access(self, sample_food):
        """Test accessing nutrients from Food object."""
        food = sample_food
        
        # Test direct access to nutrients
        assert food.nutrients.energy.component == BedcaComponent.ENERGY
        assert food.nutrients.protein.component == BedcaComponent.PROTEIN
        
        # Test that values are properly typed
        assert isinstance(food.nutrients.energy.value, Energy)
        assert isinstance(food.nutrients.protein.value, Mass)


@pytest.mark.unit
class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_complete_food_model_structure(self, sample_food):
        """Test that complete Food model has proper structure."""
        food = sample_food
        
        # Test basic properties
        assert isinstance(food.id, str)
        assert isinstance(food.name_es, str)
        assert isinstance(food.name_en, str)
        
        # Test nutrients structure
        nutrients = food.nutrients
        assert hasattr(nutrients, 'energy')
        assert hasattr(nutrients, 'protein')
        assert hasattr(nutrients, 'fat')
        
        # Test that all nutrients are FoodValue instances
        for attr_name in dir(nutrients):
            if not attr_name.startswith('_'):
                attr_value = getattr(nutrients, attr_name)
                if isinstance(attr_value, FoodValue):
                    assert hasattr(attr_value, 'component')
                    assert hasattr(attr_value, 'value')
                    assert hasattr(attr_value, 'unit')

    def test_food_value_consistency(self, sample_food):
        """Test that FoodValue objects are consistent."""
        food = sample_food
        
        # Test energy consistency
        energy = food.nutrients.energy
        assert energy.component == BedcaComponent.ENERGY
        assert energy.unit == "kJ"
        assert isinstance(energy.value, Energy)
        
        # Test mass consistency
        protein = food.nutrients.protein
        assert protein.component == BedcaComponent.PROTEIN
        assert protein.unit == "g"
        assert isinstance(protein.value, Mass)
        
        # Test trace consistency
        vitamin_d = food.nutrients.vitamin_d
        assert vitamin_d.component == BedcaComponent.VITAMIN_D
        assert vitamin_d.value == "trace"
        assert vitamin_d.unit == "ug"