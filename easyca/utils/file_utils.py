import json
import os
from pathlib import Path
from typing import Dict, List


def read_json(file: Path) -> "Dict":
    with open(os.path.expandvars(file), 'r') as j:
        return json.load(j)


def write_json(file: Path, content: Dict):
    with open(os.path.expandvars(file), 'w') as j:
        json.dump(content, j)


def list_dirs(path: Path, exclude: List[str] = None, include: List[str] = None) \
        -> "List[Path]":
    result = [Path(str(mydir)) for mydir in os.listdir(path)
              if os.path.isdir(os.path.join(path, mydir))]
    if exclude:
        result = [path for path in result if str(path) not in exclude]
    if include:
        result = [path for path in result if str(path) in include]
    return result


def list_files(path: Path) -> "List[Path]":
    return [Path(str(file)) for file in os.listdir(path)
            if os.path.isfile(os.path.join(path, file))]
