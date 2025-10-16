from abc import ABCMeta
from dataclasses import dataclass, asdict, is_dataclass
from enum import Enum, StrEnum
from typing import Optional, Dict, Type, List, cast


@dataclass
class MatchType:
    """
    The base type for entity resolution operators.

    :ivar targetColumns: A list of column names that are the target for matching. If
        None, all columns are used for entity resolution.
    :type targetColumns: Optional[List[str]]
    """
    targetColumns: Optional[List[str]] = None

@dataclass
class ExactMatch(MatchType):
    """
    Use this match type to evaluate and configure specific exact matching criteria
    for the data values.

    :ivar minVariation: Minimum allowable variation in the field to check for matches
                        (defaults to 0.0).
    :type minVariation: Optional[float]
    :ivar minDistinct: Minimum percentage of distinct values in the field to check for matches
                       (defaults to 0.0).
    :type minDistinct: Optional[float]
    """
    minVariation: Optional[float] = None
    minDistinct: Optional[float] = None


@dataclass
class GeoMatch(MatchType):
    """
    use this match type to check for matches in fields that represent geographical
    attributes.

    :ivar distance: The maximum distance value for the geographical match (defaults to 2.0)
    :type distance: Optional[float]
    :ivar distanceUnit: The unit of measurement for the distance, such as
        kilometers or miles (defaults to 'kilometers').
    :type distanceUnit: Optional[str]
    """
    distance: Optional[float] = None
    distanceUnit: Optional[str] = None

class EntityResolutionTypes(StrEnum):
    """
    Enumerates the various resolution strategies for handling
    matching or reconciliation of entity data. Each enumeration value
    specifies a particular method or approach used for determining
    entity equivalence or correspondence.

    :cvar ExactMatch: Used when entities are determined to be equivalent
        based on exact value matches without any approximation.
    :cvar GeoMatch: Used when entities are matched based on their
        geographical location or proximity.
    """
    ExactMatch = "ExactMatch"
    GeoMatch = "GeoMatch"

# sanity check
for match_type in EntityResolutionTypes:
    class_name = match_type
    if class_name not in globals() or not isinstance(globals()[class_name], type):
        raise TypeError(f"Mismatch: {class_name} does not correspond to a valid class.")

class MatchTypeConfig:
    """
    Encapsulates configuration related to different types of entity resolution matches.

    This class is designed to store, manage, and provide access to various entity resolution
    match type configurations, such as ExactMatch and GeoMatch. It maintains internal
    state for these match types and also provides access to a consolidated configuration
    in dictionary format.

    :ivar matchTypes: A dictionary mapping entity resolution types to their respective match
        configurations (e.g., ExactMatch, GeoMatch).
    :type matchTypes: dict[EntityResolutionTypes, Optional[MatchType]]
    """
    def __init__(self, exact_match: Optional[ExactMatch] = None, geo_match: Optional[GeoMatch] = None):
        self.matchTypes: dict[EntityResolutionTypes, Optional[MatchType]] = {
            EntityResolutionTypes.ExactMatch: exact_match,
            EntityResolutionTypes.GeoMatch: geo_match,
        }

    @property
    def config(self) -> Optional[Dict[str, Dict]]:
        cfg = {}
        for match_type, match_obj in self.matchTypes.items():
            if match_obj is not None:
                cfg[match_type.value] = asdict(match_obj)
        return cfg if cfg else None


# Quick Test
if __name__ == "__main__":
    exact = ExactMatch(minVariation=0.15, minDistinct=0.25)
    geo = GeoMatch(distance=20, distanceUnit="km")
    geo2 = GeoMatch()

    exact_target = ExactMatch(targetColumns=["col1"])

    config = MatchTypeConfig(exact_match=exact, geo_match=geo)
    print(config.config)

    config = MatchTypeConfig(exact_match=exact)
    print(config.config)

    config = MatchTypeConfig(exact_match=exact_target)
    print(config.config)

    config = MatchTypeConfig(geo_match=geo2)
    print(config.config)

    config = MatchTypeConfig()
    print(config.config)
