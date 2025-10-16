"""BEDCA API client implementation."""

from typing import List, Union
import xml.etree.ElementTree as ET

import httpx

from .query import BedcaQueryBuilder
from .models import FoodPreview, Food
from .parser import parse_food_response
from .enums import Languages, BedcaRelation, BedcaAttribute


class BedcaClient:
    """Client for interacting with the BEDCA API."""

    BASE_URL = "https://www.bedca.net/bdpub/procquery.php"

    def __init__(self):
        """Initialize the BEDCA client."""
        self.client = httpx.Client()
        self.async_client = httpx.AsyncClient()
        self.headers = {
            "Content-Type": "text/xml",
            "User-Agent": "Python-pybedca",
            "Origin": "https://www.bedca.net",
            "Referer": "https://www.bedca.net/bdpub/index.php",
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()

    def close(self):
        """Close the HTTP clients."""
        self.client.close()

    async def aclose(self):
        """Close the async HTTP client."""
        await self.async_client.aclose()

    @staticmethod
    def _validate_language(language: Languages) -> None:
        """Validate language parameter.
        
        Args:
            language: The language to validate.
            
        Raises:
            ValueError: If language is invalid.
        """
        if language not in Languages:
            raise ValueError(f"Invalid language: {language}. Must be one of: {[lang for lang in Languages]}")

    @staticmethod
    def _build_get_all_foods_query() -> str:
        """Build query for getting all foods.
        
        Returns:
            str: XML query string.
        """
        return (
            BedcaQueryBuilder(level=1)
            .select(
                BedcaAttribute.ID,
                BedcaAttribute.SPANISH_NAME,
                BedcaAttribute.ENGLISH_NAME,
                BedcaAttribute.ORIGIN,
            )
            .where(BedcaAttribute.ORIGIN, BedcaRelation.EQUAL, "BEDCA")
            .order(BedcaAttribute.SPANISH_NAME)
            .build()
        )

    @staticmethod
    def _build_search_query(search_query: str, language: Languages) -> str:
        """Build query for searching foods by name.
        
        Args:
            search_query: The substring to search for.
            language: The language to search in.
            
        Returns:
            str: XML query string.
        """
        language_name_map = {
            Languages.ES: BedcaAttribute.SPANISH_NAME,
            Languages.EN: BedcaAttribute.ENGLISH_NAME
        }
        search_attribute = language_name_map[language]
        return (
            BedcaQueryBuilder(level=1)
            .select(
                BedcaAttribute.ID,
                BedcaAttribute.SPANISH_NAME,
                BedcaAttribute.ENGLISH_NAME,
                BedcaAttribute.ORIGIN,
            )
            .where(search_attribute, BedcaRelation.LIKE, search_query)
            .where(BedcaAttribute.ORIGIN, BedcaRelation.EQUAL, "BEDCA")
            .order(search_attribute)
            .build()
        )

    @staticmethod
    def _build_get_food_by_id_query(food_id: Union[int, str]) -> str:
        """Build query for getting food by ID.
        
        Args:
            food_id: The ID of the food to fetch.
            
        Returns:
            str: XML query string.
        """
        return (
            BedcaQueryBuilder(level=2)
            .select(
                *[attr for attr in BedcaAttribute]  # Select all attributes
            )
            .where(BedcaAttribute.ID, BedcaRelation.EQUAL, str(food_id))
            .order(BedcaAttribute.COMPONENT_GROUP_ID)
            .build()
        )

    @staticmethod
    def _parse_food_previews(xml_text: str) -> List[FoodPreview]:
        """Parse XML response into FoodPreview objects.
        
        Args:
            xml_text: XML response text.
            
        Returns:
            List[FoodPreview]: List of parsed food previews.
        """
        root = ET.fromstring(xml_text)
        return [
            FoodPreview(
                id=food.findtext("f_id"),
                name_es=food.findtext("f_ori_name"),
                name_en=food.findtext("f_eng_name"),
            )
            for food in root.findall("food")
        ]

    def get_all_foods(self) -> List[FoodPreview]:
        """Get all food products from BEDCA.

        Returns:
            List[FoodPreview]: A list of FoodPreview objects containing basic information about each food item.
        """
        query = self._build_get_all_foods_query()
        response = self.client.post(self.BASE_URL, headers=self.headers, content=query)
        response.raise_for_status()
        return self._parse_food_previews(response.text)

    def search_food_by_name(self, search_query: str, language: Languages = Languages.ES) -> List[FoodPreview]:
        """Search for foods by name using a basic substring match (LIKE '%search_query%').

        Args:
            search_query: The substring to search for in the food name.
            language: The language to search in (default is Spanish).

        Returns:
            List[FoodPreview]: A list of FoodPreview objects containing only id, name_es, and name_en.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        self._validate_language(language)
        query = self._build_search_query(search_query, language)
        response = self.client.post(self.BASE_URL, headers=self.headers, content=query)
        response.raise_for_status()
        return self._parse_food_previews(response.text)

    def get_food_by_id(self, food_id: Union[int, str]) -> Food:
        """Get detailed information about a specific food by its ID.
        
        Args:
            food_id: The ID of the food to fetch.
            
        Returns:
            Food: Object with all the nutritional value.
            
        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        query = self._build_get_food_by_id_query(food_id)
        response = self.client.post(self.BASE_URL, headers=self.headers, content=query)
        response.raise_for_status()
        return parse_food_response(response.text)

    async def get_all_foods_async(self) -> List[FoodPreview]:
        """Get all food products from BEDCA (async).

        Returns:
            List[FoodPreview]: A list of FoodPreview objects containing basic information about each food item.
        """
        query = self._build_get_all_foods_query()
        response = await self.async_client.post(self.BASE_URL, headers=self.headers, content=query)
        response.raise_for_status()
        return self._parse_food_previews(response.text)

    async def search_food_by_name_async(self, search_query: str, language: Languages = Languages.ES) -> List[FoodPreview]:
        """Search for foods by name using a basic substring match (LIKE '%search_query%') (async).

        Args:
            search_query: The substring to search for in the food name.
            language: The language to search in (default is Spanish).

        Returns:
            List[FoodPreview]: A list of FoodPreview objects containing only id, name_es, and name_en.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        self._validate_language(language)
        query = self._build_search_query(search_query, language)
        response = await self.async_client.post(self.BASE_URL, headers=self.headers, content=query)
        response.raise_for_status()
        return self._parse_food_previews(response.text)

    async def get_food_by_id_async(self, food_id: Union[int, str]) -> Food:
        """Get detailed information about a specific food by its ID (async).
        
        Args:
            food_id: The ID of the food to fetch.
            
        Returns:
            Food: Object with all the nutritional value.
            
        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        query = self._build_get_food_by_id_query(food_id)
        response = await self.async_client.post(self.BASE_URL, headers=self.headers, content=query)
        response.raise_for_status()
        return parse_food_response(response.text)
