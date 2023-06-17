import itertools
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

from blue_archive.common import (CharData, LocalizeCharProfile,
                                 ScenarioCharacterName, load_excel_table_list,
                                 name_to_id)
from utils.json_utils import read_json, write_list


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

    id_mappings = read_json(script_dir / "data/id_mapping.json", None)

    def get_id(prof: LocalizeCharProfile):
        cid = name_to_id(prof.PersonalNameJp)
        return id_mappings.get(cid, cid)

    # For every profile, gather images
    used_images = set()
    image_users = {}
    result = []
    result_map: dict[str, CharData] = {}
    for prof in profiles:
        key = prof.FamilyNameJp + prof.PersonalNameJp
        if len(key) == 0:
            continue
        if prof.PersonalNameJp not in portrait_images:
            print(f"Profile without portrait: {key}")
            continue

        images = portrait_images[prof.PersonalNameJp] - used_images
        if len(images) == 0:
            print(f"Profile without new image: {key}")
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
                get_id(prof),
                prof.CharacterId,
                prof.FamilyNameJp,
                prof.FamilyNameRubyJp,
                prof.PersonalNameJp,
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
    for name in names_without_profile:
        images = images_without_profile[name]
        for img in images:
            if img in image_users:
                aka = result_map[image_users[img]].aka
                if name not in aka:
                    aka.append(name)

        images -= used_images
        if len(images) == 0:
            continue

        if name in result_map:
            char = result_map[name]
        else:
            print(f"Additional char: {name}")
            char = CharData(
                "",
                -1,
                "",
                "",
                name,
                [],
                [],
            )
            result.append(char)
            result_map[name] = char

        char.image_files = sorted(list(set(char.image_files) | images))
        used_images |= images
        for img in char.image_files:
            image_users[img] = name

    write_list(CharData, script_dir / "data/char_data.json", result)


if __name__ == "__main__":
    main()
