import json
import re
import argparse
import logging
from pyzxing import BarCodeReader

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# AAMVA Key Mapping
AAMVA_KEYS = {
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

def parse_aamva(data):
    """Extract all possible fields from an AAMVA barcode."""
    parsed_data = {}

    for key, name in AAMVA_KEYS.items():
        match = re.search(rf"{key}([^\n\r]+)", data)
        if match:
            parsed_data[name] = match.group(1).strip()

    return parsed_data

def decode_pdf417(file_path):
    """Decode a PDF417 barcode using ZXing."""
    reader = BarCodeReader()
    results = reader.decode(file_path)

    if not results:
        logging.error("No barcode detected.")
        return None

    try:
        raw_text = results[0].get("parsed", b"").decode("utf-8")
        return parse_aamva(raw_text)
    except Exception as e:
        logging.error(f"Error decoding barcode: {e}")
        return None

def main():
    """Main function to handle command-line arguments and execute the script."""
    parser = argparse.ArgumentParser(description="Decode PDF417 barcode from an image and return JSON output.")
    
    parser.add_argument("file", nargs="?", help="Path to the image file containing the PDF417 barcode")
    parser.add_argument("-f", "--file", dest="file_opt", help="Alternative way to specify the image file")

    args = parser.parse_args()
    file_path = args.file or args.file_opt

    if not file_path:
        parser.error("No input file provided. Use 'python3 script.py image.png' or 'python3 script.py -f image.png'.")

    logging.info(f"Decoding barcode from: {file_path}")
    parsed_json = decode_pdf417(file_path)

    if parsed_json:
        print(json.dumps(parsed_json, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
