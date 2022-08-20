import glob
import logging
import os
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, List, Tuple

from utils.json_utils import read_json, write_json
from utils.models import Character, FilterGroup
from utils.resource_utils import ResourceProcessor
from utils.web_utils import download_json

lang_mappings = {
    "ja": "ja",
    "en": "en",
    "zh-hant": "zh-tw",
    "zh-hans": "zh-cn",
}


class BlueArchiveResourceProcessor(ResourceProcessor):
    def __init__(self) -> None:
        super().__init__("ba")
        self.res_root = Path(self.args.resources) / "Assets/_MX/AddressableAsset/UIs/01_Common"

    def configure_parser(self, parser: ArgumentParser) -> ArgumentParser:
        parser.add_argument("resources", help="Path to BuruakaResources assets folder")
        return parser

    def get_chars(self) -> Tuple[List[Character], Dict[str, Path]]:
        res_root = self.res_root
        script_dir = Path(os.path.split(__file__)[0])

        data = download_json("https://raw.githubusercontent.com/YuzuTalk/translation/main/json/characters.json")
        data = sorted(data, key=lambda ch: ch["name"]["first_name"]["en"])

        # add characters if at least one image is found
        characters = []
        avatar_files = {}
        img_mappings_file = script_dir / "img_mappings.json"
        img_mappings = read_json(img_mappings_file, dict)
        has_update = False

        for ch in data:
            key = ch["id"]
            names = ch["name"]

            char = Character(
                key,
                {mapped: " ".join([names["last_name"][k], names["first_name"][k]]).strip() for k, mapped in lang_mappings.items()},
                {mapped: names["first_name"][k] for k, mapped in lang_mappings.items()},
                [],
                [ch["school"], *ch["club"]],
            )

            for img in ch["img"]:
                choices = [
                    f"NPC_Portrait_{img}.png",
                    f"NPC_Portrait_{img}1.png",
                    f"Student_Portrait_{img}.png",
                    f"Student_Portrait_{img}_Small.png",
                ]
                if img in img_mappings and len(img_mappings[img]) > 0:
                    choices += [img_mappings[img] + ".png"]
                found = False
                for choice in choices:
                    img_file = res_root / "01_Character" / choice
                    if os.path.isfile(img_file):
                        avatar_files[img] = img_file
                        char.images.append(img)
                        found = True
                        break

                if not found and (img not in img_mappings or len(img_mappings[img]) > 0):
                    img_mappings[img] = ""
                    has_update = True

            if len(char.images) > 0:
                characters.append(char)
            else:
                logging.warning(f"Skip: {key} {char.names['ja']}")

        if has_update:
            write_json(img_mappings_file, img_mappings)

        # overrides
        for lang in ["zh-cn"]:
            res_file = script_dir / f"lang/{lang}.json"
            res_data = read_json(res_file, dict)
            has_update = False
            for ch in characters:
                if ch.id not in res_data:
                    res_data[ch.id] = {"name": "", "short_name": ""}
                    has_update = True
                if len(res_data[ch.id]["name"]) > 0:
                    ch.names[lang] = res_data[ch.id]["name"]
                if len(res_data[ch.id]["short_name"]) > 0:
                    ch.short_names[lang] = res_data[ch.id]["short_name"]
            if has_update:
                write_json(res_file, res_data)

        return characters, avatar_files

    def get_stamps(self) -> List[str]:
        in_root = self.res_root / "31_ClanEmoji"
        return sorted(glob.glob(str(in_root / "*_Jp.png")))

    def get_filters(self) -> List[FilterGroup]:
        def make_group(key, names, data: Dict[str, Dict[str, str]]):
            data_keys = sorted(list(data.keys()))
            return FilterGroup(
                key,
                names,
                data_keys,
                [
                    {
                        lang_mappings[k]: v for k, v in data[data_key].items() if k in lang_mappings
                    }
                    for data_key in data_keys
                ],
                [False] * len(data_keys)
            )

        schools = download_json("https://raw.githubusercontent.com/YuzuTalk/translation/main/json/schools.json")
        clubs = download_json("https://raw.githubusercontent.com/YuzuTalk/translation/main/json/clubs.json")

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
