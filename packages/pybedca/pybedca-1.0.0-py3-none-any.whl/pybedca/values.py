"""Value handling classes for BEDCA API client."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Dict, Union, Literal

class MassUnit(StrEnum):
    """Available mass units."""
    MICROGRAMS = "µg"
    MICROGRAMS_ALT = "ug"  # Alternative representation
    MILLIGRAMS = "mg"
    GRAMS = "g"
    KILOGRAMS = "kg"

# Conversion factors to grams
MASS_TO_GRAMS: Dict[MassUnit, Decimal] = {
    MassUnit.MICROGRAMS: Decimal("0.000001"),
    MassUnit.MICROGRAMS_ALT: Decimal("0.000001"),
    MassUnit.MILLIGRAMS: Decimal("0.001"),
    MassUnit.GRAMS: Decimal("1"),
    MassUnit.KILOGRAMS: Decimal("1000"),
}

class EnergyUnit(StrEnum):
    """Available energy units."""
    KILOCALORIES = "kcal"
    KILOJOULES = "kJ"

# Conversion factor from kJ to kcal
KJ_TO_KCAL = Decimal("0.239006")

@dataclass
class Mass:
    """Represents a mass value that can be converted between units."""
    _value_in_grams: Decimal
    original_unit: MassUnit
    
    @classmethod
    def from_value(cls, value: Union[Decimal, float, str], unit: str) -> 'Mass':
        """Create a Mass instance from a value and unit."""
        value = Decimal(str(value))
        
        # Convert to StrEnum if string
        if isinstance(unit, str):
            unit = MassUnit(unit)

        # Handle alternative microgram representation
        if unit == MassUnit.MICROGRAMS_ALT:
            unit = MassUnit.MICROGRAMS
            
            
        # Convert to grams
        value_in_grams = value * MASS_TO_GRAMS[unit]
        
        return cls(_value_in_grams=value_in_grams, original_unit=unit)
    
    def to_unit(self, unit: Union[MassUnit, str]) -> Decimal:
        """Convert the stored mass to the specified unit."""
        if isinstance(unit, str):
            unit = MassUnit(unit)
            
        return self._value_in_grams / MASS_TO_GRAMS[unit]
    
    @property
    def value(self) -> Decimal:
        """Get the value in the original unit."""
        return self.to_unit(self.original_unit)

    def __str__(self) -> str:
        """Return string representation of the mass value."""
        return f"{round(self.value, 2)} {self.original_unit}"


@dataclass
class Energy:
    """Represents an energy value that can be converted between kJ and kcal."""
    _value_in_kcal: Decimal

    @classmethod
    def from_value(cls, value: Union[Decimal, float, str], unit: Union[EnergyUnit, str]) -> 'Energy':
        """Create an Energy instance from a value and unit."""
        value = Decimal(str(value))
            
        # Convert string unit to enum
        if isinstance(unit, str):
            unit = EnergyUnit(unit)
            
        # Convert to kcal if needed
        if unit == EnergyUnit.KILOJOULES:
            value = value * KJ_TO_KCAL
            
        return cls(_value_in_kcal=value)
    
    @property
    def kcal(self) -> Decimal:
        """Get the value in kilocalories."""
        return self._value_in_kcal
        
    @property
    def kj(self) -> Decimal:
        """Get the value in kilojoules."""
        return self._value_in_kcal / KJ_TO_KCAL
            
    def __str__(self) -> str:
        """Return string representation of the energy value."""
        return f"{round(self.kcal, 2)} kcal"
