import json
from dataclasses import dataclass, field
from typing import Callable, Optional, TypeVar

import romkan
from dataclasses_json import Undefined, dataclass_json

T = TypeVar("T")

all_langs = [
    "en",
    "ja",
    "zh-cn",
    "zh-tw",
]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LocalizeCharProfile:
    CharacterId: int
    FamilyNameJp: str
    FamilyNameRubyJp: str
    PersonalNameJp: str
    IdOverride: str = field(default="")


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ScenarioCharacterName:
    NameJP: str
    SmallPortrait: str


@dataclass_json
@dataclass
class CharData:
    id: str
    char_id: int
    family_name: str
    family_name_ruby: str
    personal_name: str
    image_files: list[str]
    aka: list[str]


@dataclass
class ManualProfile:
    family_name: str
    family_name_ruby: str
    personal_name: str


@dataclass
class ManualPortrait:
    name: str
    images: list[str]
    id: str


@dataclass
class CharLangData:
    id: str
    name: dict[str, str]
    short_name: Optional[dict[str, str]] = field(default=None)


@dataclass
class GroupLangData:
    id: str
    name: dict[str, str]


@dataclass
class GroupData:
    id: str
    members: list[str]


def load_excel_table_list(cls: Callable[[], T], file: str) -> list[T]:
    with open(file, "r", encoding="utf-8-sig") as f:
        data = json.load(f)["DataList"]

    return [cls.from_dict(d) for d in data]


def name_to_id(name: str) -> str:
    roma = romkan.to_roma(name)
    return roma[0].upper() + roma[1:]
