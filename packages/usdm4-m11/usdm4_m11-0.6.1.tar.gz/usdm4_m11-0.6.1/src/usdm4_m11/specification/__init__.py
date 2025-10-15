from simple_error_log import Errors
from usdm4_m11.specification.files import root
from usdm4_m11.specification.sections import Sections
from usdm4_m11.specification.section import Section


class Specification:
    MODULE = "usdm4_m11.specification.Specification"

    def __init__(self):
        self._root = root()
        self._errors = Errors()
        self._sections = {}

    @property
    def default_section(self):
        return "title_page"

    def section_list(self) -> list[str] | None:
        return Sections(self._root, self._errors).list()

    def section(self, section: str) -> str | None:
        return self._section(section).content(section)

    def template(self, section: str) -> str:
        return self._section(section).template()

    def first_element(self, section: str) -> str | None:
        return self._section(section).first_element()

    def element(self, section: str, element: str) -> str | None:
        return self._section(section).element(element)

    def mapping(self, section: str, element: str) -> str:
        return self._section(section).mapping(element)

    def _section(self, section) -> Section:
        if section not in self._sections:
            self._sections[section] = Section(section, self._root, self._errors)
        return self._sections[section]
