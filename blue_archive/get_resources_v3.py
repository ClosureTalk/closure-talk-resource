import glob
from pathlib import Path
import shutil
from typing import Dict, List, Tuple

from omegaconf import OmegaConf

from blue_archive.common import (
    CharLangData,
    GroupData,
    GroupLangData,
    SimpleCharData,
    all_langs,
    name_to_id,
)
from utils.models import Character, FilterGroup
from utils.resource_utils import ResourceProcessor

script_dir = Path(__file__).parent


def get_default_lang_data(data: SimpleCharData) -> CharLangData:
    if len(data.family_name) > 0:
        jp_name = f"{data.family_name} {data.personal_name}"
        if len(data.personal_name_ruby) > 0:
            en_name = f"{name_to_id(data.family_name_ruby)} {name_to_id(data.personal_name_ruby)}"
        else:
            en_name = f"{name_to_id(data.family_name_ruby)} {data.id}"
    else:
        jp_name = data.personal_name
        en_name = " ".join([s[0].upper() + s[1:] for s in data.id.split("_") if s != "npc"])

    return OmegaConf.structured(CharLangData(
        data.id,
        {
            "ja": jp_name,
            "en": en_name,
            "ko": "",
            "zh-cn": "",
            "zh-tw": "",
        },
    ))


class BlueArchiveResourceProcessor(ResourceProcessor):
    def __init__(self) -> None:
        super().__init__("ba")

    def get_chars(self) -> Tuple[List[Character], Dict[str, Path]]:
        res_root = self.res_root / "assets"
        chars_res_root = res_root / "UIs/01_Common/01_Character"
        unused_char_files = set([f.stem for f in chars_res_root.glob("*.png") if not f.stem.strip().endswith("_Small")])
        unused_char_files.remove("Student_Portrait_Serika_Shibasek")

        chars: dict[str, SimpleCharData] = OmegaConf.load(script_dir / "data/chars.yaml")

        club_data: list[GroupData] = OmegaConf.load(script_dir / "data/clubs.yaml")
        school_data: list[GroupData] = OmegaConf.load(script_dir / "data/schools.yaml")
        group_data = club_data + school_data

        with open(script_dir / "lang/char.yaml", "r", encoding="utf-8") as f:
            translations: dict[str, CharLangData] = {t.id: t for t in OmegaConf.load(f)}

        result: list[Character] = []
        avatar_files = {}
        image_config = {}
        updated_translations = False
        chars_without_school: list[Character] = []
        chars_without_club: list[Character] = []

        for cid, data in chars.items():
            trans = translations.get(cid)
            if trans is None:
                print(f"New translation: {cid}")
                trans = translations[cid] = get_default_lang_data(data)
                updated_translations = True

            # Get short_name by splitting full name, unless manually translated
            short_name = dict(trans.short_name) if "short_name" in trans and trans.short_name is not None else {}
            for lang in all_langs:
                if lang not in short_name or len(short_name[lang]) == 0:
                    short_name[lang] = trans.name[lang].split(" ")[-1]

            char = Character(
                cid,
                translations[cid].name,
                short_name,
                [],
                sorted([gp.id for gp in group_data if cid in gp.members]),
            )

            # Get avatar files
            for img in data.image_files:
                if ":" in img:
                    name, img = img.split(":")
                else:
                    name = img.split("/")[-1]
                    name = name[name.index("Portrait_")+len("Portrait_"):]

                assert len(name) > 0
                assert name not in avatar_files, f"Duplicate: {name}"

                img_file = res_root / f"{img}.png"
                assert img_file.exists(), str(img_file)

                char.images.append(name)
                avatar_files[name] = img_file

                if img_file.stem in unused_char_files:
                    unused_char_files.remove(img_file.stem)

            char.images = sorted(char.images)
            result.append(char)
            if len([gp for gp in school_data if cid in gp.members]) == 0:
                chars_without_school.append(char)
            if len([gp for gp in club_data if cid in gp.members]) == 0:
                chars_without_club.append(char)

        if updated_translations:
            with open(script_dir / "lang/char.yaml", "w", encoding="utf-8") as f:
                f.write(OmegaConf.to_yaml(
                    sorted(translations.values(), key=lambda x: x.id.lower()), sort_keys=True))

        if len(unused_char_files) > 0:
            print("Unused char files:")
            for file in sorted(unused_char_files):
                print(f"  {file}")
                if len(unused_char_files) < 50:
                    src = chars_res_root / f"{file}.png"
                    dst = script_dir.parent / f"scripts/ba_unused/{file}.png"
                    dst.parent.mkdir(exist_ok=True)
                    if not dst.exists():
                        shutil.copy2(src, dst)

        result = sorted(result, key=lambda ch: ch.id.lower())
        return result, avatar_files, image_config

    def get_stamps(self) -> List[str]:
        in_root = self.res_root / "assets/UIs/01_Common/31_ClanEmoji"
        files = list(glob.glob(str(in_root / "*_Jp.png")))
        # ClanChat_Emoji_100_Jp
        return sorted(files, key=lambda s: int(s.split("/")[-1].split("_")[2]))

    def get_filters(self) -> List[FilterGroup]:
        result = []
        type_names = OmegaConf.to_container(OmegaConf.load(script_dir / "lang/group_types.yaml"))
        for key in ["schools", "clubs"]:
            groups: list[GroupLangData] = OmegaConf.load(script_dir / f"lang/{key}.yaml")
            groups = sorted(groups, key=lambda gp: gp.id)
            for gp in groups:
                gp.name = OmegaConf.to_container(gp.name)
                gp.name = {k: gp.name[k] or "" for k in all_langs}
            result.append(FilterGroup(
                key,
                type_names[key],
                [gp.id for gp in groups],
                [gp.name for gp in groups],
                [False] * len(groups),
            ))

        return result


if __name__ == "__main__":
    BlueArchiveResourceProcessor().main()
