import json
import os


def read_json(file, default_func=None):
    if file is None or not os.path.isfile(file):
        return default_func()
    with open(file, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def write_json(file, data):
    os.makedirs(os.path.split(file)[0], exist_ok=True)
    with open(file, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))


def write_list(cls, file, data):
    os.makedirs(os.path.split(file)[0], exist_ok=True)
    text = cls.schema().dumps(data, many=True, indent=2, ensure_ascii=False, sort_keys=True)
    with open(file, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
