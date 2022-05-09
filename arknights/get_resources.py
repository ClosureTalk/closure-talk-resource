import glob
import logging
import os
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from utils.models import Character
from utils.resource_utils import ResourceProcessor
from utils.web_utils import download_json


class ArknightsResourceProcessor(ResourceProcessor):
    def __init__(self) -> None:
        super().__init__("ak")
        self.res_root = Path(self.args.resources)

    def configure_parser(self, parser: ArgumentParser) -> ArgumentParser:
        parser.add_argument("--resources", default="G:\\Games\\AknResources\\cn\\assets")
        return parser

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
        char_tables = {}
        enemy_tables = {}
        for lang in langs:
            logging.info(f"Download {lang} tables")
            path = f"https://github.com/Kengxxiao/ArknightsGameData/blob/master/{lang_keys[lang]}/gamedata/excel"
            char_tables[lang] = download_json(f"{path}/character_table.json?raw=true")
            enemy_tables[lang] = download_json(f"{path}/enemy_handbook_table.json?raw=true")

        # add characters with avatars
        characters = []
        avatar_files = {}
        appellations = defaultdict(str)

        for k, v in sorted(char_tables["zh-cn"].items(), key=lambda pair: pair[0]):
            name = v["name"]
            basic_sprite = res_root / f"spritepack/ui_char_avatar_h1_0/Sprite/{k}.png"
            if not os.path.isfile(basic_sprite):
                logging.warning(f"Skip: {k} {name}")
                continue

            avatar_files[k] = basic_sprite
            ch = Character(k, { "zh-cn": name }, { "zh-cn": name }, [k], [v["appellation"]])
            appellations[ch.id] = v["appellation"]

            # E2 and skins
            additional = glob.glob(str(res_root / f"spritepack/ui_char_avatar_h1_elite_0/Sprite/{k}*.png")) + \
                glob.glob(str(res_root / f"spritepack/ui_char_avatar_h1_skins_0/Sprite/{k}*.png"))
            for file in additional:
                img_name = os.path.splitext(os.path.split(file)[1])[0]
                avatar_files[img_name] = file
                ch.images.append(img_name)

            characters.append(ch)

        for k, v in sorted(enemy_tables["zh-cn"].items(), key=lambda pair: pair[0]):
            name = v["name"]
            if name == "-":
                continue

            basic_sprite = res_root / f"spritepack/icon_enemies_h2_0/Sprite/{k}.png"
            if not os.path.isfile(basic_sprite):
                logging.warning(f"Skip: {k} {name}")
                continue

            avatar_files[k] = basic_sprite
            characters.append(Character(k, { "zh-cn": name }, { "zh-cn": name }, [k], []))

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
            avatar_files[closure_id] = res_root / f"spritepack/ui_char_avatar_h1_0/Sprite/{closure_id}_1.png"

        return characters, avatar_files

    def get_stamps(self) -> List[str]:
        return []

if __name__ == "__main__":
    ArknightsResourceProcessor().main()
