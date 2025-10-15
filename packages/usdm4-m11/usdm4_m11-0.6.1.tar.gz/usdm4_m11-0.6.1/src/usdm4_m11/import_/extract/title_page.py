import re
import dateutil.parser as parser
from raw_docx.raw_docx import RawDocx, RawTable
from usdm4_m11.import_.extract.utility import table_get_row
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation


class TitlePage:
    MODULE = "usdm4_m11.import_.title_page.TitlePage"

    def __init__(self, raw_docx: RawDocx, errors: Errors):
        self._raw_docx = raw_docx
        self._sections = self._raw_docx.target_document.sections
        self._errors = errors

    def process(self):
        table: RawTable = self._title_table()
        if table:
            table.replace_class("raw-docx-table", "ich-m11-title-page-table")
            name_and_address = table_get_row(table, "Sponsor Name")
            address = self._get_sponsor_address_simple(name_and_address)
            sponsor = self._get_sponsor_name(name_and_address)
            acronym = table_get_row(table, "Acronym")
            identifier = table_get_row(table, "Sponsor Protocol Identifier")
            compund_code = table_get_row(table, "Compound Code")
            reg_identifiers = table_get_row(
                table, "Regulatory Agency Identifier Number(s)"
            )
            result = {
                "identification": {
                    "titles": {
                        "official": table_get_row(table, "Full Title"),
                        "acronym": acronym,
                        "brief": table_get_row(table, "Short Title"),
                    },
                    "identifiers": [
                        {
                            "identifier": identifier,
                            "scope": {
                                "non_standard": {
                                    "type": "pharma",
                                    "description": "The sponsor organization",
                                    "label": sponsor,
                                    "identifier": "UNKNOWN",
                                    "identifierScheme": "UNKNOWN",
                                    "legalAddress": address,
                                }
                            },
                        }
                    ],
                },
                "compounds": {
                    "compound_codes": compund_code,
                    "compound_names": table_get_row(table, "Compound Name"),
                },
                "amendments_summary": {
                    "amendment_identifier": table_get_row(
                        table, "Amendment Identifier"
                    ),
                    "amendment_scope": table_get_row(table, "Amendment Scope"),
                    "amendment_details": table_get_row(table, "Amendment Details"),
                },
                "study_design": {
                    "label": "Study Design 1",
                    "rationale": "Not set",
                    "trial_phase": table_get_row(table, "Trial Phase"),
                },
                "study": {
                    "sponsor_approval_date": self._get_sponsor_approval_date(table),
                    "version_date": self._get_protocol_date(table),
                    "version": table_get_row(table, "Version Number"),
                    "rationale": "Not set",
                    "name": {
                        "acronym": acronym,
                        "identifier": identifier,
                        "compound_code": compund_code,
                    },
                },
                "other": {
                    "confidentiality": table_get_row(table, "Sponsor Confidentiality"),
                    "regulatory_agency_identifiers": reg_identifiers,
                },
                # self.manufacturer_name_and_address = table_get_row(table, "Manufacturer")
                # self.sponsor_signatory = table_get_row(table, "Sponsor Signatory")
                # self.medical_expert_contact = table_get_row(table, "Medical Expert")
                # self.sae_reporting_method = table_get_row(table, "SAE Reporting")
            }
            extracted_reg_identifiers = self._get_regulatory_identifiers(
                reg_identifiers
            )
            if extracted_reg_identifiers["nct"]:
                identifier = {
                    "identifier": extracted_reg_identifiers["nct"][0],
                    "scope": {
                        "standard": "ct.gov",
                    },
                }
                result["identification"]["identifiers"].append(identifier)
            if extracted_reg_identifiers["ind"]:
                identifier = {
                    "identifier": extracted_reg_identifiers["ind"][0],
                    "scope": {
                        "standard": "fda",
                    },
                }
                result["identification"]["identifiers"].append(identifier)
            return result
        else:
            location = KlassMethodLocation(self.MODULE, "process")
            self._errors.error(
                "Failed to find the title page table in the document", location
            )
            return None

    # def _extra_data(self, table: RawTable) -> None:
    #     self._extra = {
    #         "original_protocol": table_get_row(table, "Original Protocol"),
    #         "regulatory_agency_identifiers": table_get_row(
    #             table, "Regulatory Agency Identifier Number(s)"
    #         ),
    #         "manufacturer_name_and_address": table_get_row(table, "Manufacturer"),
    #         "sponsor_signatory": table_get_row(table, "Sponsor Signatory"),
    #         "medical_expert_contact": table_get_row(table, "Medical Expert"),
    #         "sae_reporting_method": table_get_row(table, "SAE Reporting"),
    #         "sponsor_approval_date": self._get_sponsor_approval_date(table),
    #     }

    def _get_sponsor_name(self, text: str) -> str:
        parts = text.split("\n")
        name = parts[0].strip() if len(parts) > 0 else "Unknown Sponsor"
        self._errors.info(
            f"Sponsor name set to '{name}'",
            location=KlassMethodLocation(self.MODULE, "_get_sponsor_name"),
        )
        return name

    def _get_sponsor_address_simple(self, text: str) -> dict:
        """Simplified version of _get_sponsor_name_and_address without using the address service"""
        raw_parts = text.split("\n") if text else []
        params = {
            "lines": [],
            "city": "",
            "district": "",
            "state": "",
            "postalCode": "",
            "country": "",
        }
        parts = []
        for part in raw_parts:
            if not part.upper().startswith(("TEL", "FAX", "PHONE", "EMAIL")):
                parts.append(part)
        if len(parts) > 0:
            params["lines"] = [part.strip() for part in parts[1:]]
            if len(parts) > 2:
                params["country"] = parts[-1].strip()
        self._errors.info(
            f"Address result '{params}'",
            location=KlassMethodLocation(self.MODULE, "_get_sponsor_address_simple"),
        )
        return params

    def _get_sponsor_approval_date(self, table):
        return self._get_date(table, "Sponsor Approval Date")

    def _get_protocol_date(self, table):
        return self._get_date(table, "Version Date")

    def _get_date(self, table, text):
        try:
            date_text = table_get_row(table, text)
            if date_text:
                date = parser.parse(date_text)
                return date
            else:
                return None
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "_get_date")
            self._errors.exception(
                f"Exception raised during date processing for '{text}'", e, location
            )
            return None

    def _title_table(self):
        section = self._sections[0]
        for table in section.tables():
            title = table_get_row(table, "Protocol Title")
            if title:
                self._errors.info(
                    "Found CPT title page table",
                    location=KlassMethodLocation(self.MODULE, "_title_table"),
                )
                return table
        self._errors.warning(
            "Cannot locate CPT title page table!",
            location=KlassMethodLocation(self.MODULE, "_title_table"),
        )
        return None

    def _get_regulatory_identifiers(self, text: str) -> dict:
        """
        Extract NCT and IND regulatory identifiers from text.

        Args:
            text: Input text that may contain regulatory identifiers

        Returns:
            dict: Dictionary containing lists of found NCT and IND identifiers
        """
        if not text:
            return {"nct": [], "ind": []}

        # Pattern for NCT identifiers: NCT followed by exactly 8 digits
        nct_pattern = r"\bNCT\d{8}\b"

        # Multiple patterns for IND identifiers:
        # 1. IND followed directly by 6 digits (original format)
        # 2. IND followed by whitespace then 6 digits
        # 3. Title containing "IND" followed by space/colon then 6 digits
        ind_patterns = [
            r"\bIND\d{6}\b",  # IND123456
            r"\bIND\s+(\d{6})\b",  # IND 123456
            r"IND\s*\w*[\s:]+(\d{6})\b",  # Title with IND: 123456 or IND Number: 123456
        ]

        # Find NCT matches
        nct_matches = re.findall(nct_pattern, text, re.IGNORECASE)
        nct_identifiers = [match.upper() for match in nct_matches]

        # Find IND matches using multiple patterns
        ind_identifiers = []

        # Pattern 1: IND followed directly by 6 digits
        direct_matches = re.findall(ind_patterns[0], text, re.IGNORECASE)
        for match in direct_matches:
            ind_identifiers.append(match.upper())

        # Pattern 2: IND followed by whitespace then 6 digits
        spaced_matches = re.findall(ind_patterns[1], text, re.IGNORECASE)
        for match in spaced_matches:
            ind_identifiers.append(match)  # match is just the digits

        # Pattern 3: Title containing "IND" followed by space/colon then 6 digits
        title_matches = re.findall(ind_patterns[2], text, re.IGNORECASE)
        for match in title_matches:
            ind_identifiers.append(match)  # match is just the digits

        # Remove duplicates while preserving order
        nct_identifiers = list(dict.fromkeys(nct_identifiers))
        ind_identifiers = list(dict.fromkeys(ind_identifiers))

        result = {"nct": nct_identifiers, "ind": ind_identifiers}

        # Log the results
        location = KlassMethodLocation(self.MODULE, "_get_regulatory_identifiers")
        if nct_identifiers or ind_identifiers:
            self._errors.info(
                f"Found regulatory identifiers: NCT={nct_identifiers}, IND={ind_identifiers}",
                location,
            )
        else:
            self._errors.info("No regulatory identifiers found", location)

        return result

    def _preserve_original(self, original_parts, value):
        for part in original_parts:
            for item in re.split(r"[,\s]+", part):
                if item.upper() == value.upper():
                    return item
        return value

    def extra(self):
        return {
            "sponsor_confidentiality": self.sponosr_confidentiality,
            "compound_codes": self.compound_codes,
            "compound_names": self.compound_names,
            "amendment_identifier": self.amendment_identifier,
            "amendment_scope": self.amendment_scope,
            "amendment_details": self.amendment_details,
            "sponsor_name_and_address": self.sponsor_name_and_address,
            "original_protocol": self.original_protocol,
            "regulatory_agency_identifiers": self.regulatory_agency_identifiers,
            "manufacturer_name_and_address": self.manufacturer_name_and_address,
            "sponsor_signatory": self.sponsor_signatory,
            "medical_expert_contact": self.medical_expert_contact,
            "sae_reporting_method": self.sae_reporting_method,
            "sponsor_approval_date": self.sponsor_approval_date,
        }

    def _get_sponsor_name_and_address_simple(self):
        """Simplified version of _get_sponsor_name_and_address without using the address service"""
        name = "[Sponsor Name]"
        parts = (
            self.sponsor_name_and_address.split("\n")
            if self.sponsor_name_and_address
            else []
        )
        params = {
            "lines": [],
            "city": "",
            "district": "",
            "state": "",
            "postalCode": "",
            "country": None,
        }
        if len(parts) > 0:
            name = parts[0].strip()
            self._errors.info(f"Sponsor name set to '{name}'")
        if len(parts) > 1:
            # Simple address parsing - just store the address lines
            params["lines"] = [part.strip() for part in parts[1:]]
            # Try to extract country from the last line
            if len(parts) > 2:
                last_line = parts[-1].strip()
                country_code = self._builder.iso3166_code(last_line)
                if country_code:
                    params["country"] = country_code

        self._errors.info(f"Name and address result '{name}', '{params}'")
        return name, params

    def _get_sponsor_approval_date(self, table: RawTable) -> str:
        return self._get_date(table, "Sponsor Approval")

    def _get_protocol_date(self, table):
        return self._get_date(table, "Version Date")

    def _get_date(self, table: RawTable, header_text: str) -> str:
        try:
            date_text = table_get_row(table, header_text)
            if date_text:
                return date_text.strip()
            else:
                return ""
        except Exception as e:
            data = date_text if date_text else ""
            self._errors.exception(
                f"Exception raised during date processing for '{data}'",
                e,
                KlassMethodLocation(self.MODULE, "_get_date"),
            )
            return ""

    def _title_table(self):
        section = self._sections[0]
        for table in section.tables():
            title = table_get_row(table, "Full Title")
            if title:
                self._errors.info(
                    "Found M11 title page table",
                    location=KlassMethodLocation(self.MODULE, "_title_table"),
                )
                return table
        self._errors.warning(
            "Cannot locate M11 title page table!",
            location=KlassMethodLocation(self.MODULE, "_title_table"),
        )
        return None

    def _preserve_original(self, original_parts, value):
        for part in original_parts:
            for item in re.split(r"[,\s]+", part):
                if item.upper() == value.upper():
                    return item
        return value
