from raw_docx.raw_docx import RawDocx
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4_m11.import_.extract.title_page import TitlePage
from usdm4_m11.import_.extract.inclusion_exclusion import InclusionExclusion
from usdm4_m11.import_.extract.amendments import Amendments
from usdm4_m11.import_.extract.document import Document


class ExtractStudy:
    MODULE = "usdm4_cpt.import_.extract.__init__.ExtractStudy"

    def __init__(self, raw_docx: RawDocx, errors: Errors):
        self._raw_docx = raw_docx
        self._sections = self._raw_docx.target_document.sections
        self._errors = errors

    def process(self) -> dict:
        try:
            title_page = TitlePage(self._raw_docx, self._errors)
            ie = InclusionExclusion(self._raw_docx, self._errors)
            amendments = Amendments(self._raw_docx, self._errors)
            document = Document(self._raw_docx, self._errors)
            result = title_page.process()
            result["document"] = document.process(result["study"]["version_date"])
            result["population"] = {
                "label": "Default population",
                "inclusion_exclusion": ie.process(),
            }
            result["amendments"] = amendments.process()
            return result
        except Exception as e:
            print(f"Exception: {e}")
            location = KlassMethodLocation(self.MODULE, "process")
            self._errors.exception(
                "Exception raised extracting study data",
                e,
                location,
            )
            return None
