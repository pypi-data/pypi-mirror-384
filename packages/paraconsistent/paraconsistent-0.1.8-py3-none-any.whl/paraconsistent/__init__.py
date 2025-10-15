# se usou subpasta "blocks"
from .blocks.block import ParaconsistentBlock
from .core import (
    BlockParams, ParaconsistentEngine, validate_and_merge,
    clamp01, radial_d_to_nearest_apex, Complete
)

__all__ = [
    "ParaconsistentBlock",
    "BlockParams", "ParaconsistentEngine", "validate_and_merge",
    "clamp01", "radial_d_to_nearest_apex", "Complete",
]