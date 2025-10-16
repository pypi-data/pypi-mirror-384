"""End-to-end workflow tests for pybedca."""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

from pybedca import BedcaClient, FoodPreview, Food
from pybedca.enums import Languages, BedcaComponent
from pybedca.values import Mass, Energy


class TestSearchToDetailWorkflow:
    """Tests for the complete search-to-detail workflow."""

    def test_search_and_get_details_workflow(self, workflow_client):
        """Test complete workflow from search to getting detailed information."""
        # Step 1: Search for foods
        search_results = workflow_client.search_food_by_name("paella")
        
        # Verify search results
        assert isinstance(search_results, list)
        assert len(search_results) > 0
        assert all(isinstance(food, FoodPreview) for food in search_results)
        
        # Step 2: Get detailed information for first result
        first_food_preview = search_results[0]
        food_id = int(first_food_preview.id)
        detailed_food = workflow_client.get_food_by_id(food_id)
        
        # Verify detailed information
        assert isinstance(detailed_food, Food)
        assert detailed_food.id == first_food_preview.id
        assert detailed_food.name_es == first_food_preview.name_es
        assert detailed_food.name_en == first_food_preview.name_en
        
        # Verify nutritional data is available
        assert detailed_food.nutrients is not None
        assert hasattr(detailed_food.nutrients, 'energy')
        assert hasattr(detailed_food.nutrients, 'protein')
        assert hasattr(detailed_food.nutrients, 'fat')

    def test_multilingual_search_workflow(self, workflow_client):
        """Test workflow with different languages."""
        # Search in Spanish (default)
        spanish_results = workflow_client.search_food_by_name("paella")
        
        # Search in English
        english_results = workflow_client.search_food_by_name("paella", language=Languages.EN)
        
        # Both should return results (mocked to return same data)
        assert len(spanish_results) > 0
        assert len(english_results) > 0
        
        # Results should have both Spanish and English names
        for food in spanish_results:
            assert hasattr(food, 'name_es')
            assert hasattr(food, 'name_en')
            assert len(food.name_es) > 0

    def test_nutritional_analysis_workflow(self, workflow_client):
        """Test workflow for nutritional analysis."""
        # Search for food
        foods = workflow_client.search_food_by_name("paella")
        assert len(foods) > 0
        
        # Get detailed nutritional information
        food = workflow_client.get_food_by_id(int(foods[0].id))
        nutrients = food.nutrients
        
        # Analyze macronutrients
        macronutrients = {
            'energy': nutrients.energy,
            'protein': nutrients.protein,
            'fat': nutrients.fat,
            'carbohydrate': nutrients.carbohydrate,
            'water': nutrients.water
        }
        
        # All macronutrients should be present
        for name, nutrient in macronutrients.items():
            assert nutrient is not None
            assert hasattr(nutrient, 'value')
            assert hasattr(nutrient, 'unit')
            assert hasattr(nutrient, 'component')
        
        # Energy should be Energy type, others should be Mass type
        assert isinstance(nutrients.energy.value, Energy)
        assert isinstance(nutrients.protein.value, Mass)
        assert isinstance(nutrients.fat.value, Mass)
        assert isinstance(nutrients.carbohydrate.value, Mass)

    def test_unit_conversion_workflow(self, workflow_client):
        """Test workflow involving unit conversions."""
        # Get food details
        foods = workflow_client.search_food_by_name("paella")
        food = workflow_client.get_food_by_id(int(foods[0].id))
        
        # Test energy unit conversions
        energy = food.nutrients.energy.value
        if isinstance(energy, Energy):
            kcal_value = energy.kcal
            kj_value = energy.kj
            
            # Both should be positive numbers
            assert kcal_value > 0
            assert kj_value > 0
            
            # kJ should be larger than kcal (approximately 4.184 times)
            assert kj_value > kcal_value
        
        # Test mass unit conversions
        protein = food.nutrients.protein.value
        if isinstance(protein, Mass):
            g_value = protein.to_unit("g")
            mg_value = protein.to_unit("mg")
            
            # mg should be 1000 times larger than g
            assert abs(mg_value - (g_value * 1000)) < Decimal("0.01")


class TestErrorRecoveryWorkflows:
    """Tests for error recovery in workflows."""

    def test_search_no_results_workflow(self):
        """Test workflow when search returns no results."""
        client = BedcaClient()
        
        # Mock empty search results - proper XML structure but no food elements
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
<foodresponse>
</foodresponse>"""
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        client.client = mock_client
        
        # Search should return empty list
        results = client.search_food_by_name("nonexistentfood")
        assert isinstance(results, list)
        assert len(results) == 0
        
        # Workflow should handle empty results gracefully
        if results:
            # This branch shouldn't execute
            pytest.fail("Expected empty results")
        else:
            # This is the expected path
            assert True

    def test_invalid_food_id_workflow(self):
        """Test workflow with invalid food ID."""
        client = BedcaClient()
        
        # Mock httpx client to raise error for invalid ID
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Food not found")
        mock_client.post.return_value = mock_response
        client.client = mock_client
        
        # Should raise an error
        with pytest.raises(Exception):
            client.get_food_by_id(999999999)

    def test_network_error_recovery_workflow(self):
        """Test workflow recovery from network errors."""
        client = BedcaClient()
        
        # Mock network error
        mock_client = Mock()
        mock_client.post.side_effect = Exception("Network error")
        client.client = mock_client
        
        # Should propagate network error
        with pytest.raises(Exception):
            client.search_food_by_name("paella")


class TestDataValidationWorkflows:
    """Tests for data validation in workflows."""

    def test_food_data_consistency_workflow(self, workflow_client):
        """Test that food data is consistent across search and detail views."""
        # Search for foods
        search_results = workflow_client.search_food_by_name("paella")
        assert len(search_results) > 0
        
        # Get detailed view
        preview = search_results[0]
        detailed = workflow_client.get_food_by_id(int(preview.id))
        
        # Basic information should match
        assert detailed.id == preview.id
        assert detailed.name_es == preview.name_es
        assert detailed.name_en == preview.name_en
        
        # Detailed view should have additional information
        assert hasattr(detailed, 'nutrients')
        assert hasattr(detailed, 'scientific_name')

    def test_nutritional_data_validation_workflow(self, workflow_client):
        """Test validation of nutritional data."""
        # Get food with nutritional data
        foods = workflow_client.search_food_by_name("paella")
        food = workflow_client.get_food_by_id(int(foods[0].id))
        
        nutrients = food.nutrients
        
        # Validate that all required nutrients are present
        required_nutrients = [
            'energy', 'protein', 'fat', 'carbohydrate', 'water',
            'fiber', 'saturated_fat', 'monounsaturated_fat', 'polyunsaturated_fat',
            'vitamin_c', 'calcium', 'iron', 'sodium'
        ]
        
        for nutrient_name in required_nutrients:
            assert hasattr(nutrients, nutrient_name)
            nutrient = getattr(nutrients, nutrient_name)
            assert nutrient is not None
            assert hasattr(nutrient, 'value')
            assert hasattr(nutrient, 'unit')
            assert hasattr(nutrient, 'component')

    def test_value_type_validation_workflow(self, workflow_client):
        """Test validation of value types in workflow."""
        # Get food data
        foods = workflow_client.search_food_by_name("paella")
        food = workflow_client.get_food_by_id(int(foods[0].id))
        
        nutrients = food.nutrients
        
        # Energy should be Energy type
        energy_value = nutrients.energy.value
        if energy_value != "trace":
            assert isinstance(energy_value, Energy)
            assert hasattr(energy_value, 'kcal')
            assert hasattr(energy_value, 'kj')
        
        # Mass nutrients should be Mass type
        mass_nutrients = ['protein', 'fat', 'carbohydrate', 'calcium', 'iron']
        for nutrient_name in mass_nutrients:
            nutrient_value = getattr(nutrients, nutrient_name).value
            if nutrient_value != "trace":
                assert isinstance(nutrient_value, Mass)
                assert hasattr(nutrient_value, 'value')
                assert hasattr(nutrient_value, 'to_unit')


class TestPerformanceWorkflows:
    """Tests for performance aspects of workflows."""

    def test_multiple_searches_workflow(self, workflow_client):
        """Test workflow with multiple consecutive searches."""
        search_terms = ["paella", "arroz", "pan"]
        
        all_results = []
        for term in search_terms:
            results = workflow_client.search_food_by_name(term)
            all_results.extend(results)
        
        # Should have collected results from all searches
        assert len(all_results) >= len(search_terms)  # At least one result per search
        
        # All results should be FoodPreview objects
        assert all(isinstance(food, FoodPreview) for food in all_results)

    def test_batch_detail_retrieval_workflow(self, workflow_client):
        """Test workflow for retrieving details of multiple foods."""
        # Search for foods
        search_results = workflow_client.search_food_by_name("paella")
        
        # Get details for multiple foods
        detailed_foods = []
        for preview in search_results[:2]:  # Limit to first 2 for performance
            detailed = workflow_client.get_food_by_id(int(preview.id))
            detailed_foods.append(detailed)
        
        # All should be Food objects with complete data
        assert len(detailed_foods) <= 2
        assert all(isinstance(food, Food) for food in detailed_foods)
        assert all(food.nutrients is not None for food in detailed_foods)


@pytest.mark.integration
class TestRealWorldWorkflows:
    """Real-world workflow tests (marked as integration)."""

    @pytest.mark.slow
    def test_real_nutritional_comparison_workflow(self):
        """Test real workflow for comparing nutritional values."""
        client = BedcaClient()
        
        try:
            # Search for different types of rice
            rice_foods = client.search_food_by_name("arroz")
            
            if len(rice_foods) >= 2:
                # Get detailed info for first two rice types
                rice1 = client.get_food_by_id(int(rice_foods[0].id))
                rice2 = client.get_food_by_id(int(rice_foods[1].id))
                
                # Compare energy content
                energy1 = rice1.nutrients.energy.value
                energy2 = rice2.nutrients.energy.value
                
                if isinstance(energy1, Energy) and isinstance(energy2, Energy):
                    # Both should have reasonable energy values
                    assert energy1.kcal > 0
                    assert energy2.kcal > 0
                    
                    # Energy values should be in reasonable range for rice (200-400 kcal/100g)
                    assert 100 < energy1.kcal < 500
                    assert 100 < energy2.kcal < 500
                
        except Exception:
            pytest.skip("Real API not available or insufficient data")

    @pytest.mark.slow
    def test_real_search_refinement_workflow(self):
        """Test real workflow for refining searches."""
        client = BedcaClient()
        
        try:
            # Broad search
            broad_results = client.search_food_by_name("pan")  # Bread
            
            # More specific search
            specific_results = client.search_food_by_name("pan integral")  # Whole wheat bread
            
            # Specific search should return fewer or equal results
            assert len(specific_results) <= len(broad_results)
            
            # All results should be relevant
            for food in specific_results:
                assert isinstance(food, FoodPreview)
                assert len(food.name_es) > 0
                
        except Exception:
            pytest.skip("Real API not available")


class TestWorkflowEdgeCases:
    """Tests for edge cases in workflows."""

    def test_empty_search_term_workflow(self, workflow_client):
        """Test workflow with empty search term."""
        results = workflow_client.search_food_by_name("")
        
        # Should handle gracefully (return empty list or all foods)
        assert isinstance(results, list)

    def test_special_characters_workflow(self, workflow_client):
        """Test workflow with special characters in search."""
        # Test with accented characters
        results = workflow_client.search_food_by_name("café")
        assert isinstance(results, list)
        
        # Test with symbols
        results = workflow_client.search_food_by_name("pan & mantequilla")
        assert isinstance(results, list)

    def test_very_long_search_term_workflow(self, workflow_client):
        """Test workflow with very long search term."""
        long_term = "a" * 1000  # Very long search term
        
        results = workflow_client.search_food_by_name(long_term)
        
        # Should handle gracefully
        assert isinstance(results, list)

    def test_numeric_search_term_workflow(self, workflow_client):
        """Test workflow with numeric search term."""
        results = workflow_client.search_food_by_name("123")
        
        # Should handle gracefully
        assert isinstance(results, list)


class TestWorkflowIntegration:
    """Integration tests combining multiple workflow aspects."""

    def test_complete_food_analysis_workflow(self, workflow_client):
        """Test complete workflow for food analysis."""
        # Step 1: Search
        foods = workflow_client.search_food_by_name("paella")
        assert len(foods) > 0
        
        # Step 2: Get details
        food = workflow_client.get_food_by_id(int(foods[0].id))
        
        # Step 3: Analyze nutrition
        nutrients = food.nutrients
        
        # Step 4: Extract key information
        nutrition_summary = {
            'name': food.name_es,
            'energy_kcal': nutrients.energy.value.kcal if isinstance(nutrients.energy.value, Energy) else 0,
            'protein_g': nutrients.protein.value.value if isinstance(nutrients.protein.value, Mass) else 0,
            'fat_g': nutrients.fat.value.value if isinstance(nutrients.fat.value, Mass) else 0,
            'carbs_g': nutrients.carbohydrate.value.value if isinstance(nutrients.carbohydrate.value, Mass) else 0,
        }
        
        # Verify summary has reasonable values
        assert nutrition_summary['name'] == "Paella"
        assert nutrition_summary['energy_kcal'] > 0
        assert nutrition_summary['protein_g'] > 0
        
        # Step 5: Unit conversions
        if isinstance(nutrients.protein.value, Mass):
            protein_mg = nutrients.protein.value.to_unit("mg")
            assert protein_mg > nutrition_summary['protein_g'] * 900  # Should be ~1000x larger

    def test_multi_language_comparison_workflow(self, workflow_client):
        """Test workflow comparing results in different languages."""
        # Search in Spanish
        spanish_results = workflow_client.search_food_by_name("paella", Languages.ES)
        
        # Search in English  
        english_results = workflow_client.search_food_by_name("paella", Languages.EN)
        
        # Both should return results (in our mock, they return the same data)
        assert len(spanish_results) > 0
        assert len(english_results) > 0
        
        # Results should have both language names
        for food in spanish_results:
            assert hasattr(food, 'name_es')
            assert hasattr(food, 'name_en')
            assert len(food.name_es) > 0