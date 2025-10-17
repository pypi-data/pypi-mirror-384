"""Helium Event"""

from dataclasses import dataclass

from edf_fusion.concept import Event as FusionEvent


@dataclass(kw_only=True)
class Event(FusionEvent):
    """Helium Event"""

    source: str = 'helium'
