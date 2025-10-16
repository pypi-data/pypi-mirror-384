"""Unit tests for the enums module."""

import pytest

from pybedca.enums import BedcaComponent, BedcaAttribute, BedcaRelation, Languages


class TestBedcaComponent:
    """Tests for the BedcaComponent enum."""

    def test_bedca_component_proximales(self):
        """Test proximales (macronutrient) components."""
        assert BedcaComponent.ALCOHOL == "alcohol (ethanol)"
        assert BedcaComponent.ENERGY == "energy, total metabolisable calculated from energy-producing food components"
        assert BedcaComponent.FAT == "fat, total (total lipid)"
        assert BedcaComponent.PROTEIN == "protein, total"
        assert BedcaComponent.WATER == "water (moisture)"

    def test_bedca_component_carbohydrates(self):
        """Test carbohydrate components."""
        assert BedcaComponent.CARBOHYDRATE == "carbohydrate"
        assert BedcaComponent.FIBER == "fibre, total dietary"

    def test_bedca_component_fats(self):
        """Test fat components."""
        assert BedcaComponent.MONOUNSATURATED == "fatty acids, total monounsaturated"
        assert BedcaComponent.POLYUNSATURATED == "fatty acids, total polyunsaturated"
        assert BedcaComponent.SATURATED == "fatty acids, total saturated"
        assert BedcaComponent.CHOLESTEROL == "cholesterol"

    def test_bedca_component_vitamins(self):
        """Test vitamin components."""
        assert BedcaComponent.VITAMIN_A == "vitamin A retinol equiv from retinol and carotenoid activities"
        assert BedcaComponent.VITAMIN_D == "vitamin D"
        assert BedcaComponent.VITAMIN_E == "vitamin E alpha-tocopherol equiv from E vitamer activities"
        assert BedcaComponent.FOLATE == "folate, total"
        assert BedcaComponent.NIACIN == "niacin equivalents, total"
        assert BedcaComponent.RIBOFLAVIN == "riboflavin"
        assert BedcaComponent.THIAMIN == "thiamin"
        assert BedcaComponent.VITAMIN_B12 == "vitamin B-12"
        assert BedcaComponent.VITAMIN_B6 == "vitamin B-6, total"
        assert BedcaComponent.VITAMIN_C == "vitamin C (ascorbic acid)"

    def test_bedca_component_minerals(self):
        """Test mineral components."""
        assert BedcaComponent.CALCIUM == "calcium"
        assert BedcaComponent.IRON == "iron, total"
        assert BedcaComponent.POTASSIUM == "potassium"
        assert BedcaComponent.MAGNESIUM == "magnesium"
        assert BedcaComponent.SODIUM == "sodium"
        assert BedcaComponent.PHOSPHORUS == "phosphorus"
        assert BedcaComponent.IODIDE == "iodide"
        assert BedcaComponent.SELENIUM == "selenium, total"
        assert BedcaComponent.ZINC == "zinc"

    def test_bedca_component_enum_behavior(self):
        """Test that BedcaComponent behaves as a proper enum."""
        # Test that we can create from string value
        protein = BedcaComponent("protein, total")
        assert protein == BedcaComponent.PROTEIN
        
        # Test that invalid values raise ValueError
        with pytest.raises(ValueError):
            BedcaComponent("invalid component")

    def test_bedca_component_iteration(self):
        """Test that we can iterate over BedcaComponent values."""
        components = list(BedcaComponent)
        
        # Should have all expected components
        assert len(components) > 20  # We have many components
        assert BedcaComponent.PROTEIN in components
        assert BedcaComponent.ENERGY in components
        assert BedcaComponent.VITAMIN_C in components
        assert BedcaComponent.CALCIUM in components

    def test_bedca_component_string_representation(self):
        """Test string representation of BedcaComponent."""
        assert str(BedcaComponent.PROTEIN) == "protein, total"
        assert str(BedcaComponent.ENERGY) == "energy, total metabolisable calculated from energy-producing food components"


class TestBedcaAttribute:
    """Tests for the BedcaAttribute enum."""

    def test_bedca_attribute_food_attributes(self):
        """Test food-related attributes."""
        assert BedcaAttribute.ID == "f_id"
        assert BedcaAttribute.SPANISH_NAME == "f_ori_name"
        assert BedcaAttribute.ENGLISH_NAME == "f_eng_name"
        assert BedcaAttribute.SCIENTIFIC_NAME == "sci_name"
        assert BedcaAttribute.LANGUAL == "langual"
        assert BedcaAttribute.ORIGIN == "f_origen"
        assert BedcaAttribute.PUBLIC == "publico"

    def test_bedca_attribute_component_attributes(self):
        """Test component-related attributes."""
        assert BedcaAttribute.COMPONENT_ID == "c_id"
        assert BedcaAttribute.COMPONENT_NAME_ES == "c_ori_name"
        assert BedcaAttribute.COMPONENT_NAME_EN == "c_eng_name"
        assert BedcaAttribute.COMPONENT_GROUP_ID == "componentgroup_id"
        assert BedcaAttribute.BEST_LOCATION == "best_location"
        assert BedcaAttribute.VALUE_UNIT == "v_unit"
        assert BedcaAttribute.VALUE_TYPE == "value_type"

    def test_bedca_attribute_description_attributes(self):
        """Test description-related attributes."""
        assert BedcaAttribute.DESCRIPTION_ES == "f_des_esp"
        assert BedcaAttribute.DESCRIPTION_EN == "f_des_ing"
        assert BedcaAttribute.GLOSSARY_ES == "glos_esp"
        assert BedcaAttribute.GLOSSARY_EN == "glos_ing"

    def test_bedca_attribute_classification_attributes(self):
        """Test classification-related attributes."""
        assert BedcaAttribute.FOODEX_CODE == "foodexcode"
        assert BedcaAttribute.MAIN_LEVEL_CODE == "mainlevelcode"
        assert BedcaAttribute.CODE_LEVEL_1 == "codlevel1"
        assert BedcaAttribute.NAME_LEVEL_1 == "namelevel1"
        assert BedcaAttribute.CODE_LEVEL_2 == "codlevel2"
        assert BedcaAttribute.NAME_LEVEL_2 == "namelevel2"

    def test_bedca_attribute_statistical_attributes(self):
        """Test statistical and measurement attributes."""
        assert BedcaAttribute.STANDARD_DEVIATION == "stdv"
        assert BedcaAttribute.MIN_VALUE == "min"
        assert BedcaAttribute.MAX_VALUE == "max"
        assert BedcaAttribute.N_VALUE == "v_n"
        assert BedcaAttribute.MOEX == "moex"

    def test_bedca_attribute_reference_attributes(self):
        """Test reference and method attributes."""
        assert BedcaAttribute.REFERENCE_ID == "ref_id"
        assert BedcaAttribute.CITATION == "citation"
        assert BedcaAttribute.METHOD_ID == "method_id"
        assert BedcaAttribute.METHOD_NAME_ES == "m_nom_esp"
        assert BedcaAttribute.METHOD_NAME_EN == "m_nom_ing"

    def test_bedca_attribute_enum_behavior(self):
        """Test that BedcaAttribute behaves as a proper enum."""
        # Test that we can create from string value
        food_id = BedcaAttribute("f_id")
        assert food_id == BedcaAttribute.ID
        
        # Test that invalid values raise ValueError
        with pytest.raises(ValueError):
            BedcaAttribute("invalid_attribute")

    def test_bedca_attribute_iteration(self):
        """Test that we can iterate over BedcaAttribute values."""
        attributes = list(BedcaAttribute)
        
        # Should have many attributes
        assert len(attributes) > 50  # We have many attributes
        assert BedcaAttribute.ID in attributes
        assert BedcaAttribute.SPANISH_NAME in attributes
        assert BedcaAttribute.BEST_LOCATION in attributes

    def test_bedca_attribute_completeness(self):
        """Test that all expected attributes are present."""
        # Test some key attributes that should definitely be present
        required_attributes = [
            BedcaAttribute.ID,
            BedcaAttribute.SPANISH_NAME,
            BedcaAttribute.ENGLISH_NAME,
            BedcaAttribute.COMPONENT_ID,
            BedcaAttribute.BEST_LOCATION,
            BedcaAttribute.VALUE_UNIT,
            BedcaAttribute.VALUE_TYPE,
            BedcaAttribute.COMPONENT_GROUP_ID,
        ]
        
        for attr in required_attributes:
            assert isinstance(attr, BedcaAttribute)
            assert isinstance(attr.value, str)
            assert len(attr.value) > 0


class TestBedcaRelation:
    """Tests for the BedcaRelation enum."""

    def test_bedca_relation_values(self):
        """Test BedcaRelation enum values."""
        assert BedcaRelation.EQUAL == "EQUAL"
        assert BedcaRelation.LIKE == "LIKE"
        assert BedcaRelation.BEGINS_WITH == "BEGINW"

    def test_bedca_relation_enum_behavior(self):
        """Test that BedcaRelation behaves as a proper enum."""
        # Test that we can create from string value
        equal_rel = BedcaRelation("EQUAL")
        assert equal_rel == BedcaRelation.EQUAL
        
        # Test that invalid values raise ValueError
        with pytest.raises(ValueError):
            BedcaRelation("INVALID")

    def test_bedca_relation_iteration(self):
        """Test that we can iterate over BedcaRelation values."""
        relations = list(BedcaRelation)
        
        assert len(relations) == 3
        assert BedcaRelation.EQUAL in relations
        assert BedcaRelation.LIKE in relations
        assert BedcaRelation.BEGINS_WITH in relations

    def test_bedca_relation_string_representation(self):
        """Test string representation of BedcaRelation."""
        assert str(BedcaRelation.EQUAL) == "EQUAL"
        assert str(BedcaRelation.LIKE) == "LIKE"
        assert str(BedcaRelation.BEGINS_WITH) == "BEGINW"


class TestLanguages:
    """Tests for the Languages enum."""

    def test_languages_values(self):
        """Test Languages enum values."""
        assert Languages.ES == "ES"
        assert Languages.EN == "EN"

    def test_languages_enum_behavior(self):
        """Test that Languages behaves as a proper enum."""
        # Test that we can create from string value
        spanish = Languages("ES")
        assert spanish == Languages.ES
        
        # Test that invalid values raise ValueError
        with pytest.raises(ValueError):
            Languages("FR")

    def test_languages_iteration(self):
        """Test that we can iterate over Languages values."""
        languages = list(Languages)
        
        assert len(languages) == 2
        assert Languages.ES in languages
        assert Languages.EN in languages

    def test_languages_string_representation(self):
        """Test string representation of Languages."""
        assert str(Languages.ES) == "ES"
        assert str(Languages.EN) == "EN"


class TestEnumIntegration:
    """Integration tests for enum usage."""

    def test_component_attribute_mapping_consistency(self):
        """Test that component and attribute enums work together."""
        # Test that we can use components and attributes together
        component = BedcaComponent.PROTEIN
        attribute = BedcaAttribute.COMPONENT_NAME_EN
        
        # Both should be string enums
        assert isinstance(component, str)
        assert isinstance(attribute, str)
        
        # Should be able to compare with string values
        assert component == "protein, total"
        assert attribute == "c_eng_name"

    def test_relation_usage_with_attributes(self):
        """Test that relations work with attributes."""
        # Test typical usage pattern
        attribute = BedcaAttribute.SPANISH_NAME
        relation = BedcaRelation.LIKE
        
        # Should be usable in query building context
        assert attribute == "f_ori_name"
        assert relation == "LIKE"

    def test_language_usage_with_attributes(self):
        """Test that languages work with name attributes."""
        spanish_attr = BedcaAttribute.SPANISH_NAME
        english_attr = BedcaAttribute.ENGLISH_NAME
        
        spanish_lang = Languages.ES
        english_lang = Languages.EN
        
        # Test typical usage pattern for language selection
        if spanish_lang == Languages.ES:
            selected_attr = spanish_attr
        else:
            selected_attr = english_attr
            
        assert selected_attr == BedcaAttribute.SPANISH_NAME

    def test_enum_values_are_unique(self):
        """Test that enum values are unique within each enum."""
        # Test BedcaComponent uniqueness
        component_values = [comp.value for comp in BedcaComponent]
        assert len(component_values) == len(set(component_values))
        
        # Test BedcaAttribute uniqueness
        attribute_values = [attr.value for attr in BedcaAttribute]
        assert len(attribute_values) == len(set(attribute_values))
        
        # Test BedcaRelation uniqueness
        relation_values = [rel.value for rel in BedcaRelation]
        assert len(relation_values) == len(set(relation_values))
        
        # Test Languages uniqueness
        language_values = [lang.value for lang in Languages]
        assert len(language_values) == len(set(language_values))


@pytest.mark.unit
class TestEnumEdgeCases:
    """Tests for enum edge cases and error conditions."""

    def test_component_case_sensitivity(self):
        """Test that component matching is case sensitive."""
        # Should work with exact case
        protein = BedcaComponent("protein, total")
        assert protein == BedcaComponent.PROTEIN
        
        # Should fail with different case
        with pytest.raises(ValueError):
            BedcaComponent("Protein, Total")

    def test_attribute_case_sensitivity(self):
        """Test that attribute matching is case sensitive."""
        # Should work with exact case
        food_id = BedcaAttribute("f_id")
        assert food_id == BedcaAttribute.ID
        
        # Should fail with different case
        with pytest.raises(ValueError):
            BedcaAttribute("F_ID")

    def test_empty_string_enum_creation(self):
        """Test that empty strings raise appropriate errors."""
        with pytest.raises(ValueError):
            BedcaComponent("")
        
        with pytest.raises(ValueError):
            BedcaAttribute("")
        
        with pytest.raises(ValueError):
            BedcaRelation("")
        
        with pytest.raises(ValueError):
            Languages("")

    def test_none_enum_creation(self):
        """Test that None values raise appropriate errors."""
        with pytest.raises((ValueError, TypeError)):
            BedcaComponent(None)
        
        with pytest.raises((ValueError, TypeError)):
            BedcaAttribute(None)
        
        with pytest.raises((ValueError, TypeError)):
            BedcaRelation(None)
        
        with pytest.raises((ValueError, TypeError)):
            Languages(None)

    def test_enum_membership_testing(self):
        """Test membership testing with enums."""
        # Test that string values are found in enums
        assert "protein, total" in [comp.value for comp in BedcaComponent]
        assert "f_id" in [attr.value for attr in BedcaAttribute]
        assert "EQUAL" in [rel.value for rel in BedcaRelation]
        assert "ES" in [lang.value for lang in Languages]
        
        # Test that invalid values are not found
        assert "invalid component" not in [comp.value for comp in BedcaComponent]
        assert "invalid_attr" not in [attr.value for attr in BedcaAttribute]