import logging


def setup_logging(level=logging.INFO, file=None):
    handlers = [logging.StreamHandler()]
    if file is not None:
        handlers += [logging.FileHandler(file, encoding="utf-8")]
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
