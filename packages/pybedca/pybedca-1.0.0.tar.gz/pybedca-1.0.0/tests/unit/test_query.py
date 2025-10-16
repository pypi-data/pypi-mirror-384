"""Unit tests for the query builder module."""

import pytest
import xml.etree.ElementTree as ET

from pybedca.query import BedcaQueryBuilder
from pybedca.enums import BedcaAttribute, BedcaRelation


class TestBedcaQueryBuilder:
    """Tests for the BedcaQueryBuilder class."""

    def test_query_builder_initialization_level_1(self):
        """Test initializing query builder with level 1."""
        builder = BedcaQueryBuilder(level=1)
        
        # Build and parse the XML to check structure
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        # Check root element
        assert root.tag == "foodquery"
        
        # Check type level
        type_elem = root.find("type")
        assert type_elem is not None
        assert type_elem.get("level") == "1"
        
        # Check selection element exists
        selection_elem = root.find("selection")
        assert selection_elem is not None

    def test_query_builder_initialization_level_2(self):
        """Test initializing query builder with level 2."""
        builder = BedcaQueryBuilder(level=2)
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        # Check type level
        type_elem = root.find("type")
        assert type_elem.get("level") == "2"
        
        # Level 2 should automatically add public condition
        conditions = root.findall("condition")
        assert len(conditions) >= 1
        
        # Find the public condition
        public_condition = None
        for condition in conditions:
            cond1 = condition.find("cond1")
            if cond1 is not None:
                attr1 = cond1.find("atribute1")
                if attr1 is not None and attr1.get("name") == "publico":
                    public_condition = condition
                    break
        
        assert public_condition is not None
        
        # Check the public condition structure
        relation = public_condition.find("relation")
        assert relation.get("type") == "EQUAL"
        
        cond3 = public_condition.find("cond3")
        assert cond3.text == "1"

    def test_select_single_attribute(self):
        """Test selecting a single attribute."""
        builder = BedcaQueryBuilder(level=1)
        builder.select(BedcaAttribute.ID)
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        selection = root.find("selection")
        attributes = selection.findall("atribute")
        
        assert len(attributes) == 1
        assert attributes[0].get("name") == "f_id"

    def test_select_multiple_attributes(self):
        """Test selecting multiple attributes."""
        builder = BedcaQueryBuilder(level=1)
        builder.select(
            BedcaAttribute.ID,
            BedcaAttribute.SPANISH_NAME,
            BedcaAttribute.ENGLISH_NAME
        )
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        selection = root.find("selection")
        attributes = selection.findall("atribute")
        
        assert len(attributes) == 3
        attribute_names = [attr.get("name") for attr in attributes]
        assert "f_id" in attribute_names
        assert "f_ori_name" in attribute_names
        assert "f_eng_name" in attribute_names

    def test_where_condition_equal(self):
        """Test adding an EQUAL where condition."""
        builder = BedcaQueryBuilder(level=1)
        builder.where(BedcaAttribute.ID, BedcaRelation.EQUAL, "2597")
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        conditions = root.findall("condition")
        assert len(conditions) >= 1
        
        # Find our condition (not the auto-added public one for level 2)
        condition = conditions[0]  # For level 1, this should be our condition
        
        # Check attribute
        cond1 = condition.find("cond1")
        attr1 = cond1.find("atribute1")
        assert attr1.get("name") == "f_id"
        
        # Check relation
        relation = condition.find("relation")
        assert relation.get("type") == "EQUAL"
        
        # Check value
        cond3 = condition.find("cond3")
        assert cond3.text == "2597"

    def test_where_condition_like(self):
        """Test adding a LIKE where condition."""
        builder = BedcaQueryBuilder(level=1)
        builder.where(BedcaAttribute.SPANISH_NAME, BedcaRelation.LIKE, "paella")
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        condition = root.find("condition")
        
        # Check attribute
        cond1 = condition.find("cond1")
        attr1 = cond1.find("atribute1")
        assert attr1.get("name") == "f_ori_name"
        
        # Check relation
        relation = condition.find("relation")
        assert relation.get("type") == "LIKE"
        
        # Check value
        cond3 = condition.find("cond3")
        assert cond3.text == "paella"

    def test_multiple_where_conditions(self):
        """Test adding multiple where conditions."""
        builder = BedcaQueryBuilder(level=1)
        builder.where(BedcaAttribute.SPANISH_NAME, BedcaRelation.LIKE, "paella")
        builder.where(BedcaAttribute.ORIGIN, BedcaRelation.EQUAL, "BEDCA")
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        conditions = root.findall("condition")
        assert len(conditions) == 2
        
        # Check that both conditions are present
        condition_attrs = []
        for condition in conditions:
            cond1 = condition.find("cond1")
            attr1 = cond1.find("atribute1")
            condition_attrs.append(attr1.get("name"))
        
        assert "f_ori_name" in condition_attrs
        assert "f_origen" in condition_attrs

    def test_order_ascending(self):
        """Test adding ascending order."""
        builder = BedcaQueryBuilder(level=1)
        builder.order(BedcaAttribute.SPANISH_NAME, ascending=True)
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        order = root.find("order")
        assert order is not None
        assert order.get("ordtype") == "ASC"
        
        attr3 = order.find("atribute3")
        assert attr3.get("name") == "f_ori_name"

    def test_order_descending(self):
        """Test adding descending order."""
        builder = BedcaQueryBuilder(level=1)
        builder.order(BedcaAttribute.SPANISH_NAME, ascending=False)
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        order = root.find("order")
        assert order.get("ordtype") == "DESC"

    def test_order_default_ascending(self):
        """Test that order defaults to ascending."""
        builder = BedcaQueryBuilder(level=1)
        builder.order(BedcaAttribute.SPANISH_NAME)  # No ascending parameter
        
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        order = root.find("order")
        assert order.get("ordtype") == "ASC"

    def test_method_chaining(self):
        """Test that methods can be chained."""
        builder = BedcaQueryBuilder(level=1)
        result = (builder
                 .select(BedcaAttribute.ID, BedcaAttribute.SPANISH_NAME)
                 .where(BedcaAttribute.ORIGIN, BedcaRelation.EQUAL, "BEDCA")
                 .order(BedcaAttribute.SPANISH_NAME))
        
        # Should return the same builder instance
        assert result is builder
        
        # Check that all operations were applied
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        
        # Check selection
        selection = root.find("selection")
        attributes = selection.findall("atribute")
        assert len(attributes) == 2
        
        # Check condition
        condition = root.find("condition")
        assert condition is not None
        
        # Check order
        order = root.find("order")
        assert order is not None

    def test_build_returns_valid_xml(self):
        """Test that build() returns valid XML."""
        builder = BedcaQueryBuilder(level=1)
        builder.select(BedcaAttribute.ID).where(BedcaAttribute.ORIGIN, BedcaRelation.EQUAL, "BEDCA")
        
        xml_str = builder.build()
        
        # Should be valid XML
        root = ET.fromstring(xml_str)
        assert root.tag == "foodquery"
        
        # Should contain XML declaration
        assert xml_str.startswith('<?xml version="1.0" encoding="utf-8"?>')

    def test_build_xml_formatting(self):
        """Test that build() returns properly formatted XML."""
        builder = BedcaQueryBuilder(level=1)
        builder.select(BedcaAttribute.ID)
        
        xml_str = builder.build()
        
        # Should have proper indentation (multiple lines)
        lines = xml_str.strip().split('\n')
        assert len(lines) > 1
        
        # Should have indented elements
        assert any(line.startswith('  ') for line in lines)


class TestQueryBuilderComplexScenarios:
    """Tests for complex query building scenarios."""

    def test_search_food_by_name_query(self):
        """Test building a search food by name query."""
        builder = BedcaQueryBuilder(level=1)
        query = (builder
                .select(
                    BedcaAttribute.ID,
                    BedcaAttribute.SPANISH_NAME,
                    BedcaAttribute.ENGLISH_NAME,
                    BedcaAttribute.ORIGIN,
                )
                .where(BedcaAttribute.SPANISH_NAME, BedcaRelation.LIKE, "paella")
                .where(BedcaAttribute.ORIGIN, BedcaRelation.EQUAL, "BEDCA")
                .order(BedcaAttribute.SPANISH_NAME)
                .build())
        
        # Parse and validate structure
        root = ET.fromstring(query)
        
        # Check type level
        type_elem = root.find("type")
        assert type_elem.get("level") == "1"
        
        # Check selection has 4 attributes
        selection = root.find("selection")
        attributes = selection.findall("atribute")
        assert len(attributes) == 4
        
        # Check conditions
        conditions = root.findall("condition")
        assert len(conditions) == 2
        
        # Check order
        order = root.find("order")
        assert order is not None

    def test_get_food_by_id_query(self):
        """Test building a get food by ID query."""
        builder = BedcaQueryBuilder(level=2)
        
        # Select all attributes (like in the real implementation)
        all_attributes = list(BedcaAttribute)
        query = (builder
                .select(*all_attributes)
                .where(BedcaAttribute.ID, BedcaRelation.EQUAL, "2597")
                .order(BedcaAttribute.COMPONENT_GROUP_ID)
                .build())
        
        root = ET.fromstring(query)
        
        # Check type level
        type_elem = root.find("type")
        assert type_elem.get("level") == "2"
        
        # Check selection has many attributes
        selection = root.find("selection")
        attributes = selection.findall("atribute")
        assert len(attributes) == len(all_attributes)
        
        # Check conditions (should have public + our ID condition)
        conditions = root.findall("condition")
        assert len(conditions) == 2
        
        # Find ID condition
        id_condition = None
        for condition in conditions:
            cond3 = condition.find("cond3")
            if cond3 is not None and cond3.text == "2597":
                id_condition = condition
                break
        
        assert id_condition is not None

    def test_get_all_foods_query(self):
        """Test building a get all foods query."""
        builder = BedcaQueryBuilder(level=1)
        query = (builder
                .select(
                    BedcaAttribute.ID,
                    BedcaAttribute.SPANISH_NAME,
                    BedcaAttribute.ENGLISH_NAME,
                    BedcaAttribute.ORIGIN,
                )
                .where(BedcaAttribute.ORIGIN, BedcaRelation.EQUAL, "BEDCA")
                .order(BedcaAttribute.SPANISH_NAME)
                .build())
        
        root = ET.fromstring(query)
        
        # Should have single condition for origin
        conditions = root.findall("condition")
        assert len(conditions) == 1
        
        condition = conditions[0]
        cond3 = condition.find("cond3")
        assert cond3.text == "BEDCA"


@pytest.mark.unit
class TestQueryBuilderIntegration:
    """Integration tests for query builder with real XML comparison."""

    def test_search_query_matches_expected_structure(self, xml_search_query):
        """Test that generated search query matches expected structure."""
        builder = BedcaQueryBuilder(level=1)
        generated_query = (builder
                          .select(
                              BedcaAttribute.ID,
                              BedcaAttribute.SPANISH_NAME,
                              BedcaAttribute.LANGUAL,
                              BedcaAttribute.ENGLISH_NAME,
                              BedcaAttribute.ORIGIN,
                          )
                          .where(BedcaAttribute.SPANISH_NAME, BedcaRelation.LIKE, "paella")
                          .where(BedcaAttribute.ORIGIN, BedcaRelation.EQUAL, "BEDCA")
                          .order(BedcaAttribute.SPANISH_NAME)
                          .build())
        
        # Parse both XMLs
        generated_root = ET.fromstring(generated_query)
        expected_root = ET.fromstring(xml_search_query)
        
        # Compare structure (not exact text due to formatting differences)
        assert generated_root.tag == expected_root.tag
        
        # Compare type level
        gen_type = generated_root.find("type")
        exp_type = expected_root.find("type")
        assert gen_type.get("level") == exp_type.get("level")
        
        # Compare selection count
        gen_selection = generated_root.find("selection")
        exp_selection = expected_root.find("selection")
        gen_attrs = gen_selection.findall("atribute")
        exp_attrs = exp_selection.findall("atribute")
        assert len(gen_attrs) == len(exp_attrs)
        
        # Compare condition count
        gen_conditions = generated_root.findall("condition")
        exp_conditions = expected_root.findall("condition")
        assert len(gen_conditions) == len(exp_conditions)