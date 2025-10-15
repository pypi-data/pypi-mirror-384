import os
from usdm4_m11.specification.files import read_yaml, sections_file, read_html
from simple_error_log import Errors


class Section:
    MODULE = "usdm4_m11.specification.section.Section"

    def __init__(self, section: str, root: str, errors: Errors):
        self._section = section
        self._root = root
        self._errors = errors
        self._sections = None

    def content(self, section: str) -> str | None:
        self._read_sections()
        return self._sections[section] if section in self._sections else None

    def elements(self) -> list[dict]:
        self._read_sections()
        return self._read_elements()

    def element(self, name: str) -> dict:
        self._read_sections()
        elements = self._read_elements()
        return elements[name]

    def mapping(self, name: str) -> dict:
        self._read_sections()
        mappings = self._read_mappings()
        return mappings[name]

    def first_element(self) -> dict:
        self._read_sections()
        elements = self._read_elements()
        print(f"ELEMENTS: {elements.keys()}")
        element = next((v for k, v in elements.items() if v["ordinal"] == 1), None)
        return element

    def template(self) -> str:
        self._read_sections()
        result = self._read_template()
        return result

    def _read_sections(self):
        if not self._sections:
            print("READING SECTIONS")
            self._sections = read_yaml(sections_file())
        return self._sections

    def _read_elements(self):
        filepath = self._data_file("elements")
        return read_yaml(filepath)

    def _read_template(self):
        filepath = self._data_file("template")
        return read_html(filepath)

    def _read_mappings(self):
        filepath = self._data_file("mappings")
        return read_yaml(filepath)

    def _data_file(self, key: str) -> str:
        filename = self._sections[self._section][key]
        return os.path.join(self._root, filename)
