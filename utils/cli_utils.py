from argparse import ArgumentParser
from pathlib import Path


def create_common_parser(output_name: str) -> ArgumentParser:
    parser = ArgumentParser()

    resource_project_foler = Path(__file__).parent.parent
    parser.add_argument(
        "-a", "--astgenne",
        default=(resource_project_foler.parent.parent.parent / "Data/Astgenne")
    )
    # output defaults to Github page resources folder
    parser.add_argument(
        "-o", "--output",
        default=(resource_project_foler.parent / f"closuretalk.github.io/resources/{output_name}").resolve(),
    )
    parser.add_argument("--avatar_size", type=int, default=128)
    parser.add_argument("--stamp_size", type=int, default=200)
    parser.add_argument("--skip_chars", action="store_true")
    parser.add_argument("--skip_stamps", action="store_true")
    parser.add_argument("--skip_filters", action="store_true")

    return parser
