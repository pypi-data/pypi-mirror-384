from raw_docx.raw_docx import RawDocx
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation


class Document:
    MODULE = "usdm4_m11.import_.document.Document"
    ICH_HEADERS = [
        (
            "INTERNATIONAL COUNCIL FOR HARMONISATION OF TECHNICAL REQUIREMENTS FOR PHARMACEUTICALS FOR HUMAN USE",
            "ich-m11-header-1",
        ),
        ("ICH HARMONISED GUIDELINE", "ich-m11-header-2"),
        ("Clinical electronic Structured Harmonised Protocol", "ich-m11-header-3"),
        ("(CeSHarP)", "ich-m11-header-4"),
        ("Example", "ich-m11-header-4"),
    ]
    DESIGN_ITEMS = [
        ("Number of Arms", "ich-m11-overall-design-title"),
        ("Trial Blind Schema", "ich-m11-overall-design-title"),
        ("Number of Participants", "ich-m11-overall-design-title"),
        ("Duration", "ich-m11-overall-design-title"),
        ("Committees", "ich-m11-overall-design-title"),
        ("Blinded Roles", "ich-m11-overall-design-title"),
    ]

    def __init__(self, raw_docx: RawDocx, errors: Errors):
        self._raw_docx = raw_docx
        self._sections = self._raw_docx.target_document.sections
        self._errors = errors

    def process(self, date: str) -> dict:
        self._decode_ich_header()
        self._decode_trial_design_summary()
        return {
            "document": {
                "label": "Protocol Document",
                "version": "",  # @todo
                "status": "Final",  # @todo
                "template": "Legacy",
                "version_date": date,
            },
            "sections": [
                {
                    "section_number": str(x.number) if x.number else "",
                    "section_title": x.title,
                    "text": x.to_html(),
                }
                for x in self._sections
            ],
        }

    def _decode_ich_header(self):
        section = self._raw_docx.target_document.section_by_ordinal(1)
        if section:
            for header in self.ICH_HEADERS:
                items = section.find(header[0])
                for item in items:
                    item.add_class(header[1])
        else:
            self._errors.error(
                "Failed to find first  (header) section in M11 document",
                KlassMethodLocation(self.MODULE, "_decode_ich_header"),
            )

    def _decode_trial_design_summary(self):
        section = self._raw_docx.target_document.section_by_number("1.1.2")
        if section:
            tables = section.tables()
            if tables:
                table = tables[0]
                table.replace_class("raw-docx-table", "ich-m11-overall-design-table")
                for design_item in self.DESIGN_ITEMS:
                    items = section.find_at_start(design_item[0])
                    for item in items:
                        item.add_span(design_item[0], design_item[1])
            else:
                self._errors.error(
                    "Failed to find any tables in section 1.1.2 in M11 document",
                    KlassMethodLocation(self.MODULE, "_decode_trial_design_summary"),
                )
        else:
            self._errors.error(
                "Failed to find section 1.1.2 in M11 document",
                KlassMethodLocation(self.MODULE, "_decode_trial_design_summary"),
            )
