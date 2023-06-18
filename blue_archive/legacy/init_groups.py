from pathlib import Path

from omegaconf import OmegaConf

from blue_archive.common import GroupData, GroupLangData
from utils.json_utils import read_json


def main():
    script_dir = Path(__file__).parent
    groups = {}
    for tp in ["clubs", "schools"]:
        data = read_json(script_dir / f"{tp}.json")
        data = [
            OmegaConf.structured(GroupLangData(key, value)) for key, value in data.items()
        ]
        data = sorted(data, key=lambda d: d.id)
        with open(script_dir.parent / f"lang/{tp}.yaml", "w", encoding="utf-8") as f:
            f.write(OmegaConf.to_yaml(data, sort_keys=True))

        groups[tp] = {
            d.id: GroupData(d.id, []) for d in data
        }

    chars = read_json(script_dir / "char.json")
    for tp in ["clubs", "schools"]:
        tp_groups = groups[tp]
        for char in chars:
            for search in char["searches"]:
                if search in tp_groups:
                    tp_groups[search].members.append(char["id"])
        for gp in tp_groups.values():
            gp.members = sorted(gp.members)

        tp_groups = sorted(tp_groups.values(), key=lambda d: d.id)
        with open(script_dir.parent / f"manual/{tp}.yaml", "w", encoding="utf-8") as f:
            f.write(OmegaConf.to_yaml(tp_groups, sort_keys=True))


if __name__ == "__main__":
    main()
