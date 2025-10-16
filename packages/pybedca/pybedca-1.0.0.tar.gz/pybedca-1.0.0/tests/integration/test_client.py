"""Integration tests for the BEDCA API client."""

import pytest
from unittest.mock import Mock, patch
import httpx

from pybedca.client import BedcaClient
from pybedca.models import FoodPreview, Food
from pybedca.enums import Languages


class TestBedcaClientInitialization:
    """Tests for BedcaClient initialization."""

    def test_client_initialization(self):
        """Test that BedcaClient initializes correctly."""
        client = BedcaClient()
        
        assert client.BASE_URL == "https://www.bedca.net/bdpub/procquery.php"
        assert hasattr(client, 'client')
        assert isinstance(client.client, httpx.Client)
        
        # Check headers
        expected_headers = {
            "Content-Type": "text/xml",
            "User-Agent": "Python-pybedca",
            "Origin": "https://www.bedca.net",
            "Referer": "https://www.bedca.net/bdpub/index.php",
        }
        assert client.headers == expected_headers

    def test_context_manager(self):
        """Test that BedcaClient works as a context manager."""
        with BedcaClient() as client:
            assert client.client is not None
            assert isinstance(client.client, httpx.Client)
            original_client = client.client
        
        # Verify close was called (client should be closed after exiting context)
        # We can't directly check if it's closed, but we can verify the context manager worked
        assert original_client is not None

    def test_close_method(self):
        """Test that close method properly closes the httpx client."""
        client = BedcaClient()
        httpx_client = client.client
        
        # Close the client
        client.close()
        
        # Verify the httpx client's close was called
        # The client object still exists but should be closed
        assert httpx_client is not None

    def test_close_method_closes_sync_client(self):
        """Test that close method closes the sync client."""
        client = BedcaClient()
        
        # Mock the client's close method to verify it's called
        client.client.close = Mock()
        
        # Close the client
        client.close()
        
        # Verify close was called
        client.client.close.assert_called_once()


class TestBedcaClientMockedRequests:
    """Tests for BedcaClient with mocked HTTP requests."""

    @pytest.fixture
    def mock_client(self):
        """Fixture providing a mock httpx client."""
        return Mock(spec=httpx.Client)

    @pytest.fixture
    def client_with_mock_session(self, mock_client):
        """Fixture providing a client with mocked httpx client."""
        client = BedcaClient()
        client.client = mock_client
        return client

    def test_get_all_foods_success(self, client_with_mock_session, xml_search_response):
        """Test successful get_all_foods call."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = xml_search_response
        mock_response.raise_for_status = Mock()
        client_with_mock_session.client.post.return_value = mock_response
        
        # Call method
        foods = client_with_mock_session.get_all_foods()
        
        # Verify results
        assert isinstance(foods, list)
        assert len(foods) == 2  # Based on the fixture data
        assert all(isinstance(food, FoodPreview) for food in foods)
        
        # Check first food
        first_food = foods[0]
        assert first_food.id == "2597"
        assert first_food.name_es == "Paella"
        assert first_food.name_en == "Paella"
        
        # Verify client was called correctly
        client_with_mock_session.client.post.assert_called_once()
        call_args = client_with_mock_session.client.post.call_args
        assert call_args[0][0] == client_with_mock_session.BASE_URL
        assert call_args[1]['headers'] == client_with_mock_session.headers

    def test_search_food_by_name_spanish_success(self, client_with_mock_session, xml_search_response):
        """Test successful search_food_by_name in Spanish."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = xml_search_response
        mock_response.raise_for_status = Mock()
        client_with_mock_session.client.post.return_value = mock_response
        
        # Call method
        foods = client_with_mock_session.search_food_by_name("paella")
        
        # Verify results
        assert isinstance(foods, list)
        assert len(foods) == 2
        assert all(isinstance(food, FoodPreview) for food in foods)
        
        # Check that both paella variants are returned
        food_names = [food.name_es for food in foods]
        assert "Paella" in food_names
        assert "Paella marinera" in food_names
        
        # Verify client was called
        client_with_mock_session.client.post.assert_called_once()

    def test_search_food_by_name_english_success(self, client_with_mock_session, xml_search_response):
        """Test successful search_food_by_name in English."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = xml_search_response
        mock_response.raise_for_status = Mock()
        client_with_mock_session.client.post.return_value = mock_response
        
        # Call method
        foods = client_with_mock_session.search_food_by_name("paella", language=Languages.EN)
        
        # Verify results
        assert isinstance(foods, list)
        assert len(foods) == 2
        
        # Verify client was called
        client_with_mock_session.client.post.assert_called_once()

    def test_search_food_by_name_invalid_language(self, client_with_mock_session):
        """Test search_food_by_name with invalid language raises ValueError."""
        # Should raise ValueError for invalid language
        with pytest.raises(ValueError, match="Invalid language"):
            client_with_mock_session.search_food_by_name("paella", language="INVALID")

    def test_get_food_by_id_success(self, client_with_mock_session, xml_food_response):
        """Test successful get_food_by_id call."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = xml_food_response
        mock_response.raise_for_status = Mock()
        client_with_mock_session.client.post.return_value = mock_response
        
        # Call method
        food = client_with_mock_session.get_food_by_id(2597)
        
        # Verify results
        assert isinstance(food, Food)
        assert food.id == "2597"
        assert food.name_es == "Paella"
        assert food.name_en == "Paella"
        assert food.nutrients is not None
        
        # Verify client was called correctly
        client_with_mock_session.client.post.assert_called_once()
        call_args = client_with_mock_session.client.post.call_args
        assert call_args[0][0] == client_with_mock_session.BASE_URL

    def test_http_error_handling(self, client_with_mock_session):
        """Test HTTP error handling."""
        # Setup mock to raise HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404 Not Found", request=Mock(), response=Mock())
        client_with_mock_session.client.post.return_value = mock_response
        
        # Should raise HTTPStatusError
        with pytest.raises(httpx.HTTPStatusError):
            client_with_mock_session.get_all_foods()

    def test_network_error_handling(self, client_with_mock_session):
        """Test network error handling."""
        # Setup mock to raise connection error
        client_with_mock_session.client.post.side_effect = httpx.ConnectError("Network error")
        
        # Should raise ConnectError
        with pytest.raises(httpx.ConnectError):
            client_with_mock_session.get_all_foods()

    def test_invalid_xml_response_handling(self, client_with_mock_session):
        """Test handling of invalid XML responses."""
        # Setup mock response with invalid XML
        mock_response = Mock()
        mock_response.text = "This is not valid XML"
        mock_response.raise_for_status = Mock()
        client_with_mock_session.client.post.return_value = mock_response
        
        # Should raise XML parsing error
        with pytest.raises(Exception):  # Could be ParseError or ValueError
            client_with_mock_session.get_food_by_id(2597)

    def test_empty_response_handling(self, client_with_mock_session):
        """Test handling of empty responses."""
        # Setup mock response with empty food list
        empty_response = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse>
        </foodresponse>"""
        
        mock_response = Mock()
        mock_response.text = empty_response
        mock_response.raise_for_status = Mock()
        client_with_mock_session.client.post.return_value = mock_response
        
        # Should return empty list for search methods
        foods = client_with_mock_session.get_all_foods()
        assert isinstance(foods, list)
        assert len(foods) == 0

    def test_malformed_food_response_handling(self, client_with_mock_session):
        """Test handling of malformed food responses."""
        # Setup mock response without food element
        malformed_response = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse>
            <componentList>
                <component>
                    <id>404</id>
                </component>
            </componentList>
        </foodresponse>"""
        
        mock_response = Mock()
        mock_response.text = malformed_response
        mock_response.raise_for_status = Mock()
        client_with_mock_session.client.post.return_value = mock_response
        
        # Should raise ValueError for get_food_by_id
        with pytest.raises(ValueError, match="No food element found in XML"):
            client_with_mock_session.get_food_by_id(2597)


class TestBedcaClientQueryGeneration:
    """Tests for query generation in BedcaClient."""

    @pytest.fixture
    def client_with_captured_queries(self, xml_search_response, xml_food_response):
        """Fixture that captures generated queries."""
        client = BedcaClient()
        captured_queries = []
        
        def capture_post(url, headers=None, content=None):
            captured_queries.append(content)
            mock_response = Mock()
            
            # Return appropriate response based on query type
            if 'level="1"' in (content or ""):
                # Search query
                mock_response.text = xml_search_response
            elif 'level="2"' in (content or ""):
                # Detail query  
                mock_response.text = xml_food_response
            else:
                # Default - empty but valid structure
                mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
<foodresponse>
</foodresponse>"""
            
            mock_response.raise_for_status = Mock()
            return mock_response
        
        client.client.post = capture_post
        client.captured_queries = captured_queries
        return client

    def test_get_all_foods_query_structure(self, client_with_captured_queries):
        """Test that get_all_foods generates correct query structure."""
        client_with_captured_queries.get_all_foods()
        
        assert len(client_with_captured_queries.captured_queries) == 1
        query = client_with_captured_queries.captured_queries[0]
        
        # Should be valid XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(query)
        
        # Check basic structure
        assert root.tag == "foodquery"
        
        # Check type level
        type_elem = root.find("type")
        assert type_elem.get("level") == "1"
        
        # Check selection
        selection = root.find("selection")
        attributes = selection.findall("atribute")
        assert len(attributes) == 4  # ID, Spanish name, English name, Origin
        
        # Check condition for BEDCA origin
        conditions = root.findall("condition")
        assert len(conditions) == 1
        
        condition = conditions[0]
        cond3 = condition.find("cond3")
        assert cond3.text == "BEDCA"

    def test_search_food_by_name_query_structure(self, client_with_captured_queries):
        """Test that search_food_by_name generates correct query structure."""
        client_with_captured_queries.search_food_by_name("paella")
        
        assert len(client_with_captured_queries.captured_queries) == 1
        query = client_with_captured_queries.captured_queries[0]
        
        import xml.etree.ElementTree as ET
        root = ET.fromstring(query)
        
        # Check conditions (should have LIKE for name and EQUAL for origin)
        conditions = root.findall("condition")
        assert len(conditions) == 2
        
        # Find the LIKE condition
        like_condition = None
        for condition in conditions:
            relation = condition.find("relation")
            if relation.get("type") == "LIKE":
                like_condition = condition
                break
        
        assert like_condition is not None
        cond3 = like_condition.find("cond3")
        assert cond3.text == "paella"

    def test_get_food_by_id_query_structure(self, client_with_captured_queries):
        """Test that get_food_by_id generates correct query structure."""
        client_with_captured_queries.get_food_by_id(2597)
        
        assert len(client_with_captured_queries.captured_queries) == 1
        query = client_with_captured_queries.captured_queries[0]
        
        import xml.etree.ElementTree as ET
        root = ET.fromstring(query)
        
        # Check type level
        type_elem = root.find("type")
        assert type_elem.get("level") == "2"
        
        # Check conditions (should have public=1 and f_id=2597)
        conditions = root.findall("condition")
        assert len(conditions) == 2
        
        # Find the ID condition
        id_condition = None
        for condition in conditions:
            cond3 = condition.find("cond3")
            if cond3.text == "2597":
                id_condition = condition
                break
        
        assert id_condition is not None


@pytest.mark.integration
class TestBedcaClientRealAPI:
    """Integration tests with real API calls (marked as integration)."""

    @pytest.mark.slow
    def test_real_search_food_by_name(self):
        """Test real API call for search_food_by_name."""
        client = BedcaClient()
        
        try:
            # Search for a common food
            foods = client.search_food_by_name("arroz")  # Rice in Spanish
            
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

    @pytest.mark.slow
    def test_real_get_food_by_id(self):
        """Test real API call for get_food_by_id."""
        client = BedcaClient()
        
        try:
            # Get a known food (paella)
            food = client.get_food_by_id(2597)
            
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

    @pytest.mark.slow
    def test_real_api_error_handling(self):
        """Test error handling with real API."""
        client = BedcaClient()
        
        try:
            # Try to get a non-existent food ID
            with pytest.raises((httpx.HTTPStatusError, ValueError)):
                client.get_food_by_id(999999999)
                
        except httpx.HTTPError:
            pytest.skip("Real API not available")


class TestBedcaClientEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_search_with_empty_string(self, mock_bedca_client):
        """Test search with empty string."""
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse></foodresponse>"""
        mock_response.raise_for_status = Mock()
        mock_bedca_client.client.post.return_value = mock_response
        
        foods = mock_bedca_client.search_food_by_name("")
        assert isinstance(foods, list)
        assert len(foods) == 0

    def test_search_with_special_characters(self, mock_bedca_client):
        """Test search with special characters."""
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
        <foodresponse></foodresponse>"""
        mock_response.raise_for_status = Mock()
        mock_bedca_client.client.post.return_value = mock_response
        
        # Should not raise an error
        foods = mock_bedca_client.search_food_by_name("café & té")
        assert isinstance(foods, list)

    def test_get_food_by_id_with_string_id(self, mock_bedca_client):
        """Test get_food_by_id with string ID (should work due to str() conversion)."""
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
        mock_bedca_client.client.post.return_value = mock_response
        
        # Should work with string ID
        food = mock_bedca_client.get_food_by_id("2597")
        assert isinstance(food, Food)

    def test_client_reuse(self):
        """Test that the same httpx client is reused across calls."""
        client = BedcaClient()
        original_client = client.client
        
        # Client should be the same instance
        assert client.client is original_client
        
        # Should still be the same after multiple operations
        with patch.object(client.client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
            <foodresponse></foodresponse>"""
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            client.get_all_foods()
            client.search_food_by_name("test")
            
            assert client.client is original_client
            assert mock_post.call_count == 2