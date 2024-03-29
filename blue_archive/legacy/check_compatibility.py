from pathlib import Path

from utils.json_utils import read_json

script_dir = Path(__file__).parent


def main():
    # verify that we maintain all ids
    old_data = read_json(script_dir / "char.json")
    new_data = read_json(script_dir.parent / "data/char_data.json")

    old_ids = set((d["id"] for d in old_data))
    new_ids = set((d["id"] for d in new_data))

    missing_ids = old_ids - new_ids
    added_ids = new_ids - old_ids

    print(f"Missing ids: {len(missing_ids)}")
    if len(missing_ids) > 0:
        print("\n  " + "\n  ".join(sorted(missing_ids)))
    print(f"Added ids: {len(added_ids)}")

    # verify images
    new_data = read_json(script_dir.parent.parent.parent / "closuretalk.github.io/resources/ba/char.json")

    old_images = {
        d["id"]: d["images"] for d in old_data
    }
    new_images = {
        d["id"]: d["images"] for d in new_data
    }
    for key, names in old_images.items():
        new_names = new_images[key]
        missing_names = [
            name for name in names if name not in new_names
        ]
        if len(missing_names) > 0:
            print(key)
            print("  " + "\n  ".join(sorted(missing_names)))
            print()


if __name__ == "__main__":
    main()
