import json
import re
import argparse
import logging
from pyzxing import BarCodeReader
import pdf417gen

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

def generate_barcode(json_path, output_path, columns, security, scale, ratio, fg_color, bg_color):
    """Generate a PDF417 barcode from JSON file with customization options."""
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Convert JSON to AAMVA-formatted string
        aamva_data = "\n".join(f"{code}{data[field]}" for code, field in FULL_FIELDS.items() if field in data)

        # Generate PDF417 barcode with custom options
        barcode = pdf417gen.encode(aamva_data, columns=columns, security_level=security)
        image = pdf417gen.render_image(barcode, scale=scale, ratio=ratio, fg_color=fg_color, bg_color=bg_color)
        image.save(output_path)
        
        logging.info(f"Barcode saved as {output_path}")
    except Exception as e:
        logging.error(f"Error generating barcode: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Decode or generate PDF417 barcode based on AAMVA format."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("image", nargs="?", help="Path to the barcode image")
    group.add_argument("-g", "--generate", metavar="JSON_FILE", help="Generate a PDF417 barcode from a JSON file")

    parser.add_argument("-o", "--output", metavar="OUTPUT_FILE", default="barcode.png", help="Output file for generated barcode (default: barcode.png)")
    
    # Decoding options
    parser.add_argument("-s", "--simple", action="store_true", help="Decode and display key readable fields")
    parser.add_argument("-f", "--full", action="store_true", help="Decode and display all readable fields")
    parser.add_argument("-r", "--raw", action="store_true", help="Display raw barcode output")
    
    # Barcode generation customization
    parser.add_argument("--columns", type=int, default=10, choices=range(1, 31), help="Number of columns (default: 10, range: 1-30)")
    parser.add_argument("--security", type=int, default=2, choices=range(0, 9), help="Error correction level (default: 2, range: 0-8)")
    parser.add_argument("--scale", type=int, default=3, help="Barcode scaling factor (default: 3)")
    parser.add_argument("--ratio", type=int, default=3, help="Module height-to-width ratio (default: 3)")
    parser.add_argument("--fg-color", default="#000000", help="Foreground color (default: black)")
    parser.add_argument("--bg-color", default="#FFFFFF", help="Background color (default: white)")

    args = parser.parse_args()

    if args.generate:
        generate_barcode(
            args.generate, args.output, args.columns, args.security,
            args.scale, args.ratio, args.fg_color, args.bg_color
        )
    else:
        if args.simple:
            mode = "simple"
        elif args.full:
            mode = "full"
        elif args.raw:
            mode = "raw"
        else:
            parser.error("Decoding mode (-s, -f, or -r) is required when decoding a barcode.")
        
        decode_barcode(args.image, mode)

if __name__ == "__main__":
    main()
