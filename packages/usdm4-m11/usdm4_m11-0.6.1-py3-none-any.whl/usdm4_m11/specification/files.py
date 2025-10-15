import os
import yaml
import pathlib



@staticmethod
def read_yaml(full_path: str) -> dict:
    with open(full_path, "r") as f:
        result = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
    return result


@staticmethod
def read_html(full_path: str) -> str:
    with open(full_path, "r") as f:
        result = f.read()
        f.close()
    return result


@staticmethod
def root() -> str:
    path = pathlib.Path(__file__).parent.parent.resolve()
    return path


@staticmethod
def sections_file() -> str:
    return os.path.join(root(), "data/specification/sections.yaml")
