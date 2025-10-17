from typing import Optional, Literal
from rapidfuzz import fuzz, process
from ..params.nominatim import STATES, PROVINCES, STANDARD_THRESHOLD
from .strings import normalize

def standardize_admin_division(
    name: str,
    level: Literal["province", "state"] = "province",
    country_code: str = "es"
) -> Optional[str]:
    """
    Normalize and standardize administrative divisions of a given country using RapidFuzz.
    Uses normalized dict keys for comparison and returns dict values with the official names.
    """
    if not name:
        return None

    country_code = country_code.lower()
    mapping = STATES.get(country_code) if level == "state" else PROVINCES.get(country_code)

    if not mapping: # If country is not standardized, return raw name
        return name

    normalized_name = normalize(name) # Essential for rapidfuzz to work well
    result = process.extractOne(
        normalized_name,
        mapping.keys(), # Compare with the normalized names in the dict
        scorer=fuzz.WRatio,
        score_cutoff=STANDARD_THRESHOLD,
    )

    if not result:
        return None

    best_key, score, _ = result
    
    # Return the standardized name corresponding to the normalized name
    return mapping[best_key]