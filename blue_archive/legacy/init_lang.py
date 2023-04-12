import json
from pathlib import Path

from utils.json_utils import write_json
from utils.models import Character


def main():
    script_dir = Path(__file__).parent
    with open(script_dir / "../../../closuretalk.github.io/resources/ba/char.json", "r", encoding="utf-8") as f:
        # for some reason this line doesn't work
        # chars: list[Character] = Character.schema().load(f, many=True)
        # so, we load one by one
        data = json.load(f)
    chars: list[Character] = [Character.from_dict(d) for d in data]

    data = {
        "en": {},
        "zh-tw": {},
    }
    for char in chars:
        for lang in data:
            data[lang][char.id] = {
                "name": char.names[lang],
                "short_name": char.short_names[lang],
            }

    for lang, value in data.items():
        write_json(script_dir / f"../lang/{lang}.json", value)


if __name__ == "__main__":
    main()
