import itertools
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

from omegaconf import OmegaConf

from blue_archive.common import (CharData, LocalizeCharProfile, ManualPortrait,
                                 ManualProfile, ScenarioCharacterName,
                                 load_excel_table_list, name_to_id)
from utils.json_utils import read_json, write_list


def add_manual_data(profiles: list[LocalizeCharProfile], portrait_images: defaultdict[str, set[str]]):
    root = Path(__file__).parent / "manual"
    manual_profiles: list[ManualProfile] = OmegaConf.load(root / "profiles.yaml")
    for prof in manual_profiles:
        assert prof.personal_name is not None and len(prof.personal_name) > 0
        profiles.append(LocalizeCharProfile(
            -1,
            prof.family_name or "",
            prof.family_name_ruby or "",
            prof.personal_name,
        ))

    profile_names = set((prof.PersonalNameJp for prof in profiles))

    manual_portraits: list[ManualPortrait] = OmegaConf.load(root / "portraits.yaml")
    for portrait in manual_portraits:
        name = portrait.name

        if name not in profile_names:
            assert hasattr(portrait, "id") and len(portrait.id) > 0, f"Need id for {name}"
            profile_names.add(name)
            profiles.append(LocalizeCharProfile(
                -1,
                "",
                "",
                name,
                "",
                "",
                portrait.id,
            ))

        images = portrait_images[portrait.name]
        for img in portrait.images:
            if "/" not in img:
                img = f"UIs/01_Common/01_Character/{img}"
            images.add(img)


def generate_manual_data(result: list[CharData]):
    root = Path(__file__).parent / "manual"
    manual_profiles = []
    manual_portraits = []

    # students have katakana names
    # (also handles things like プレジデント)
    def is_student_name(s: str):
        return all((0x30A0 <= ord(c) <= 0x30FF for c in s))

    for char in result:
        if char.id != "$$$":
            continue

        is_student = char.image_files[0].startswith("Student_Portrait") or \
            is_student_name(char.personal_name)

        if is_student:
            manual_profiles.append(OmegaConf.structured(ManualProfile("", "", char.personal_name)))
        else:
            images = [f.split("/")[-1] if f.startswith("UIs/01_Common/01_Character") else f for f in char.image_files]
            manual_portraits.append(OmegaConf.structured(ManualPortrait("|".join([*char.aka, char.personal_name]), images, "")))

    with open(root / "profiles.generated.yaml", "w", encoding="utf-8") as f:
        f.write(OmegaConf.to_yaml(manual_profiles) + "\n")
    with open(root / "portraits.generated.yaml", "w", encoding="utf-8") as f:
        f.write(OmegaConf.to_yaml(manual_portraits) + "\n")


def main():
    script_dir = Path(__file__).parent
    parser = ArgumentParser()
    parser.add_argument(
        "-a", "--astgenne",
        default=(script_dir.parent.parent.parent.parent / "Data/Astgenne/ba")
    )
    args = parser.parse_args()
    res_root = Path(args.astgenne)
    json_dir = res_root / "table/json"

    profiles = load_excel_table_list(LocalizeCharProfile, json_dir / "LocalizeCharProfileExcelTable.json")
    scenario_names = load_excel_table_list(ScenarioCharacterName, json_dir / "ScenarioCharacterNameExcelTable.json")

    portrait_images = defaultdict(set)
    portrait_folder = res_root / "assets/UIs/01_Common/01_Character"
    portrait_files = set([f.stem for f in portrait_folder.glob("*.png")])
    for obj in scenario_names:
        if obj.SmallPortrait.endswith("NPC_Portrait_Null"):
            continue
        if not obj.SmallPortrait.split("/")[-1] in portrait_files:
            continue
        portrait_images[obj.NameJP].add(obj.SmallPortrait)
    add_manual_data(profiles, portrait_images)

    id_mappings = read_json(script_dir / "data/id_mapping.json", None)

    # For every profile, gather images
    used_images = set()
    image_users = {}
    result: list[CharData] = []
    result_map: dict[str, CharData] = {}
    for prof in profiles:
        key = prof.FamilyNameJp + prof.PersonalNameJp
        if len(key) == 0:
            continue

        if len(prof.IdOverride) > 0:
            cid = prof.IdOverride
        else:
            cid = name_to_id(prof.PersonalNameJp)
            cid = id_mappings.get(cid, cid)

        images = set()
        if prof.PersonalNameJp in portrait_images:
            images |= portrait_images[prof.PersonalNameJp]

        if f"Student_Portrait_{cid}" in portrait_files:
            images.add(f"UIs/01_Common/01_Character/Student_Portrait_{cid}")

        images -= used_images
        if len(images) == 0:
            if key not in result_map:
                print(f"Profile without image: {key}")
            continue

        all_heuristic_images = set()
        for img in images:
            img = img.split("/")[-1]
            if not img.startswith("Student_Portrait_") or \
                    img.startswith("Student_Portrait_CH") or \
                    len(img.split("_")) > 3:
                continue

            heuristic_images = set(
                [f"UIs/01_Common/01_Character/{f.stem}" for f in portrait_folder.glob(f"{img}_*") if not f.stem.endswith("_Small")]) - images - all_heuristic_images
            for himg in heuristic_images:
                print(f"Profile heuristics: {key} - {himg}")
            all_heuristic_images |= heuristic_images
        images |= all_heuristic_images

        if key in result_map:
            char = result_map[key]
        else:
            char = CharData(
                cid,
                prof.CharacterId,
                prof.FamilyNameJp,
                prof.FamilyNameRubyJp,
                prof.PersonalNameJp,
                prof.FamilyNameKr,
                prof.PersonalNameKr,
                [],
                [],
            )
            result.append(char)
            result_map[key] = char

        char.image_files = sorted(list(set(char.image_files) | images))
        used_images |= images
        for img in char.image_files:
            image_users[img] = key

    # Create profiles for images that have not been linked to a certain profile
    all_profiled_names = set((prof.PersonalNameJp for prof in profiles))
    used_images = set(itertools.chain(*(data.image_files for data in result)))

    images_without_profile = {
        k: v for k, v in portrait_images.items() if k not in all_profiled_names
    }

    names_without_profile = sorted(images_without_profile.keys())
    generated_chars = []
    for name in names_without_profile:
        images = images_without_profile[name]
        for img in images:
            if img in image_users:
                aka = result_map[image_users[img]].aka
                if name not in aka:
                    aka.append(name)

        images -= used_images
        for img in images:
            key = img.split("/")[-1]
            if key in result_map:
                char = result_map[key]
            else:
                char = CharData(
                    key,
                    -1,
                    "",
                    "",
                    key,
                    "",
                    "",
                    [img],
                    [],
                )
                result.append(char)
                result_map[key] = char
                image_users[img] = key
                generated_chars.append(char)

            char.aka.append(name)
        used_images |= images

    # Merge created profiles with single AKA, and assign name
    chars_to_merge: dict[str, list[CharData]] = defaultdict(list)
    for char in generated_chars:
        if len(char.aka) != 1:
            continue
        chars_to_merge[char.aka[0]].append(char)
    for key, chars in chars_to_merge.items():
        for char in chars:
            result = [c for c in result if c is not char]
            result_map.pop(char.id)
        char = CharData(
            chars[0].id,
            -1,
            "",
            "",
            chars[0].aka[0],
            "",
            "",
            list(set(itertools.chain(*(c.image_files for c in chars)))),
            [],
        )
        result.append(char)
        result_map[char.id] = char
        generated_chars.append(char)

    for char in generated_chars:
        char.id = "$$$"

    # Create profiles for unused images for completeness
    unused_portrait_files = sorted(portrait_files - set((Path(f).stem for f in used_images)))
    for file in unused_portrait_files:
        if file.endswith("_Small") or file.endswith("_Small "):
            continue

        print(f"Unused portrait file: {file}")
        char = CharData(
            "$$$",
            -1,
            "",
            "",
            file,
            "",
            "",
            [file],
            [],
        )
        result.append(char)
        result_map[file] = file

    result = sorted(result, key=lambda ch: ch.id.lower())
    write_list(CharData, script_dir / "data/char_data.json", result)

    # Generate suggested yaml template
    generate_manual_data(result)


if __name__ == "__main__":
    main()
