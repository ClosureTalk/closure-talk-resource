from argparse import ArgumentParser
from pathlib import Path
import os


def create_common_parser(output_name: str) -> ArgumentParser:
    parser = ArgumentParser()

    # output defaults to Github page resources folder
    script_foler = Path(os.path.split(__file__)[0])
    parser.add_argument(
        "--output",
        default=(script_foler / f"../../closuretalk.github.io/resources/{output_name}").resolve(),
    )
    parser.add_argument("--avatar_size", type=int, default=128)
    parser.add_argument("--stamp_size", type=int, default=200)
    parser.add_argument("--skip_chars", action="store_true")
    parser.add_argument("--skip_stamps", action="store_true")
    parser.add_argument("--skip_filters", action="store_true")

    return parser
