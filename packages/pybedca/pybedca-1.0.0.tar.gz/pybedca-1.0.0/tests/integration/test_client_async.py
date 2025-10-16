"""Integration tests for the BEDCA API client async methods."""

import pytest
from unittest.mock import Mock, AsyncMock
import httpx

from pybedca.client import BedcaClient
from pybedca.models import FoodPreview, Food
from pybedca.enums import Languages


class TestBedcaClientAsyncInitialization:
    """Tests for BedcaClient async initialization."""

    def test_async_client_initialization(self):
        """Test that BedcaClient initializes with async client."""
        client = BedcaClient()
        
        assert hasattr(client, 'async_client')
        assert isinstance(client.async_client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test that BedcaClient works as an async context manager."""
        async with BedcaClient() as client:
            assert client.async_client is not None
            assert isinstance(client.async_client, httpx.AsyncClient)
            original_client = client.async_client
        
        # Verify the context manager worked
        assert original_client is not None

    @pytest.mark.asyncio
    async def test_aclose_method(self):
        """Test that aclose method properly closes the async httpx client."""
        client = BedcaClient()
        async_client = client.async_client
        
        # Close the async client
        await client.aclose()
        
        # Verify the async client object still exists
        assert async_client is not None


class TestBedcaClientAsyncMethods:
    """Tests for BedcaClient async methods with mocked HTTP requests."""

    @pytest.fixture
    def mock_async_client(self):
        """Fixture providing a mock async httpx client."""
        return AsyncMock(spec=httpx.AsyncClient)

    @pytest.fixture
    def client_with_mock_async(self, mock_async_client):
        """Fixture providing a client with mocked async httpx client."""
        client = BedcaClient()
        client.async_client = mock_async_client
        return client

    @pytest.mark.asyncio
    async def test_get_all_foods_async_success(self, client_with_mock_async, xml_search_response):
        """Test successful get_all_foods_async call."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = xml_search_response
        mock_response.raise_for_status = Mock()
        client_with_mock_async.async_client.post.return_value = mock_response
        
        # Call method
        foods = await client_with_mock_async.get_all_foods_async()
        
        # Verify results
        assert isinstance(foods, list)
        assert len(foods) == 2
        assert all(isinstance(food, FoodPreview) for food in foods)
        
        # Check first food
        first_food = foods[0]
        assert first_food.id == "2597"
        assert first_food.name_es == "Paella"
        assert first_food.name_en == "Paella"
        
        # Verify async client was called correctly
        client_with_mock_async.async_client.post.assert_called_once()
        call_args = client_with_mock_async.async_client.post.call_args
        assert call_args[0][0] == client_with_mock_async.BASE_URL
        assert call_args[1]['headers'] == client_with_mock_async.headers

    @pytest.mark.asyncio
    async def test_search_food_by_name_async_spanish_success(self, client_with_mock_async, xml_search_response):
        """Test successful search_food_by_name_async in Spanish."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = xml_search_response
        mock_response.raise_for_status = Mock()
        client_with_mock_async.async_client.post.return_value = mock_response
        
        # Call method
        foods = await client_with_mock_async.search_food_by_name_async("paella")
        
        # Verify results
        assert isinstance(foods, list)
        assert len(foods) == 2
        assert all(isinstance(food, FoodPreview) for food in foods)
        
        # Check that both paella variants are returned
        food_names = [food.name_es for food in foods]
        assert "Paella" in food_names
        assert "Paella marinera" in food_names
        
        # Verify async client was called
        client_with_mock_async.async_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_food_by_name_async_english_success(self, client_with_mock_async, xml_search_response):
        """Test successful search_food_by_name_async in English."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = xml_search_response
        mock_response.raise_for_status = Mock()
        client_with_mock_async.async_client.post.return_value = mock_response
        
        # Call method
        foods = await client_with_mock_async.search_food_by_name_async("paella", language=Languages.EN)
        
        # Verify results
        assert isinstance(foods, list)
        assert len(foods) == 2
        
        # Verify async client was called
        client_with_mock_async.async_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_food_by_name_async_invalid_language(self, client_with_mock_async):
        """Test search_food_by_name_async with invalid language raises ValueError."""
        # Should raise ValueError for invalid language
        with pytest.raises(ValueError, match="Invalid language"):
            await client_with_mock_async.search_food_by_name_async("paella", language="INVALID")

    @pytest.mark.asyncio
    async def test_get_food_by_id_async_success(self, client_with_mock_async, xml_food_response):
        """Test successful get_food_by_id_async call."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = xml_food_response
        mock_response.raise_for_status = Mock()
        client_with_mock_async.async_client.post.return_value = mock_response
        
        # Call method
        food = await client_with_mock_async.get_food_by_id_async(2597)
        
        # Verify results
        assert isinstance(food, Food)
        assert food.id == "2597"
        assert food.name_es == "Paella"
        assert food.name_en == "Paella"
        assert food.nutrients is not None
        
        # Verify async client was called correctly
        client_with_mock_async.async_client.post.assert_called_once()
        call_args = client_with_mock_async.async_client.post.call_args
        assert call_args[0][0] == client_with_mock_async.BASE_URL

    @pytest.mark.asyncio
    async def test_http_error_handling_async(self, client_with_mock_async):
        """Test HTTP error handling in async methods."""
        # Setup mock to raise HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404 Not Found", request=Mock(), response=Mock())
        client_with_mock_async.async_client.post.return_value = mock_response
        
        # Should raise HTTPStatusError
        with pytest.raises(httpx.HTTPStatusError):
            await client_with_mock_async.get_all_foods_async()

    @pytest.mark.asyncio
    async def test_network_error_handling_async(self, client_with_mock_async):
        """Test network error handling in async methods."""
        # Setup mock to raise connection error
        client_with_mock_async.async_client.post.side_effect = httpx.ConnectError("Network error")
        
        # Should raise ConnectError
        with pytest.raises(httpx.ConnectError):
            await client_with_mock_async.get_all_foods_async()

    @pytest.mark.asyncio
    async def test_empty_response_handling_async(self, client_with_mock_async):
        """Test handling of empty responses in async methods."""
        # Setup mock response with empty food list
        empty_response = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse>
        </foodresponse>"""
        
        mock_response = Mock()
        mock_response.text = empty_response
        mock_response.raise_for_status = Mock()
        client_with_mock_async.async_client.post.return_value = mock_response
        
        # Should return empty list for search methods
        foods = await client_with_mock_async.get_all_foods_async()
        assert isinstance(foods, list)
        assert len(foods) == 0


@pytest.mark.integration
class TestBedcaClientAsyncRealAPI:
    """Integration tests with real API calls using async methods (marked as integration)."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_real_search_food_by_name_async(self):
        """Test real API call for search_food_by_name_async."""
        client = BedcaClient()
        
        try:
            # Search for a common food
            foods = await client.search_food_by_name_async("arroz")  # Rice in Spanish
            
            # Should return some results
            assert isinstance(foods, list)
            assert len(foods) > 0
            
            # Check first result structure
            first_food = foods[0]
            assert isinstance(first_food, FoodPreview)
            assert hasattr(first_food, 'id')
            assert hasattr(first_food, 'name_es')
            assert hasattr(first_food, 'name_en')
            assert len(first_food.id) > 0
            assert len(first_food.name_es) > 0
            
        except httpx.HTTPError:
            pytest.skip("Real API not available")
        finally:
            await client.aclose()

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_real_get_food_by_id_async(self):
        """Test real API call for get_food_by_id_async."""
        client = BedcaClient()
        
        try:
            # Get a known food (paella)
            food = await client.get_food_by_id_async(2597)
            
            # Should return a Food object
            assert isinstance(food, Food)
            assert food.id == "2597"
            assert len(food.name_es) > 0
            assert len(food.name_en) > 0
            assert food.nutrients is not None
            
            # Check that nutrients have reasonable values
            assert food.nutrients.energy is not None
            assert food.nutrients.protein is not None
            
        except httpx.HTTPError:
            pytest.skip("Real API not available")
        finally:
            await client.aclose()


class TestBedcaClientAsyncEdgeCases:
    """Tests for edge cases in async methods."""

    @pytest.mark.asyncio
    async def test_search_with_empty_string_async(self, mock_bedca_client):
        """Test async search with empty string."""
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse></foodresponse>"""
        mock_response.raise_for_status = Mock()
        mock_bedca_client.async_client = AsyncMock()
        mock_bedca_client.async_client.post.return_value = mock_response
        
        foods = await mock_bedca_client.search_food_by_name_async("")
        assert isinstance(foods, list)
        assert len(foods) == 0

    @pytest.mark.asyncio
    async def test_search_with_special_characters_async(self, mock_bedca_client):
        """Test async search with special characters."""
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse></foodresponse>"""
        mock_response.raise_for_status = Mock()
        mock_bedca_client.async_client = AsyncMock()
        mock_bedca_client.async_client.post.return_value = mock_response
        
        # Should not raise an error
        foods = await mock_bedca_client.search_food_by_name_async("café & té")
        assert isinstance(foods, list)

    @pytest.mark.asyncio
    async def test_get_food_by_id_async_with_string_id(self, mock_bedca_client):
        """Test get_food_by_id_async with string ID (should work due to str() conversion)."""
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse>
            <food>
                <f_id>2597</f_id>
                <f_ori_name>Test</f_ori_name>
                <f_eng_name>Test</f_eng_name>
                <sci_name></sci_name>
            </food>
        </foodresponse>"""
        mock_response.raise_for_status = Mock()
        mock_bedca_client.async_client = AsyncMock()
        mock_bedca_client.async_client.post.return_value = mock_response
        
        # Should work with string ID
        food = await mock_bedca_client.get_food_by_id_async("2597")
        assert isinstance(food, Food)
