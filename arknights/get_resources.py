import glob
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from omegaconf import OmegaConf

from utils.json_utils import read_json
from utils.models import Character, FilterGroup
from utils.resource_utils import ResourceProcessor
from utils.web_utils import download_json

use_local_tables = False
script_dir = Path(__file__).parent
github_repo_cn = "Kengxxiao/ArknightsGameData"
github_repo_intl = "Kengxxiao/ArknightsGameData_YoStar"

langs = ["zh-cn", "ja", "en", "ko", "zh-tw"]
lang_keys = {
    "zh-cn": "zh_CN",
    "ja": "ja_JP",
    "en": "en_US",
    "zh-tw": "zh_TW",
    "ko": "ko_KR",
}
res_keys = {
    "zh-cn": "cn",
    "ja": "jp",
    "en": "us",
    "zh-tw": "tw",
    "ko": "ko",
}


def get_github_versions() -> dict[str, str]:
    update_res_keys = {
        "CN": "cn",
        "JP": "jp",
        "KR": "ko",
        "EN": "us",
    }
    result = {}
    commits = (
        requests.get(f"https://api.github.com/repos/{github_repo_intl}/commits").json() +
        requests.get(f"https://api.github.com/repos/{github_repo_cn}/commits").json()
    )
    for commit in commits:
        msg = commit["commit"]["message"]
        for key, lang in update_res_keys.items():
            if lang in result:
                continue
            if not msg.startswith(f"[{key} UPDATE]"):
                continue

            result[lang] = msg[msg.index("Data:")+5:]

        if len(result) == len(update_res_keys):
            break

    result = {f"ak-{k}": v for k, v in result.items()}
    return result


class ArknightsResourceProcessor(ResourceProcessor):
    def __init__(self) -> None:
        super().__init__("ak")
        self.github_res_vers = get_github_versions()
        print(self.github_res_vers)

    def get_chars(self) -> Tuple[List[Character], Dict[str, Path]]:
        res_root = self.res_root

        # download data
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
                    table = read_json(local_file, None)
                else:
                    logging.info(f"Download {lang} table {name}")
                    github_repo = github_repo_cn if lang == "zh-cn" else github_repo_intl
                    github_branch = "master" if lang == "zh-cn" else "main"
                    url = f"https://github.com/{github_repo}/blob/{github_branch}/{lang_keys[lang]}/gamedata/excel/{name}?raw=true"
                    table = download_json(url)

                if "enemyData" in table:
                    table = table["enemyData"]
                tables[lang] = table

        # get all avatars from cn
        res_root = res_root / "cn/assets"

        # add characters with avatars
        characters = []
        avatar_files = {}
        appellations = defaultdict(str)
        ch_types = set()

        sprite_folders = sorted(res_root.glob("spritepack/ui_char_avatar_*"))
        sprite_files: list[Path] = []
        for folder in sprite_folders:
            sprite_files += sorted(folder.glob("*.png"))
        print(f"Found {len(sprite_files)} character sprite files")

        for k, v in sorted(char_tables["zh-cn"].items(), key=lambda pair: pair[0]):
            name = v["name"]

            basic_sprite = next(iter(f for f in sprite_files if f.stem == k), None)
            if basic_sprite is None:
                logging.warning(f"Skip: {k} {name}")
                continue

            avatar_files[k] = basic_sprite
            ch_type = k.split("_")[0]
            ch_types.add(ch_type)
            ch = Character(k, {"zh-cn": name}, {"zh-cn": name}, [k], [v["appellation"], f":#type-{ch_type}"])
            appellations[ch.id] = v["appellation"]

            # E2 and skins
            used_files = set()
            for file in (f for f in sprite_files if f.stem.startswith(k) and f.stem != k):
                if file.stem in used_files:
                    continue
                used_files.add(file.stem)
                img_name = os.path.splitext(os.path.split(file)[1])[0]
                avatar_files[img_name] = file
                ch.images.append(img_name)

            characters.append(ch)

        logging.info(f"All ch types: {ch_types}")

        sprite_folders = sorted(res_root.glob("spritepack/icon_enemies_*"))
        sprite_files: list[Path] = []
        for folder in sprite_folders:
            sprite_files += sorted(folder.glob("*.png"))
        print(f"Found {len(sprite_files)} enemy sprite files")

        for k, v in sorted(enemy_tables["zh-cn"].items(), key=lambda pair: pair[0]):
            name = v["name"]
            if name == "-":
                continue

            basic_sprite = next(iter(f for f in sprite_files if f.stem == k), None)
            if basic_sprite is None:
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
                "ko": "클로저",
            }
            characters = [Character(
                closure_id,
                closure_name,
                {**closure_name},
                [closure_id],
                []
            )] + characters
            avatar_files[closure_id] = res_root / f"spritepack/ui_char_avatar_h1_0/{closure_id}_1.png"

        return characters, avatar_files, {}

    def get_stamps(self) -> List[str]:
        return []

    def get_filters(self) -> List[FilterGroup]:
        translations = OmegaConf.to_container(OmegaConf.load(script_dir / "lang/filters.yaml"))
        type_filter = FilterGroup(
            "type",
            translations["type"],
            [":#type-char", ":#type-enemy", ":#type-token"],
            [
                translations[k] for k in ["operator", "enemy", "token"]
            ],
            [True, False, False],
        )
        return [type_filter]

    def _get_versions(self) -> Dict[str, str]:
        versions = super()._get_versions() if use_local_tables else {}
        versions.update(self.github_res_vers)
        return versions


if __name__ == "__main__":
    ArknightsResourceProcessor().main()
