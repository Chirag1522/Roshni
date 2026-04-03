"""
Custom validators for ROSHNI entities.
"""
import re
from typing import Optional

def validate_house_id(house_id: str) -> bool:
    """Validate house ID format: HOUSE_FDR12_XXX"""
    return bool(re.match(r"^HOUSE_[A-Z0-9]+_\d{3}$", house_id))

def validate_feeder_code(feeder_code: str) -> bool:
    """Validate feeder code format: FDR_XX"""
    return bool(re.match(r"^FDR_[A-Z0-9]{1,10}$", feeder_code))

def validate_kwh(kwh: float) -> bool:
    """Validate kWh value is positive."""
    return isinstance(kwh, (int, float)) and kwh >= 0

def validate_priority_level(level: int) -> bool:
    """Validate priority level 1-10."""
    return isinstance(level, int) and 1 <= level <= 10