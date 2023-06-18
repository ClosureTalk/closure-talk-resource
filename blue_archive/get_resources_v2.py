import glob
from pathlib import Path
from typing import Dict, List, Tuple

from omegaconf import OmegaConf

from blue_archive.common import CharData, CharLangData, name_to_id
from utils.json_utils import read_json
from utils.models import Character, FilterGroup
from utils.resource_utils import ResourceProcessor

script_dir = Path(__file__).parent


def get_legacy_image_mappings() -> dict[str, str]:
    mappings: dict[str, str] = read_json(script_dir / "legacy/img_mappings.json")
    return {
        v.split("/")[-1]: k for k, v in mappings.items() if len(v) > 0
    }


def get_default_lang_data(data: CharData) -> CharLangData:
    if len(data.family_name) > 0:
        jp_name = f"{data.family_name} {data.personal_name}"
        en_name = f"{name_to_id(data.family_name_ruby)} {data.id}"
        en_shortname = data.id
    else:
        jp_name = data.personal_name
        en_name = " ".join([s[0].upper() + s[1:] for s in data.id.split("_") if s != "npc"])
        en_shortname = en_name

    return OmegaConf.structured(CharLangData(
        data.id,
        {
            "jp": jp_name,
            "en": en_name,
            "zh-cn": "",
            "zh-tw": "",
        },
        {
            "jp": data.personal_name,
            "en": en_shortname,
            "zh-cn": "",
            "zh-tw": "",
        }
    ))


class BlueArchiveResourceProcessor(ResourceProcessor):
    def __init__(self) -> None:
        super().__init__("ba")

    def get_chars(self) -> Tuple[List[Character], Dict[str, Path]]:
        res_root = self.res_root / "assets"

        charData = read_json(script_dir / "data/char_data.json")
        charData: list[CharData] = [CharData.from_dict(d) for d in charData]

        with open(script_dir / "lang/char.yaml", "r", encoding="utf-8") as f:
            translations = OmegaConf.load(f)
            translations: dict[str, CharLangData] = {t.id: t for t in translations}

        with open(script_dir / "manual/excluded_portraits.txt", "r", encoding="utf-8") as f:
            excluded_portraits = set([l.strip() for l in f.readlines()])

        result = []
        avatar_files = {}
        image_mappings = get_legacy_image_mappings()
        updated_translations = False

        for data in charData:
            cid = data.id
            if cid not in translations:
                print(f"New translation: {cid}")
                translations[cid] = get_default_lang_data(data)
                updated_translations = True

            char = Character(
                data.id,
                translations[cid].name,
                translations[cid].short_name,
                [],
                [],
            )

            # Get avatar files
            for img in data.image_files:
                name = img.split("/")[-1]
                if name in excluded_portraits:
                    continue

                if name in image_mappings:
                    name = image_mappings[name]
                else:
                    name = name[name.index("Portrait_")+len("Portrait_"):]
                assert len(name) > 0
                assert name not in avatar_files, f"Duplicate: {name}"

                img_file = res_root / f"{img}.png"
                assert img_file.exists(), str(img_file)

                char.images.append(name)
                avatar_files[name] = img_file

            result.append(char)

        if updated_translations:
            with open(script_dir / "lang/char.yaml", "w", encoding="utf-8") as f:
                f.write(OmegaConf.to_yaml(
                    sorted(translations.values(), key=lambda x: x.id.lower()), sort_keys=True) + "\n")
        return result, avatar_files

    def get_stamps(self) -> List[str]:
        in_root = self.res_root / "assets/UIs/01_Common/31_ClanEmoji"
        return sorted(glob.glob(str(in_root / "*_Jp.png")))

    def get_filters(self) -> List[FilterGroup]:
        def make_group(key, names, data: Dict[str, Dict[str, str]]):
            data_keys = sorted(list(data.keys()))
            return FilterGroup(
                key,
                names,
                data_keys,
                [
                    data[key] for key in data_keys
                ],
                [False] * len(data_keys)
            )

        schools = read_json(script_dir / "data/schools.json")
        clubs = read_json(script_dir / "data/clubs.json")

        return [
            make_group(
                "schools",
                {
                    "zh-cn": "学校",
                    "ja": "学校",
                    "en": "School",
                    "zh-tw": "学校",
                },
                schools,
            ),
            make_group(
                "clubs",
                {
                    "zh-cn": "社团",
                    "ja": "クラブ",
                    "en": "Club",
                    "zh-tw": "社團",
                },
                clubs,
            ),
        ]


if __name__ == "__main__":
    BlueArchiveResourceProcessor().main()
