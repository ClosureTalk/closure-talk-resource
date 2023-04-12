import json
from pathlib import Path

from blue_archive.common import (LocalizeCharProfile, load_excel_table_list,
                                 name_to_id)
from utils.json_utils import write_json
from utils.models import Character


def main():
    script_dir = Path(__file__).parent
    data_dir = script_dir / "../../../../../Data/Astgenne/ba/table/json"
    profiles = load_excel_table_list(
        LocalizeCharProfile,
        data_dir / "LocalizeCharProfileExcelTable.json",
    )

    with open(script_dir / "../../../closuretalk.github.io/resources/ba/char.json", "r", encoding="utf-8") as f:
        # for some reason this line doesn't work
        # chars: list[Character] = Character.schema().load(f, many=True)
        # so, we load one by one
        data = json.load(f)
    chars: list[Character] = [Character.from_dict(d) for d in data]

    existing_ids = {
        c.short_names["ja"]: c.id for c in chars
    }
    mappings = {}
    for prof in profiles:
        name = prof.PersonalNameJp
        if name == "":
            continue
        if name not in existing_ids:
            print(f"No existing id: {name}")
            continue

        inferred_id = name_to_id(name)
        existing_id = existing_ids[name]
        if existing_id != inferred_id:
            print(f"Map {name}: {inferred_id} -> {existing_id}")
            mappings[inferred_id] = existing_id

    write_json(script_dir / "../data/id_mapping.json", mappings)


if __name__ == "__main__":
    main()
