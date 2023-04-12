from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

from blue_archive.common import (CharData, LocalizeCharProfile,
                                 ScenarioCharacterName, load_excel_table_list, name_to_id)
from utils.json_utils import write_list, read_json


def main():
    script_dir = Path(__file__).parent
    parser = ArgumentParser()
    parser.add_argument(
        "-a", "--astgenne",
        default=(script_dir.parent.parent.parent.parent / "Data/Astgenne/ba")
    )
    args = parser.parse_args()
    json_dir = Path(args.astgenne) / "table/json"

    profiles = load_excel_table_list(LocalizeCharProfile, json_dir / "LocalizeCharProfileExcelTable.json")
    scenario_names = load_excel_table_list(ScenarioCharacterName, json_dir / "ScenarioCharacterNameExcelTable.json")

    portrait_images = defaultdict(set)
    for obj in scenario_names:
        if obj.SmallPortrait.endswith("NPC_Portrait_Null"):
            continue
        portrait_images[obj.NameJP].add(obj.SmallPortrait)

    id_mappings = read_json(script_dir / "data/id_mapping.json", None)

    def get_id(prof: LocalizeCharProfile):
        cid = name_to_id(prof.PersonalNameJp)
        return id_mappings.get(cid, cid)

    result = [
        CharData(
            get_id(prof),
            prof.CharacterId,
            prof.FamilyNameJp,
            prof.FamilyNameRubyJp,
            prof.PersonalNameJp,
            sorted(list(portrait_images[prof.PersonalNameJp])),
        )
        for prof in profiles
        if prof.PersonalNameJp in portrait_images
    ]

    all_profiled_names = set((prof.PersonalNameJp for prof in profiles))
    images_without_profiles = {
        k: v for k, v in portrait_images.items() if k not in all_profiled_names
    }
    # TODO handle these
    for k, v in images_without_profiles.items():
        print(k, v)

    write_list(CharData, script_dir / "data/char_data.json", result)


if __name__ == "__main__":
    main()
