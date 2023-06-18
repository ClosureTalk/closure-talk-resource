from pathlib import Path

from omegaconf import OmegaConf

from blue_archive.common import CharLangData, all_langs
from utils.json_utils import read_json
from utils.models import Character


def main():
    script_dir = Path(__file__).parent
    chars: list[Character] = [Character.from_dict(d) for d in read_json(script_dir / "char.json")]

    result = [
        OmegaConf.structured(CharLangData(
            char.id,
            {k: char.names.get(k, "") for k in all_langs},
            {k: char.short_names.get(k, "") for k in all_langs},
        ))
        for char in chars
    ]
    result = sorted(result, key=lambda x: x.id)

    with open(script_dir.parent / "lang/char.yaml", "w", encoding="utf-8") as f:
        f.write(OmegaConf.to_yaml(result, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
