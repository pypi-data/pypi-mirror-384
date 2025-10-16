"""Unit tests for the XML parser module."""

import pytest
import xml.etree.ElementTree as ET
from decimal import Decimal

from pybedca.parser import parse_food_response, parse_food, parse_food_value
from pybedca.models import Food, FoodValue
from pybedca.enums import BedcaComponent
from pybedca.values import Mass, Energy


class TestParseFood:
    """Tests for the parse_food function."""

    def test_parse_food_from_complete_response(self, xml_food_response):
        """Test parsing a complete food response."""
        food = parse_food_response(xml_food_response)
        
        assert isinstance(food, Food)
        assert food.id == "2597"
        assert food.name_es == "Paella"
        assert food.name_en == "Paella"
        assert food.scientific_name == None
        
        # Check that nutrients are properly parsed
        assert food.nutrients is not None
        assert isinstance(food.nutrients.energy.value, Energy)
        assert isinstance(food.nutrients.protein.value, Mass)

    def test_parse_food_energy_values(self, xml_food_response):
        """Test that energy values are parsed correctly."""
        food = parse_food_response(xml_food_response)
        
        energy = food.nutrients.energy
        assert energy.component == BedcaComponent.ENERGY
        assert isinstance(energy.value, Energy)
        assert energy.unit == "kJ"
        
        # Check the actual energy value (719.15 kJ)
        assert abs(energy.value.kj - Decimal("719.15")) < Decimal("0.01")

    def test_parse_food_mass_values(self, xml_food_response):
        """Test that mass values are parsed correctly."""
        food = parse_food_response(xml_food_response)
        
        protein = food.nutrients.protein
        assert protein.component == BedcaComponent.PROTEIN
        assert isinstance(protein.value, Mass)
        assert protein.unit == "g"
        
        # Check the actual protein value (12.37 g)
        assert abs(protein.value.value - Decimal("12.37")) < Decimal("0.01")

    def test_parse_food_trace_values(self, xml_food_response):
        """Test that trace values are handled correctly."""
        food = parse_food_response(xml_food_response)
        
        vitamin_d = food.nutrients.vitamin_d
        assert vitamin_d.component == BedcaComponent.VITAMIN_D
        assert vitamin_d.value == "trace"
        assert vitamin_d.unit == "ug"

    def test_parse_food_different_units(self, xml_food_response):
        """Test parsing values with different units."""
        food = parse_food_response(xml_food_response)
        
        # Test milligram values
        cholesterol = food.nutrients.cholesterol
        assert cholesterol.unit == "mg"
        assert isinstance(cholesterol.value, Mass)
        
        # Test microgram values
        vitamin_a = food.nutrients.vitamin_a
        assert vitamin_a.unit == "ug"
        assert isinstance(vitamin_a.value, Mass)

    def test_parse_food_missing_element_raises_error(self):
        """Test that missing food element raises ValueError."""
        xml_without_food = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse>
            <componentList>
                <component>
                    <id>404</id>
                    <name_esp>alcohol (etanol)</name_esp>
                </component>
            </componentList>
        </foodresponse>"""
        
        with pytest.raises(ValueError, match="No food element found in XML"):
            parse_food_response(xml_without_food)

    def test_parse_food_invalid_xml_raises_error(self):
        """Test that invalid XML raises appropriate error."""
        invalid_xml = "This is not valid XML"
        
        with pytest.raises(ET.ParseError):
            parse_food_response(invalid_xml)


class TestParseFoodValue:
    """Tests for the parse_food_value function."""

    def test_parse_regular_food_value(self):
        """Test parsing a regular food value."""
        xml_element = ET.fromstring("""
        <foodvalue>
            <c_eng_name>protein, total</c_eng_name>
            <best_location>12.37</best_location>
            <v_unit>g</v_unit>
            <value_type>AR</value_type>
        </foodvalue>
        """)
        
        component, food_value = parse_food_value(xml_element)
        
        assert component == BedcaComponent.PROTEIN
        assert isinstance(food_value, FoodValue)
        assert food_value.component == BedcaComponent.PROTEIN
        assert isinstance(food_value.value, Mass)
        assert food_value.unit == "g"

    def test_parse_energy_food_value(self):
        """Test parsing an energy food value."""
        xml_element = ET.fromstring("""
        <foodvalue>
            <c_eng_name>energy, total metabolisable calculated from energy-producing food components</c_eng_name>
            <best_location>719.15</best_location>
            <v_unit>kJ</v_unit>
            <value_type>BE</value_type>
        </foodvalue>
        """)
        
        component, food_value = parse_food_value(xml_element)
        
        assert component == BedcaComponent.ENERGY
        assert isinstance(food_value.value, Energy)
        assert food_value.unit == "kJ"

    def test_parse_trace_food_value(self):
        """Test parsing a trace food value."""
        xml_element = ET.fromstring("""
        <foodvalue>
            <c_eng_name>vitamin D</c_eng_name>
            <best_location></best_location>
            <v_unit>ug</v_unit>
            <value_type>TR</value_type>
        </foodvalue>
        """)
        
        component, food_value = parse_food_value(xml_element)
        
        assert component == BedcaComponent.VITAMIN_D
        assert food_value.value == "trace"
        assert food_value.unit == "ug"

    def test_parse_unknown_component_returns_none(self):
        """Test that unknown components return None."""
        xml_element = ET.fromstring("""
        <foodvalue>
            <c_eng_name>unknown component</c_eng_name>
            <best_location>10.0</best_location>
            <v_unit>g</v_unit>
            <value_type>AR</value_type>
        </foodvalue>
        """)
        
        result = parse_food_value(xml_element)
        assert result is None

    def test_parse_empty_value_defaults_to_zero(self):
        """Test that empty values default to zero."""
        xml_element = ET.fromstring("""
        <foodvalue>
            <c_eng_name>protein, total</c_eng_name>
            <best_location></best_location>
            <v_unit>g</v_unit>
            <value_type>AR</value_type>
        </foodvalue>
        """)
        
        component, food_value = parse_food_value(xml_element)
        
        assert component == BedcaComponent.PROTEIN
        assert food_value.value.value == Decimal("0.0")

    def test_parse_invalid_numeric_value_defaults_to_zero(self):
        """Test that invalid numeric values default to zero."""
        xml_element = ET.fromstring("""
        <foodvalue>
            <c_eng_name>protein, total</c_eng_name>
            <best_location>not_a_number</best_location>
            <v_unit>g</v_unit>
            <value_type>AR</value_type>
        </foodvalue>
        """)
        
        component, food_value = parse_food_value(xml_element)
        
        assert component == BedcaComponent.PROTEIN
        assert food_value.value.value == Decimal("0.0")


@pytest.mark.unit
class TestParserIntegration:
    """Integration tests for the parser module."""

    def test_parse_complete_food_response_structure(self, xml_food_response):
        """Test that the complete parsing process produces correct structure."""
        food = parse_food_response(xml_food_response)
        
        # Verify all major nutrient categories are present
        nutrients = food.nutrients
        
        # Proximales
        assert hasattr(nutrients, 'energy')
        assert hasattr(nutrients, 'protein')
        assert hasattr(nutrients, 'fat')
        assert hasattr(nutrients, 'water')
        assert hasattr(nutrients, 'alcohol')
        
        # Carbohydrates
        assert hasattr(nutrients, 'carbohydrate')
        assert hasattr(nutrients, 'fiber')
        
        # Fats
        assert hasattr(nutrients, 'saturated_fat')
        assert hasattr(nutrients, 'monounsaturated_fat')
        assert hasattr(nutrients, 'polyunsaturated_fat')
        assert hasattr(nutrients, 'cholesterol')
        
        # Vitamins
        assert hasattr(nutrients, 'vitamin_a')
        assert hasattr(nutrients, 'vitamin_c')
        assert hasattr(nutrients, 'vitamin_d')
        assert hasattr(nutrients, 'vitamin_e')
        
        # Minerals
        assert hasattr(nutrients, 'calcium')
        assert hasattr(nutrients, 'iron')
        assert hasattr(nutrients, 'sodium')
        assert hasattr(nutrients, 'potassium')

    def test_food_value_string_representations(self, xml_food_response):
        """Test that FoodValue string representations work correctly."""
        food = parse_food_response(xml_food_response)
        
        # Test regular value
        protein_str = str(food.nutrients.protein)
        assert "12.37" in protein_str
        assert "g" in protein_str
        
        # Test energy value
        energy_str = str(food.nutrients.energy)
        assert "kcal" in energy_str
        
        # Test trace value
        vitamin_d_str = str(food.nutrients.vitamin_d)
        assert "trace" in vitamin_d_str.lower() or "traces" in vitamin_d_str.lower()