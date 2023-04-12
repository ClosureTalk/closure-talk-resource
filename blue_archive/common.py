import json
from dataclasses import dataclass
from typing import Callable, TypeVar

import romkan
from dataclasses_json import Undefined, dataclass_json

T = TypeVar("T")


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LocalizeCharProfile:
    CharacterId: int
    FamilyNameJp: str
    FamilyNameRubyJp: str
    PersonalNameJp: str


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


def load_excel_table_list(cls: Callable[[], T], file: str) -> list[T]:
    with open(file, "r", encoding="utf-8-sig") as f:
        data = json.load(f)["DataList"]

    return [cls.from_dict(d) for d in data]


def name_to_id(name: str) -> str:
    roma = romkan.to_roma(name)
    return roma[0].upper() + roma[1:]
