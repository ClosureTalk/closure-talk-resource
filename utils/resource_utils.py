import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

from tqdm import tqdm

from utils.image_utils import process_image
from utils.logging_utils import setup_logging
from utils.models import Character
from utils.json_utils import write_json, write_list
from utils.cli_utils import create_common_parser
from argparse import ArgumentParser

def char_json_path(out_root: Path):
    return out_root / "char.json"


def stamps_json_path(out_root: Path):
    return out_root / "stamps.json"


class ResourceProcessor:
    def __init__(self, key: str) -> None:
        self.key = key

        setup_logging()

        parser = self.configure_parser(create_common_parser(key))
        self.args = parser.parse_args()
        self.out_root = Path(self.args.output)

    def configure_parser(self, parser: ArgumentParser) -> ArgumentParser:
        return parser

    def get_chars(self) -> Tuple[List[Character], Dict[str, Path]]:
        raise NotImplementedError()

    def get_stamps(self) -> List[str]:
        raise NotImplementedError()

    def main(self):
        characters, avatar_paths = self._process_chars()
        self._process_avatars(characters, avatar_paths)
        self._process_stamps(self.get_stamps())

    def _process_chars(self) -> Tuple[List[Character], Dict[str, Path]]:
        out_root = self.out_root

        data_file = char_json_path(out_root)

        characters, avatar_paths = self.get_chars()
        write_list(Character, data_file, characters)
        logging.info(f"Wrote {data_file}")

        return characters, avatar_paths

    def _process_avatars(self, characters: List[Character], image_paths: Dict[str, Path]):
        out_images = self.out_root / "characters"
        src_files = [image_paths[img] for ch in characters for img in ch.images]
        dst_files = [out_images / f"{img}.webp" for ch in characters for img in ch.images]

        self._process_image_list(
            src_files,
            dst_files,
            self.args.avatar_size,
        )

    def _process_stamps(self, stamp_files: List[str]):
        out_stamps = self.out_root / "stamps"

        names = [os.path.splitext(os.path.split(f)[1])[0] for f in stamp_files]
        self._process_image_list(
            stamp_files,
            [out_stamps / f"{name}.webp" for name in names],
            self.args.stamp_size,
        )

        write_json(stamps_json_path(self.out_root), names)

    def _process_image_list(self, src_files: List[str], dst_files: List[str], size: int):
        all_files = list(zip(src_files, dst_files))
        pending = [
            f for f in all_files if not os.path.isfile(f[1])
        ]

        logging.info(f"Process {len(pending)} of {len(all_files)} images")
        if len(pending) == 0:
            return

        for src, dst in tqdm(pending):
            try:
                os.makedirs(os.path.split(dst)[0], exist_ok=True)
                process_image(src, dst, size)
            except:
                logging.error(f"Failed: {src} -> {dst}")
                raise
