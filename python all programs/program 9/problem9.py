from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Dict, List, Optional, Set


@dataclass
class RegistrationRecord:
    raw_string: str
    reg_id: str = ""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    dob: str = ""
    department_code: str = ""
    # Extracted sub-components
    reg_year: str = ""
    reg_sequence: str = ""
    email_domain: str = ""
    is_valid: bool = False
    errors: List[Dict[str, str]] = field(default_factory=list)


class RegistrationRecordAnalyzer:
    """
    Parses delimited registration strings of the format:
      REG_ID|FULL_NAME|EMAIL|PHONE|DOB|DEPT_CODE
    Validates lengths & formats, extracts components, detects duplicates,
    and categorizes errors by type.
    """

    EXPECTED_FIELDS = 6
    VALID_DEPARTMENTS = {"CSE", "ECE", "EEE", "MECH", "CIVIL", "IT", "AI"}

    # Format & Length Rules
    REG_ID_PATTERN = re.compile(r"^REG-(20\d{2})-(\d{4})$")       # Length: 13 (e.g., REG-2026-0142)
    NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s.'-]{1,48}[A-Za-z.]$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$")
    PHONE_PATTERN = re.compile(r"^(?:\+91-)?[6-9]\d{9}$")
    DEPT_PATTERN = re.compile(r"^[A-Z]{2,5}$")

    def __init__(self):
        self.records: List[RegistrationRecord] = []
        self.seen_reg_ids: Set[str] = set()
        self.seen_emails: Set[str] = set()
        self.seen_phones: Set[str] = set()
        self.error_summary: Dict[str, int] = {
            "STRUCTURAL_ERROR": 0,
            "LENGTH_ERROR": 0,
            "FORMAT_ERROR": 0,
            "DATE_LOGIC_ERROR": 0,
            "DOMAIN_VALUE_ERROR": 0,
            "DUPLICATE_ERROR": 0,
        }

    def _add_error(self, record: RegistrationRecord, category: str, field_name: str, message: str) -> None:
        record.errors.append({
            "category": category,
            "field": field_name,
            "message": message,
        })
        self.error_summary[category] = self.error_summary.get(category, 0) + 1

    def analyze_line(self, raw_line: str) -> RegistrationRecord:
        cleaned = raw_line.strip()
        record = RegistrationRecord(raw_string=cleaned)

        # 1. Structural Parsing Check
        if not cleaned:
            self._add_error(record, "STRUCTURAL_ERROR", "RAW_LINE", "Empty registration record.")
            self.records.append(record)
            return record

        parts = [p.strip() for p in cleaned.split("|")]
        if len(parts) != self.EXPECTED_FIELDS:
            self._add_error(
                record,
                "STRUCTURAL_ERROR",
                "DELIMITER_COUNT",
                f"Expected {self.EXPECTED_FIELDS} pipe-separated fields, found {len(parts)}.",
            )
            self.records.append(record)
            return record

        record.reg_id, record.full_name, record.email, record.phone, record.dob, record.department_code = parts

        # 2. Field Length & Format Validations + Component Extraction
        # --- Registration ID ---
        if len(record.reg_id) != 13:
            self._add_error(
                record,
                "LENGTH_ERROR",
                "reg_id",
                f"Expected exact length 13, got {len(record.reg_id)} ('{record.reg_id}').",
            )
        reg_match = self.REG_ID_PATTERN.match(record.reg_id)
        if not reg_match:
            self._add_error(
                record,
                "FORMAT_ERROR",
                "reg_id",
                f"Must match 'REG-YYYY-NNNN' (e.g., REG-2026-0001), got '{record.reg_id}'.",
            )
        else:
            record.reg_year = reg_match.group(1)
            record.reg_sequence = reg_match.group(2)

        # --- Full Name ---
        if not (3 <= len(record.full_name) <= 50):
            self._add_error(
                record,
                "LENGTH_ERROR",
                "full_name",
                f"Name length must be 3–50 characters, got {len(record.full_name)}.",
            )
        if not self.NAME_PATTERN.match(record.full_name):
            self._add_error(
                record,
                "FORMAT_ERROR",
                "full_name",
                f"Contains invalid characters or formatting: '{record.full_name}'.",
            )

        # --- Email ---
        if not (6 <= len(record.email) <= 80):
            self._add_error(
                record,
                "LENGTH_ERROR",
                "email",
                f"Email length must be 6–80 characters, got {len(record.email)}.",
            )
        email_match = self.EMAIL_PATTERN.match(record.email)
        if not email_match:
            self._add_error(
                record,
                "FORMAT_ERROR",
                "email",
                f"Invalid email format: '{record.email}'.",
            )
        else:
            record.email_domain = email_match.group(1).lower()

        # --- Phone ---
        normalized_phone = record.phone.replace("+91-", "")
        if len(normalized_phone) != 10:
            self._add_error(
                record,
                "LENGTH_ERROR",
                "phone",
                f"Phone number must contain 10 digits (excluding optional +91-), got '{record.phone}'.",
            )
        if not self.PHONE_PATTERN.match(record.phone):
            self._add_error(
                record,
                "FORMAT_ERROR",
                "phone",
                f"Invalid Indian mobile format (must start with 6–9): '{record.phone}'.",
            )

        # --- Date of Birth (YYYY-MM-DD) ---
        if len(record.dob) != 10:
            self._add_error(
                record,
                "LENGTH_ERROR",
                "dob",
                f"DOB must be 10 characters (YYYY-MM-DD), got '{record.dob}'.",
            )
        try:
            parsed_dob = datetime.strptime(record.dob, "%Y-%m-%d")
            if not (1980 <= parsed_dob.year <= 2010):
                self._add_error(
                    record,
                    "DATE_LOGIC_ERROR",
                    "dob",
                    f"Birth year {parsed_dob.year} outside eligible range (1980–2010).",
                )
        except ValueError:
            self._add_error(
                record,
                "FORMAT_ERROR",
                "dob",
                f"Invalid calendar date or format (expected YYYY-MM-DD): '{record.dob}'.",
            )

        # --- Department Code ---
        if not (2 <= len(record.department_code) <= 5):
            self._add_error(
                record,
                "LENGTH_ERROR",
                "department_code",
                f"Department code length must be 2–5 chars, got {len(record.department_code)}.",
            )
        if not self.DEPT_PATTERN.match(record.department_code):
            self._add_error(
                record,
                "FORMAT_ERROR",
                "department_code",
                f"Department code must be uppercase letters: '{record.department_code}'.",
            )
        elif record.department_code not in self.VALID_DEPARTMENTS:
            self._add_error(
                record,
                "DOMAIN_VALUE_ERROR",
                "department_code",
                f"Unrecognized department '{record.department_code}'. Allowed: {sorted(self.VALID_DEPARTMENTS)}.",
            )

        # 3. Duplicate Detection (checked across reg_id, normalized email, and normalized phone)
        norm_email = record.email.lower()
        if record.reg_id:
            if record.reg_id in self.seen_reg_ids:
                self._add_error(record, "DUPLICATE_ERROR", "reg_id", f"Duplicate Registration ID '{record.reg_id}'.")
            else:
                self.seen_reg_ids.add(record.reg_id)

        if norm_email:
            if norm_email in self.seen_emails:
                self._add_error(record, "DUPLICATE_ERROR", "email", f"Duplicate email address '{record.email}'.")
            else:
                self.seen_emails.add(norm_email)

        if normalized_phone and len(normalized_phone) == 10:
            if normalized_phone in self.seen_phones:
                self._add_error(record, "DUPLICATE_ERROR", "phone", f"Duplicate phone number '{record.phone}'.")
            else:
                self.seen_phones.add(normalized_phone)

        record.is_valid = len(record.errors) == 0
        self.records.append(record)
        return record

    def analyze_batch(self, raw_lines: List[str]) -> None:
        for line in raw_lines:
            self.analyze_line(line)

    def generate_report(self) -> None:
        valid_records = [r for r in self.records if r.is_valid]
        invalid_records = [r for r in self.records if not r.is_valid]

        print("=" * 75)
        print("ADVANCED STRING-BASED REGISTRATION RECORD ANALYSIS REPORT")
        print("=" * 75)
        print(f"Total Records Processed : {len(self.records)}")
        print(f"Valid Records           : {len(valid_records)}")
        print(f"Invalid Records         : {len(invalid_records)}")

        print("\n[1] EXTRACTED COMPONENTS FROM VALID RECORDS")
        print(f"  {'Reg ID':<15} {'Year':<6} {'Seq':<6} {'Dept':<6} {'Name':<20} {'Email Domain'}")
        print("  " + "-" * 71)
        for r in valid_records:
            print(
                f"  {r.reg_id:<15} {r.reg_year:<6} {r.reg_sequence:<6} "
                f"{r.department_code:<6} {r.full_name:<20} {r.email_domain}"
            )

        print("\n[2] ERROR CLASSIFICATION BREAKDOWN")
        for category, count in self.error_summary.items():
            print(f"  {category:<22}: {count}")

        print("\n[3] DETAILED RECORD DIAGNOSTICS (INVALID RECORDS)")
        if not invalid_records:
            print("  None — All records passed validation.")
        else:
            for idx, r in enumerate(invalid_records, 1):
                print(f"  {idx}. Raw Input: \"{r.raw_string}\"")
                for err in r.errors:
                    print(f"     - [{err['category']}] ({err['field']}): {err['message']}")
        print("=" * 75)


# ==========================================
# EXAMPLE EXECUTION
# ==========================================
if __name__ == "__main__":
    sample_batch = [
        # Valid records
        "REG-2026-0101|Karthik Reddy|karthik.r@university.edu.in|+91-9876543210|2006-05-14|CSE",
        "REG-2026-0102|Ananya Verma|ananya.v@gmail.com|9123456789|2005-11-22|ECE",
        # Duplicate Reg ID & Email
        "REG-2026-0101|Karthik R|karthik.r@university.edu.in|9988776655|2006-05-14|CSE",
        # Length & Format Errors (bad reg_id length, invalid phone start digit, invalid date)
        "REG-26-103|Ro|rohan_at_mail.com|12345|2007-02-30|MECH",
        # Domain Value Error & Birth Year Logic Error
        "REG-2026-0104|Divya Sri|divya@college.org|8877665544|2015-08-10|BIO",
        # Structural Error (missing fields)
        "REG-2026-0105|Incomplete Entry|only.three@fields.com",
    ]

    analyzer = RegistrationRecordAnalyzer()
    analyzer.analyze_batch(sample_batch)
    analyzer.generate_report()