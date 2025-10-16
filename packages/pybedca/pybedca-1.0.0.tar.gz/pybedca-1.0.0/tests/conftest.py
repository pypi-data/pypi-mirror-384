"""Pytest configuration and shared fixtures."""

from typing import Dict
from unittest.mock import Mock
import xml.etree.ElementTree as ET

import pytest

from pybedca.client import BedcaClient
from pybedca.models import FoodPreview, Food
from tests.fixtures.xml_responses import xml_fixtures
from tests.fixtures.sample_data import (
    get_sample_food_previews,
    get_sample_food,
    get_sample_food_nutrients,
    get_sample_food_value,
    get_sample_energy_value,
    get_sample_trace_value
)


@pytest.fixture
def xml_food_response():
    """Fixture providing the complete food response XML."""
    return xml_fixtures.food_response


@pytest.fixture
def xml_search_response():
    """Fixture providing the food search response XML."""
    return xml_fixtures.food_search_response


@pytest.fixture
def xml_get_food_query():
    """Fixture providing the get food by ID query XML."""
    return xml_fixtures.get_food_by_id_query


@pytest.fixture
def xml_search_query():
    """Fixture providing the search food by name query XML."""
    return xml_fixtures.search_food_by_name_query


@pytest.fixture
def sample_food_previews():
    """Fixture providing sample FoodPreview objects."""
    return get_sample_food_previews()


@pytest.fixture
def sample_food():
    """Fixture providing a sample Food object."""
    return get_sample_food()


@pytest.fixture
def sample_food_nutrients():
    """Fixture providing sample FoodNutrients."""
    return get_sample_food_nutrients()


@pytest.fixture
def sample_food_value():
    """Fixture providing a sample FoodValue."""
    return get_sample_food_value()


@pytest.fixture
def sample_energy_value():
    """Fixture providing a sample energy FoodValue."""
    return get_sample_energy_value()


@pytest.fixture
def sample_trace_value():
    """Fixture providing a sample trace FoodValue."""
    return get_sample_trace_value()


@pytest.fixture
def mock_response():
    """Fixture providing a mock HTTP response."""
    def _create_mock_response(text: str, status_code: int = 200, headers: Dict[str, str] = None):
        mock = Mock()
        mock.text = text
        mock.status_code = status_code
        mock.headers = headers or {}
        mock.raise_for_status = Mock()
        return mock
    return _create_mock_response


@pytest.fixture
def mock_httpx_client(mock_response):
    """Fixture providing a mock httpx client."""
    def _create_mock_client(response_text: str = None):
        client = Mock()
        if response_text:
            client.post.return_value = mock_response(response_text)
        return client
    return _create_mock_client


@pytest.fixture
def bedca_client():
    """Fixture providing a BedcaClient instance."""
    return BedcaClient()


@pytest.fixture
def mock_bedca_client(mock_httpx_client):
    """Fixture providing a BedcaClient with mocked httpx client."""
    client = BedcaClient()
    client.client = mock_httpx_client()
    return client


@pytest.fixture
def mock_http_response():
    """Fixture for creating mock HTTP responses."""
    def _create_response(status_code=200, text="", headers=None, raise_for_status=None):
        response = Mock()
        response.status_code = status_code
        response.text = text
        response.headers = headers or {}
        
        if raise_for_status:
            response.raise_for_status.side_effect = raise_for_status
        else:
            response.raise_for_status = Mock()
        
        return response
    return _create_response


@pytest.fixture
def xml_validator():
    """Fixture for validating XML structure."""
    def _validate_xml(xml_string, expected_root_tag=None, expected_elements=None):
        """Validate XML structure and content."""
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML: {e}")
        
        if expected_root_tag:
            assert root.tag == expected_root_tag, f"Expected root tag '{expected_root_tag}', got '{root.tag}'"
        
        if expected_elements:
            for element_path in expected_elements:
                element = root.find(element_path)
                assert element is not None, f"Expected element '{element_path}' not found"
        
        return root
    return _validate_xml


@pytest.fixture
def assert_food_preview_valid():
    """Fixture for validating FoodPreview objects."""
    def _validate(food_preview):
        """Validate that a FoodPreview object has required attributes."""
        assert isinstance(food_preview, FoodPreview)
        assert hasattr(food_preview, 'id')
        assert hasattr(food_preview, 'name_es')
        assert hasattr(food_preview, 'name_en')
        assert isinstance(food_preview.id, str)
        assert isinstance(food_preview.name_es, str)
        assert isinstance(food_preview.name_en, str)
        assert len(food_preview.id) > 0
        assert len(food_preview.name_es) > 0
    return _validate


@pytest.fixture
def assert_food_valid():
    """Fixture for validating Food objects."""
    def _validate(food):
        """Validate that a Food object has required attributes and structure."""
        assert isinstance(food, Food)
        assert hasattr(food, 'id')
        assert hasattr(food, 'name_es')
        assert hasattr(food, 'name_en')
        assert hasattr(food, 'scientific_name')
        assert hasattr(food, 'nutrients')
        
        # Validate basic attributes
        assert isinstance(food.id, str)
        assert isinstance(food.name_es, str)
        assert isinstance(food.name_en, str)
        assert len(food.id) > 0
        assert len(food.name_es) > 0
        
        # Validate nutrients structure
        nutrients = food.nutrients
        required_nutrients = [
            'energy', 'protein', 'fat', 'carbohydrate', 'water', 'alcohol',
            'fiber', 'saturated_fat', 'monounsaturated_fat', 'polyunsaturated_fat',
            'cholesterol', 'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e',
            'calcium', 'iron', 'sodium', 'potassium'
        ]
        
        for nutrient_name in required_nutrients:
            assert hasattr(nutrients, nutrient_name), f"Missing nutrient: {nutrient_name}"
            nutrient = getattr(nutrients, nutrient_name)
            assert hasattr(nutrient, 'value')
            assert hasattr(nutrient, 'unit')
            assert hasattr(nutrient, 'component')
    
    return _validate


@pytest.fixture
def mock_httpx_session():
    """Fixture providing a comprehensive mock httpx client."""
    def _create_client(responses=None):
        """Create a mock httpx client with configurable responses."""
        client = Mock()
        
        if responses:
            # Configure responses based on URL or content patterns
            def mock_post(url, headers=None, content=None, **kwargs):
                for pattern, response_data in responses.items():
                    if pattern in (content or ""):
                        mock_resp = Mock()
                        mock_resp.text = response_data
                        mock_resp.status_code = 200
                        mock_resp.headers = {}
                        mock_resp.raise_for_status = Mock()
                        return mock_resp
                
                # Default response
                mock_resp = Mock()
                mock_resp.text = """<?xml version="1.0" encoding="utf-8"?>
                <foodresponse></foodresponse>"""
                mock_resp.status_code = 200
                mock_resp.headers = {}
                mock_resp.raise_for_status = Mock()
                return mock_resp
            
            client.post = mock_post
        else:
            # Simple mock
            mock_resp = Mock()
            mock_resp.text = """<?xml version="1.0" encoding="utf-8"?>
<foodresponse>
</foodresponse>"""
            mock_resp.status_code = 200
            mock_resp.headers = {}
            mock_resp.raise_for_status = Mock()
            client.post.return_value = mock_resp
        
        return client
    
    return _create_client


@pytest.fixture
def integration_client():
    """Fixture providing a client configured for integration testing."""
    def _create_client(mock_responses=None):
        """Create a client with optional mock responses for integration testing."""
        client = BedcaClient()
        
        if mock_responses:
            mock_client = Mock()
            
            def mock_post(url, headers=None, content=None, **kwargs):
                # Determine response based on query type
                if 'level="1"' in (content or ""):
                    # Search query
                    return Mock(
                        text=mock_responses.get('search', xml_fixtures.food_search_response),
                        status_code=200,
                        raise_for_status=Mock()
                    )
                elif 'level="2"' in (content or ""):
                    # Detail query
                    return Mock(
                        text=mock_responses.get('detail', xml_fixtures.food_response),
                        status_code=200,
                        raise_for_status=Mock()
                    )
                else:
                    # Default - empty but valid XML structure
                    return Mock(
                        text="""<?xml version="1.0" encoding="utf-8"?>
<foodresponse>
</foodresponse>""",
                        status_code=200,
                        raise_for_status=Mock()
                    )
            
            mock_client.post = mock_post
            client.client = mock_client
        
        return client
    
    return _create_client


@pytest.fixture(scope="session")
def test_data_cache():
    """Session-scoped fixture for caching test data."""
    cache = {}
    
    # Pre-load common test data
    cache['xml_fixtures'] = xml_fixtures
    cache['sample_foods'] = get_sample_food_previews()
    cache['sample_food'] = get_sample_food()
    
    return cache


@pytest.fixture
def performance_timer():
    """Fixture for timing test operations."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


@pytest.fixture
def temp_xml_file(tmp_path):
    """Fixture for creating temporary XML files for testing."""
    def _create_xml_file(content, filename="test.xml"):
        """Create a temporary XML file with given content."""
        xml_file = tmp_path / filename
        xml_file.write_text(content, encoding="utf-8")
        return xml_file
    
    return _create_xml_file


@pytest.fixture
def workflow_client(xml_search_response, xml_food_response):
    """Client configured for workflow testing."""
    client = BedcaClient()
    
    # Mock httpx client to return appropriate responses
    mock_client = Mock()
    
    def mock_post(url, headers=None, content=None):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        
        # Determine response based on query content
        if 'level="1"' in content:
            # Search query
            mock_response.text = xml_search_response
        elif 'level="2"' in content:
            # Detail query
            mock_response.text = xml_food_response
        else:
            # Default response with proper structure
            mock_response.text = xml_search_response
        
        return mock_response
    
    mock_client.post = mock_post
    client.client = mock_client
    return client


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Markers are now defined in pyproject.toml, no need to duplicate here
    pass


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to tests in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests with "slow" in name or marked as integration
        if "slow" in item.name.lower() or "integration" in str(item.fspath):
            item.add_marker(pytest.mark.slow)


# Command line options
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help="Run network tests"
    )
    parser.addoption(
        "--run-real-api",
        action="store_true", 
        default=False,
        help="Run real API tests"
    )


# Skip markers for conditional test execution
def skip_if_no_network(request):
    """Skip test if network tests are disabled."""
    if not request.config.getoption("--run-network"):
        pytest.skip("Network tests disabled (use --run-network to enable)")


def skip_if_no_real_api(request):
    """Skip test if real API tests are disabled."""
    if not request.config.getoption("--run-real-api"):
        pytest.skip("Real API tests disabled (use --run-real-api to enable)")