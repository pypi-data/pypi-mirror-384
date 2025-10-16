"""Unit tests for the value conversion system."""

import pytest
from decimal import Decimal

from pybedca.values import Mass, Energy, MassUnit, EnergyUnit, MASS_TO_GRAMS, KJ_TO_KCAL


class TestMassUnit:
    """Tests for the MassUnit enum."""

    def test_mass_unit_values(self):
        """Test that MassUnit has expected values."""
        assert MassUnit.MICROGRAMS == "µg"
        assert MassUnit.MICROGRAMS_ALT == "ug"
        assert MassUnit.MILLIGRAMS == "mg"
        assert MassUnit.GRAMS == "g"
        assert MassUnit.KILOGRAMS == "kg"

    def test_mass_to_grams_conversion_factors(self):
        """Test that mass conversion factors are correct."""
        assert MASS_TO_GRAMS[MassUnit.MICROGRAMS] == Decimal("0.000001")
        assert MASS_TO_GRAMS[MassUnit.MICROGRAMS_ALT] == Decimal("0.000001")
        assert MASS_TO_GRAMS[MassUnit.MILLIGRAMS] == Decimal("0.001")
        assert MASS_TO_GRAMS[MassUnit.GRAMS] == Decimal("1")
        assert MASS_TO_GRAMS[MassUnit.KILOGRAMS] == Decimal("1000")


class TestEnergyUnit:
    """Tests for the EnergyUnit enum."""

    def test_energy_unit_values(self):
        """Test that EnergyUnit has expected values."""
        assert EnergyUnit.KILOCALORIES == "kcal"
        assert EnergyUnit.KILOJOULES == "kJ"

    def test_kj_to_kcal_conversion_factor(self):
        """Test that kJ to kcal conversion factor is correct."""
        # 1 kJ = 0.239006 kcal (approximately)
        assert abs(KJ_TO_KCAL - Decimal("0.239006")) < Decimal("0.000001")


class TestMass:
    """Tests for the Mass class."""

    def test_mass_creation_from_grams(self):
        """Test creating Mass from grams."""
        mass = Mass.from_value(100, "g")
        
        assert mass.original_unit == MassUnit.GRAMS
        assert mass._value_in_grams == Decimal("100")
        assert mass.value == Decimal("100")

    def test_mass_creation_from_milligrams(self):
        """Test creating Mass from milligrams."""
        mass = Mass.from_value(1000, "mg")
        
        assert mass.original_unit == MassUnit.MILLIGRAMS
        assert mass._value_in_grams == Decimal("1")  # 1000 mg = 1 g
        assert mass.value == Decimal("1000")

    def test_mass_creation_from_micrograms(self):
        """Test creating Mass from micrograms."""
        mass = Mass.from_value(1000000, "µg")
        
        assert mass.original_unit == MassUnit.MICROGRAMS
        assert mass._value_in_grams == Decimal("1")  # 1,000,000 µg = 1 g
        assert mass.value == Decimal("1000000")

    def test_mass_creation_from_micrograms_alt(self):
        """Test creating Mass from alternative microgram notation."""
        mass = Mass.from_value(1000000, "ug")
        
        # Should be converted to standard microgram unit
        assert mass.original_unit == MassUnit.MICROGRAMS
        assert mass._value_in_grams == Decimal("1")

    def test_mass_creation_from_kilograms(self):
        """Test creating Mass from kilograms."""
        mass = Mass.from_value(0.5, "kg")
        
        assert mass.original_unit == MassUnit.KILOGRAMS
        assert mass._value_in_grams == Decimal("500")  # 0.5 kg = 500 g
        assert mass.value == Decimal("0.5")

    def test_mass_creation_from_string_value(self):
        """Test creating Mass from string value."""
        mass = Mass.from_value("12.37", "g")
        
        assert mass.value == Decimal("12.37")
        assert mass.original_unit == MassUnit.GRAMS

    def test_mass_creation_from_decimal_value(self):
        """Test creating Mass from Decimal value."""
        mass = Mass.from_value(Decimal("12.37"), "g")
        
        assert mass.value == Decimal("12.37")
        assert mass.original_unit == MassUnit.GRAMS

    def test_mass_to_unit_conversion_grams_to_milligrams(self):
        """Test converting grams to milligrams."""
        mass = Mass.from_value(1, "g")
        mg_value = mass.to_unit("mg")
        
        assert mg_value == Decimal("1000")

    def test_mass_to_unit_conversion_milligrams_to_grams(self):
        """Test converting milligrams to grams."""
        mass = Mass.from_value(1000, "mg")
        g_value = mass.to_unit("g")
        
        assert g_value == Decimal("1")

    def test_mass_to_unit_conversion_grams_to_micrograms(self):
        """Test converting grams to micrograms."""
        mass = Mass.from_value(1, "g")
        ug_value = mass.to_unit("µg")
        
        assert ug_value == Decimal("1000000")

    def test_mass_to_unit_conversion_with_enum(self):
        """Test converting using MassUnit enum."""
        mass = Mass.from_value(1, "g")
        mg_value = mass.to_unit(MassUnit.MILLIGRAMS)
        
        assert mg_value == Decimal("1000")

    def test_mass_string_representation(self):
        """Test Mass string representation."""
        mass = Mass.from_value(12.37, "g")
        str_repr = str(mass)
        
        assert "12.37" in str_repr
        assert "g" in str_repr

    def test_mass_string_representation_with_rounding(self):
        """Test Mass string representation with rounding."""
        mass = Mass.from_value(12.3456789, "g")
        str_repr = str(mass)
        
        # Should be rounded to 2 decimal places
        assert "12.35" in str_repr or "12.34" in str_repr
        assert "g" in str_repr

    def test_mass_value_property(self):
        """Test that value property returns original unit value."""
        mass = Mass.from_value(1000, "mg")
        
        # Value property should return in original unit (mg)
        assert mass.value == Decimal("1000")
        
        # But internal storage is in grams
        assert mass._value_in_grams == Decimal("1")


class TestEnergy:
    """Tests for the Energy class."""

    def test_energy_creation_from_kcal(self):
        """Test creating Energy from kilocalories."""
        energy = Energy.from_value(100, "kcal")
        
        assert energy._value_in_kcal == Decimal("100")
        assert energy.kcal == Decimal("100")

    def test_energy_creation_from_kj(self):
        """Test creating Energy from kilojoules."""
        energy = Energy.from_value(418.4, "kJ")
        
        # Should be converted to kcal internally
        expected_kcal = Decimal("418.4") * KJ_TO_KCAL
        assert abs(energy._value_in_kcal - expected_kcal) < Decimal("0.01")

    def test_energy_creation_from_string_value(self):
        """Test creating Energy from string value."""
        energy = Energy.from_value("719.15", "kJ")
        
        expected_kcal = Decimal("719.15") * KJ_TO_KCAL
        assert abs(energy._value_in_kcal - expected_kcal) < Decimal("0.01")

    def test_energy_creation_from_decimal_value(self):
        """Test creating Energy from Decimal value."""
        energy = Energy.from_value(Decimal("100"), "kcal")
        
        assert energy.kcal == Decimal("100")

    def test_energy_creation_with_enum_unit(self):
        """Test creating Energy with EnergyUnit enum."""
        energy = Energy.from_value(100, EnergyUnit.KILOCALORIES)
        
        assert energy.kcal == Decimal("100")

    def test_energy_kcal_property(self):
        """Test Energy kcal property."""
        energy = Energy.from_value(100, "kcal")
        
        assert energy.kcal == Decimal("100")

    def test_energy_kj_property(self):
        """Test Energy kJ property."""
        energy = Energy.from_value(100, "kcal")
        
        expected_kj = Decimal("100") / KJ_TO_KCAL
        assert abs(energy.kj - expected_kj) < Decimal("0.01")

    def test_energy_kj_to_kcal_conversion(self):
        """Test kJ to kcal conversion accuracy."""
        # 1 kcal = 4.184 kJ (approximately)
        energy = Energy.from_value(4.184, "kJ")
        
        # Should be approximately 1 kcal
        assert abs(energy.kcal - Decimal("1")) < Decimal("0.01")

    def test_energy_string_representation(self):
        """Test Energy string representation."""
        energy = Energy.from_value(100, "kcal")
        str_repr = str(energy)
        
        assert "100" in str_repr
        assert "kcal" in str_repr

    def test_energy_string_representation_from_kj(self):
        """Test Energy string representation when created from kJ."""
        energy = Energy.from_value(418.4, "kJ")
        str_repr = str(energy)
        
        # Should display in kcal
        assert "kcal" in str_repr
        # Should show approximately 100 kcal
        assert "100" in str_repr or "99.9" in str_repr

    def test_energy_string_representation_with_rounding(self):
        """Test Energy string representation with rounding."""
        energy = Energy.from_value(100.123456, "kcal")
        str_repr = str(energy)
        
        # Should be rounded to 2 decimal places
        assert "100.12" in str_repr
        assert "kcal" in str_repr


class TestValueConversions:
    """Tests for value conversion edge cases and complex scenarios."""

    def test_mass_zero_value(self):
        """Test Mass with zero value."""
        mass = Mass.from_value(0, "g")
        
        assert mass.value == Decimal("0")
        assert mass.to_unit("mg") == Decimal("0")
        assert mass.to_unit("µg") == Decimal("0")

    def test_energy_zero_value(self):
        """Test Energy with zero value."""
        energy = Energy.from_value(0, "kcal")
        
        assert energy.kcal == Decimal("0")
        assert energy.kj == Decimal("0")

    def test_mass_very_small_value(self):
        """Test Mass with very small value."""
        mass = Mass.from_value(0.001, "µg")
        
        # Should handle very small values correctly
        assert mass.value == Decimal("0.001")
        g_value = mass.to_unit("g")
        assert g_value == Decimal("1E-9")

    def test_mass_very_large_value(self):
        """Test Mass with very large value."""
        mass = Mass.from_value(1000, "kg")
        
        assert mass.value == Decimal("1000")
        g_value = mass.to_unit("g")
        assert g_value == Decimal("1000000")

    def test_energy_conversion_precision(self):
        """Test Energy conversion precision."""
        # Test with the actual paella energy value from the XML
        energy = Energy.from_value(719.15, "kJ")
        
        # Convert to kcal and back to kJ
        kcal_value = energy.kcal
        kj_value = energy.kj
        
        # Should be close to original value
        assert abs(kj_value - Decimal("719.15")) < Decimal("0.1")

    def test_mass_conversion_chain(self):
        """Test chaining mass conversions."""
        # Start with 1 gram
        mass = Mass.from_value(1, "g")
        
        # Convert to mg, then back to g
        mg_value = mass.to_unit("mg")
        assert mg_value == Decimal("1000")
        
        # Create new mass from mg value
        mass_from_mg = Mass.from_value(mg_value, "mg")
        g_value = mass_from_mg.to_unit("g")
        
        # Should be back to 1 gram
        assert g_value == Decimal("1")


@pytest.mark.unit
class TestValueIntegration:
    """Integration tests for value classes."""

    def test_realistic_nutritional_values(self):
        """Test with realistic nutritional values from paella."""
        # Test protein value (12.37 g)
        protein = Mass.from_value(12.37, "g")
        assert protein.value == Decimal("12.37")
        assert protein.to_unit("mg") == Decimal("12370")
        
        # Test energy value (719.15 kJ)
        energy = Energy.from_value(719.15, "kJ")
        # Should be approximately 172 kcal
        assert abs(energy.kcal - Decimal("172")) < Decimal("1")
        
        # Test vitamin value (11.12 µg)
        vitamin = Mass.from_value(11.12, "µg")
        assert vitamin.value == Decimal("11.12")
        assert abs(vitamin.to_unit("mg") - Decimal("0.01112")) < Decimal("0.00001")

    def test_value_string_representations_consistency(self):
        """Test that string representations are consistent."""
        mass = Mass.from_value(12.37, "g")
        energy = Energy.from_value(719.15, "kJ")
        
        mass_str = str(mass)
        energy_str = str(energy)
        
        # Both should have reasonable string representations
        assert len(mass_str) > 0
        assert len(energy_str) > 0
        assert "g" in mass_str
        assert "kcal" in energy_str

    def test_value_equality_and_comparison(self):
        """Test value equality and comparison behavior."""
        mass1 = Mass.from_value(1000, "mg")
        mass2 = Mass.from_value(1, "g")
        
        # Both represent the same mass (1 gram)
        assert mass1._value_in_grams == mass2._value_in_grams
        
        energy1 = Energy.from_value(1, "kcal")
        energy2 = Energy.from_value(4.184, "kJ")
        
        # Both represent approximately the same energy
        assert abs(energy1._value_in_kcal - energy2._value_in_kcal) < Decimal("0.01")