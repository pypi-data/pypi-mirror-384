from usdm4_m11.specification.files import sections_file, read_yaml
from simple_error_log import Errors


class Sections:
    MODULE = "usdm4_m11.specification.sections.Sections"

    def __init__(self, root: str, errors: Errors):
        self._root = root
        self._errors = errors

    def list(self) -> list[str] | None:
        results = []
        sections = read_yaml(sections_file())
        section: dict
        for section, section_data in sections.items():
            results.append(
                {
                    "section_number": section_data["number"]
                    if section_data["number"]
                    else "",
                    "section_title": section_data["title"],
                    "name": section,
                }
            )
        return list[sections.keys()]
