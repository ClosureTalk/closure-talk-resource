import glob
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from utils.json_utils import read_json
from utils.models import Character, FilterGroup
from utils.resource_utils import ResourceProcessor
from utils.web_utils import download_json

use_local_tables = False


class ArknightsResourceProcessor(ResourceProcessor):
    def __init__(self) -> None:
        super().__init__("ak")

    def get_chars(self) -> Tuple[List[Character], Dict[str, Path]]:
        res_root = self.res_root

        # download data
        langs = ["zh-cn", "ja", "en", "zh-tw"]
        lang_keys = {
            "zh-cn": "zh_CN",
            "ja": "ja_JP",
            "en": "en_US",
            "zh-tw": "zh_TW",
        }
        res_keys = {
            "zh-cn": "cn",
            "ja": "jp",
            "en": "us",
            "zh-tw": "tw",
        }
        char_tables = {}
        enemy_tables = {}
        for lang in langs:
            for tables, name in [
                [char_tables, "character_table.json"],
                [enemy_tables, "enemy_handbook_table.json"],
            ]:
                # Skip until supported by data provider
                if lang == "zh-tw":
                    tables[lang] = {}
                    continue

                local_file = res_root / f"{res_keys[lang]}/assets/gamedata/excel/{name}"
                if use_local_tables and os.path.isfile(local_file):
                    logging.info(f"Read {lang} table {name}")
                    tables[lang] = read_json(local_file, None)
                else:
                    logging.info(f"Download {lang} table {name}")
                    url = f"https://github.com/Kengxxiao/ArknightsGameData/blob/master/{lang_keys[lang]}/gamedata/excel/{name}?raw=true"
                    tables[lang] = download_json(url)

        # get all avatars from cn
        res_root = res_root / "cn/assets"

        # add characters with avatars
        characters = []
        avatar_files = {}
        appellations = defaultdict(str)
        ch_types = set()

        for k, v in sorted(char_tables["zh-cn"].items(), key=lambda pair: pair[0]):
            name = v["name"]
            basic_sprite = res_root / f"spritepack/ui_char_avatar_h1_0/{k}.png"
            if not os.path.isfile(basic_sprite):
                logging.warning(f"Skip: {k} {name}")
                continue

            avatar_files[k] = basic_sprite
            ch_type = k.split("_")[0]
            ch_types.add(ch_type)
            ch = Character(k, {"zh-cn": name}, {"zh-cn": name}, [k], [v["appellation"], f":#type-{ch_type}"])
            appellations[ch.id] = v["appellation"]

            # E2 and skins
            additional = glob.glob(str(res_root / f"spritepack/ui_char_avatar_h1_elite_0/{k}*.png")) + \
                glob.glob(str(res_root / f"spritepack/ui_char_avatar_h1_skins_0/{k}*.png"))
            for file in additional:
                img_name = os.path.splitext(os.path.split(file)[1])[0]
                avatar_files[img_name] = file
                ch.images.append(img_name)

            characters.append(ch)

        logging.info(f"All ch types: {ch_types}")

        for k, v in sorted(enemy_tables["zh-cn"].items(), key=lambda pair: pair[0]):
            name = v["name"]
            if name == "-":
                continue

            basic_sprite = res_root / f"spritepack/icon_enemies_h2_0/{k}.png"
            if not os.path.isfile(basic_sprite):
                logging.warning(f"Skip: {k} {name}")
                continue

            avatar_files[k] = basic_sprite
            characters.append(Character(k, {"zh-cn": name}, {"zh-cn": name}, [k], [":#type-enemy"]))

        # add other languages
        all_tables = char_tables
        for lang in langs:
            all_tables[lang].update(enemy_tables[lang])
        del char_tables, enemy_tables

        for lang in langs[1:]:
            tbl = all_tables[lang]
            for ch in characters:
                name = tbl[ch.id]["name"] if ch.id in tbl else ""
                if name == "" and (lang == "en" or lang == "ja"):
                    name = appellations[ch.id]
                ch.names[lang] = ch.short_names[lang] = name

        # Closure Talk must have Closure
        closure_id = "char_007_closre"
        if closure_id not in avatar_files:
            closure_name = {
                "zh-cn": "可露希尔",
                "zh-tw": "可露希爾",
                "ja": "クロージャ",
                "en": "Closure",
            }
            characters = [Character(
                closure_id,
                closure_name,
                {**closure_name},
                [closure_id],
                []
            )] + characters
            avatar_files[closure_id] = res_root / f"spritepack/ui_char_avatar_h1_0/{closure_id}_1.png"

        return characters, avatar_files

    def get_stamps(self) -> List[str]:
        return []

    def get_filters(self) -> List[FilterGroup]:
        type_filter = FilterGroup(
            "type",
            {
                "zh-cn": "类型",
                "zh-tw": "",
                "ja": "",
                "en": "Type",
            },
            [":#type-char", ":#type-token", ":#type-enemy"],
            [
                {
                    "zh-cn": "干员",
                    "zh-tw": "",
                    "ja": "",
                    "en": "Operator",
                },
                {
                    "zh-cn": "Token",
                    "zh-tw": "",
                    "ja": "",
                    "en": "Token",
                },
                {
                    "zh-cn": "敌方",
                    "zh-tw": "",
                    "ja": "",
                    "en": "Enemy",
                },
            ],
            [True, False, False],
        )
        return [type_filter]


if __name__ == "__main__":
    ArknightsResourceProcessor().main()
