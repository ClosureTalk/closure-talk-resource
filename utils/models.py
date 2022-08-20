from dataclasses import dataclass
from typing import Dict, List

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Character:
    id: str
    names: Dict[str, str]
    short_names: Dict[str, str]
    images: List[str]
    searches: List[str]


@dataclass_json
@dataclass
class FilterGroup:
    group_key: str
    group_name: Dict[str, str]
    filter_searches: List[str]
    filter_names: List[Dict[str, str]]
    active: List[bool]
