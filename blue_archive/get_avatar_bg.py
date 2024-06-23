from argparse import ArgumentParser
from pathlib import Path

from PIL import Image
from tqdm import tqdm


def main():
    resource_project_foler = Path(__file__).parent.parent

    parser = ArgumentParser()
    parser.add_argument(
        "-a", "--astgenne",
        default=(resource_project_foler.parent.parent.parent / "Data/Astgenne")
    )
    parser.add_argument(
        "-o", "--output",
        default=(resource_project_foler.parent / "closuretalk.github.io/resources/ba/avatar-bg").resolve(),
    )
    parser.add_argument("--size", type=int, default=200)
    args = parser.parse_args()

    root = Path(args.astgenne) / "ba/assets/UIs/01_Common/14_CharacterCollect"
    print(root)
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)
    size = args.size

    files = sorted(root.glob("BG_*_Collection.png"))
    out_files = [out_root / f"{f.stem.split('_')[1]}.webp" for f in files]
    tasks = [p for p in zip(files, out_files) if not p[1].exists()]
    for src, dst in tqdm(tasks):
        img = Image.open(src)
        width, height = img.width, img.height
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))
        img.save(dst, quality=95, method=6)


if __name__ == "__main__":
    main()
