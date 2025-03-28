import json
import re
from pyzxing import BarCodeReader

def parse_aamva(data):
    """Extract all possible fields from the AAMVA barcode."""
    keys = {
        "DCS": "LastName",
        "DAC": "FirstName",
        "DAD": "MiddleName",
        "DBB": "DOB",
        "DBA": "ExpirationDate",
        "DAQ": "LicenseNumber",
        "DAG": "Address",
        "DAI": "City",
        "DAJ": "State",
        "DAK": "ZipCode",
        "DAY": "EyeColor",
        "DAU": "Height",
        "DBC": "Sex",
        "DCG": "Country",
        "DBD": "IssueDate",
        "DCF": "DocumentDiscriminator",
        "DCK": "InventoryControlNumber",
        "DDE": "ComplianceType",
        "DDF": "CardRevisionDate",
        "DDG": "HazmatEndorsement",
        "DDH": "LimitedTermIndicator",
        "DCU": "NameSuffix",
        "DDC": "MedicalIndicator",
        "DDD": "NonResidentIndicator"
    }

    parsed_data = {}

    for key, name in keys.items():
        match = re.search(rf"{key}([^\n\r]+)", data)
        if match:
            parsed_data[name] = match.group(1).strip()

    return parsed_data

# Decode barcode with ZXing
reader = BarCodeReader()
results = reader.decode("barcode.png")

# Extract data from parsed barcode
if results:
    raw_text = results[0].get("parsed", b"").decode("utf-8")
    parsed_json = parse_aamva(raw_text)

    # Convert to JSON and print
    print(json.dumps(parsed_json, indent=4, ensure_ascii=False))
else:
    print("No barcode detected.")
