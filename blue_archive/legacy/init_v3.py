from pathlib import Path

from omegaconf import OmegaConf

from blue_archive.common import CharData
import json


def main():
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    chars: list[CharData] = CharData.schema().loads((data_dir / "char_data.json").read_text(), many=True)

    img_mappings: dict[str, str] = json.loads((script_dir / "img_mappings.json").read_text())
    img_mappings = {
        v.split("/")[-1]: k for k, v in img_mappings.items() if len(v) > 0
    }

    data = {
        ch.id: {
            "family_name": ch.family_name,
            "family_name_ruby": ch.family_name_ruby,
            "personal_name": ch.personal_name,
            "image_files": sorted([
                f"{img_mappings[Path(f).stem]}:{f}" if Path(f).stem in img_mappings else f for f in ch.image_files
            ]),
        }
        for ch in chars
    }
    data["Serika"]["image_files"] = [f for f in data["Serika"]["image_files"] if Path(f).stem != "Student_Portrait_Serika_Shibasek"]

    with open(data_dir / "chars.yaml", "w", encoding="utf-8") as f:
        f.write(OmegaConf.to_yaml(data, sort_keys=True))


if __name__ == "__main__":
    main()
