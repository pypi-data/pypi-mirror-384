"""XML response fixtures for pybedca tests."""

from pathlib import Path

BASE_PATH = Path(__file__).parent / "data" 


def load_xml_fixture(filename: str) -> str:
    """Load XML fixture from the data directory.
    
    Args:
        filename: Name of the XML file to load
        
    Returns:
        str: Content of the XML file
    """
    fixture_path = BASE_PATH / filename
    return fixture_path.read_text(encoding="utf-8")


class XMLFixtures:
    """Container for XML test fixtures."""
    
    @property
    def food_response(self) -> str:
        """Complete food data with all nutritional information."""
        return load_xml_fixture("food_response.xml")
    
    @property
    def food_search_response(self) -> str:
        """Search results with multiple food items."""
        return load_xml_fixture("food_search_response.xml")
    
    @property
    def get_food_by_id_query(self) -> str:
        """Query structure for detailed food requests."""
        return load_xml_fixture("get_food_by_id.xml")
    
    @property
    def search_food_by_name_query(self) -> str:
        """Query structure for name-based searches."""
        return load_xml_fixture("search_food_by_name.xml")


# Global instance for easy access
xml_fixtures = XMLFixtures()