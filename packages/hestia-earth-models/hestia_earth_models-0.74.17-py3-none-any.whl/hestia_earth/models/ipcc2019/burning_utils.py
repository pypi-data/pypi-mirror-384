from enum import Enum


class FuelCategory(Enum):
    """
    Natural vegetation fuel categories from IPCC (2019).
    """
    BOREAL_FOREST = "boreal-forest"
    DRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE = "drained-extratropical-organic-soils-wildfire"
    DRAINED_TROPICAL_ORGANIC_SOILS_WILDFIRE = "drained-tropical-organic-soils-wildfire"
    EUCALYPT_FOREST = "eucalypt-forest"
    NATURAL_TROPICAL_FOREST = "natural-tropical-forest"  # mean of primary and secondary tropical forest
    PEATLAND_VEGETATION = "peatland-vegetation"
    PRIMARY_TROPICAL_FOREST = "primary-tropical-forest"
    SAVANNA_GRASSLAND_EARLY_DRY_SEASON_BURNS = "savanna-grassland-early-dry-season-burns"
    SAVANNA_GRASSLAND_MID_TO_LATE_DRY_SEASON_BURNS = "savanna-grassland-mid-to-late-dry-season-burns"
    SAVANNA_WOODLAND_EARLY_DRY_SEASON_BURNS = "savanna-woodland-early-dry-season-burns"
    SAVANNA_WOODLAND_MID_TO_LATE_DRY_SEASON_BURNS = "savanna-woodland-mid-to-late-dry-season-burns"
    SECONDARY_TROPICAL_FOREST = "secondary-tropical-forest"
    SHRUBLAND = "shrubland"
    TEMPERATE_FOREST = "temperate-forest"
    TERTIARY_TROPICAL_FOREST = "tertiary-tropical-forest"
    TROPICAL_ORGANIC_SOILS_PRESCRIBED_FIRE = "tropical-organic-soils-prescribed-fire"
    TUNDRA = "tundra"
    UNDRAINED_EXTRATROPICAL_ORGANIC_SOILS_WILDFIRE = "undrained-extratropical-organic-soils-wildfire"
    UNKNOWN_TROPICAL_FOREST = "unknown-tropical-forest"  # mean of primary, secondary and tertiary tropical forest


class EmissionCategory(Enum):
    """
    Natural vegetation burning emission categories from IPCC (2019).
    """
    AGRICULTURAL_RESIDUES = "agricultural-residues"
    BIOFUEL_BURNING = "biofuel-burning"
    OTHER_FOREST = "other-forest"
    SAVANNA_AND_GRASSLAND = "savanna-and-grassland"
    TROPICAL_FOREST = "tropical-forest"
