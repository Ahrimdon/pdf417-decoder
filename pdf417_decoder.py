import json
import re
import argparse
import logging
from pyzxing import BarCodeReader

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# AAMVA field mappings
SIMPLE_FIELDS = {
    "DCS": "LastName",
    "DAC": "FirstName",
    "DAD": "MiddleName",
    "DBB": "DOB",
    "DBA": "ExpirationDate",
    "DAQ": "LicenseNumber",
    "DAG": "Address",
    "DAI": "City",
    "DAJ": "State",
    "DAK": "ZipCode"
}

FULL_FIELDS = {
    **SIMPLE_FIELDS,
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

def parse_aamva(data, fields):
    """Extract selected fields from the AAMVA barcode."""
    parsed_data = {}
    for key, name in fields.items():
        match = re.search(rf"{key}([^\n\r]+)", data)
        if match:
            parsed_data[name] = match.group(1).strip()
    return parsed_data

def decode_barcode(image_path, mode):
    """Decode PDF417 barcode and process output based on mode."""
    reader = BarCodeReader()
    results = reader.decode(image_path)

    if not results:
        logging.error("No barcode detected.")
        return

    raw_text = results[0].get("parsed", b"").decode("utf-8")

    if mode == "raw":
        print(results)
    elif mode == "simple":
        parsed_json = parse_aamva(raw_text, SIMPLE_FIELDS)
        print(json.dumps(parsed_json, indent=4, ensure_ascii=False))
    elif mode == "full":
        parsed_json = parse_aamva(raw_text, FULL_FIELDS)
        print(json.dumps(parsed_json, indent=4, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(
        description="Decode PDF417 barcode and output data in different formats."
    )
    parser.add_argument("image", help="Path to the barcode image")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--simple", action="store_true", help="Decode and display key readable fields")
    group.add_argument("-f", "--full", action="store_true", help="Decode and display all readable fields")
    group.add_argument("-r", "--raw", action="store_true", help="Display raw barcode output")

    args = parser.parse_args()

    if args.simple:
        mode = "simple"
    elif args.full:
        mode = "full"
    elif args.raw:
        mode = "raw"

    decode_barcode(args.image, mode)

if __name__ == "__main__":
    main()
