"""Enumerations for the BEDCA API client."""

from enum import StrEnum


class BedcaComponent(StrEnum):
    """Enum for BEDCA components."""
    # Proximales
    ALCOHOL = "alcohol (ethanol)"
    ENERGY = "energy, total metabolisable calculated from energy-producing food components"
    FAT = "fat, total (total lipid)"
    PROTEIN = "protein, total"
    WATER = "water (moisture)"
    
    # Hidratos de Carbono
    CARBOHYDRATE = "carbohydrate"
    FIBER = "fibre, total dietary"
    
    # Grasas
    MONOUNSATURATED = "fatty acids, total monounsaturated"
    POLYUNSATURATED = "fatty acids, total polyunsaturated"
    SATURATED = "fatty acids, total saturated"
    CHOLESTEROL = "cholesterol"
    
    # Vitaminas
    VITAMIN_A = "vitamin A retinol equiv from retinol and carotenoid activities"
    VITAMIN_D = "vitamin D"
    VITAMIN_E = "vitamin E alpha-tocopherol equiv from E vitamer activities"
    FOLATE = "folate, total"
    NIACIN = "niacin equivalents, total"
    RIBOFLAVIN = "riboflavin"
    THIAMIN = "thiamin"
    VITAMIN_B12 = "vitamin B-12"
    VITAMIN_B6 = "vitamin B-6, total"
    VITAMIN_C = "vitamin C (ascorbic acid)"
    
    # Minerales
    CALCIUM = "calcium"
    IRON = "iron, total"
    POTASSIUM = "potassium"
    MAGNESIUM = "magnesium"
    SODIUM = "sodium"
    PHOSPHORUS = "phosphorus"
    IODIDE = "iodide"
    SELENIUM = "selenium, total"
    ZINC = "zinc"


class BedcaAttribute(StrEnum):
    """Attributes available in BEDCA API."""
    
    # Food attributes
    ID = "f_id"
    SPANISH_NAME = "f_ori_name"
    ENGLISH_NAME = "f_eng_name"
    SCIENTIFIC_NAME = "sci_name"
    LANGUAL = "langual"
    FOODEX_CODE = "foodexcode"
    MAIN_LEVEL_CODE = "mainlevelcode"
    CODE_LEVEL_1 = "codlevel1"
    NAME_LEVEL_1 = "namelevel1"
    CODE_SUBLEVEL = "codsublevel"
    CODE_LEVEL_2 = "codlevel2"
    NAME_LEVEL_2 = "namelevel2"
    DESCRIPTION_ES = "f_des_esp"
    DESCRIPTION_EN = "f_des_ing"
    PHOTO = "photo"
    EDIBLE_PORTION = "edible_portion"
    ORIGIN = "f_origen"
    PUBLIC = "publico"
    
    # Component attributes
    COMPONENT_ID = "c_id"
    COMPONENT_NAME_ES = "c_ori_name"
    COMPONENT_NAME_EN = "c_eng_name"
    EURNAME = "eur_name"
    COMPONENT_GROUP_ID = "componentgroup_id"
    GLOSSARY_ES = "glos_esp"
    GLOSSARY_EN = "glos_ing"
    GROUP_NAME_ES = "cg_descripcion"
    GROUP_NAME_EN = "cg_description"
    BEST_LOCATION = "best_location"
    VALUE_UNIT = "v_unit"
    MOEX = "moex"
    STANDARD_DEVIATION = "stdv"
    MIN_VALUE = "min"
    MAX_VALUE = "max"
    N_VALUE = "v_n"
    UNIT_ID = "u_id"
    UNIT_NAME_ES = "u_descripcion"
    UNIT_NAME_EN = "u_description"
    VALUE_TYPE = "value_type"
    VALUE_TYPE_DESC_ES = "vt_descripcion"
    VALUE_TYPE_DESC_EN = "vt_description"
    MEASURE_UNIT_ID = "mu_id"
    MEASURE_UNIT_DESC_ES = "mu_descripcion"
    MEASURE_UNIT_DESC_EN = "mu_description"
    REFERENCE_ID = "ref_id"
    CITATION = "citation"
    ACQUISITION_TYPE_ES = "at_descripcion"
    ACQUISITION_TYPE_EN = "at_description"
    PUBLICATION_TYPE_ES = "pt_descripcion"
    PUBLICATION_TYPE_EN = "pt_description"
    METHOD_ID = "method_id"
    METHOD_TYPE_ES = "mt_descripcion"
    METHOD_TYPE_EN = "mt_description"
    METHOD_DESC_ES = "m_descripcion"
    METHOD_DESC_EN = "m_description"
    METHOD_NAME_ES = "m_nom_esp"
    METHOD_NAME_EN = "m_nom_ing"
    METHOD_HEADER_ES = "mhd_descripcion"
    METHOD_HEADER_EN = "mhd_description"


class BedcaRelation(StrEnum):
    """Relation types for BEDCA query conditions."""
    
    EQUAL = "EQUAL"
    LIKE = "LIKE"
    BEGINS_WITH = "BEGINW"


class Languages(StrEnum):
    ES = "ES"
    EN = "EN"
