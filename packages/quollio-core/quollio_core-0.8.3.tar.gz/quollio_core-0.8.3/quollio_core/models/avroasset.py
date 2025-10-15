from dataclasses import dataclass
from typing import List, Optional

from dataclasses_avroschema import AvroModel


@dataclass
class AvroAsset(AvroModel):
    "AvroAsset"

    id: str
    object_type: str
    parents: List[str]
    name: str
    stats_max: Optional[str] = None
    stats_min: Optional[str] = None
    stats_mean: Optional[str] = None
    stats_median: Optional[str] = None
    stats_mode: Optional[str] = None
    stats_stddev: Optional[str] = None
    stats_number_of_null: Optional[str] = None
    stats_number_of_unique: Optional[str] = None
    upstream: Optional[List[str]] = None
