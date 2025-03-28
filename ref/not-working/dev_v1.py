import json
import re
import argparse
import logging
import os
from pyzxing import BarCodeReader
from PIL import Image, ImageDraw

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

def generate_simple_pdf417_barcode(text, output_path, width=400, height=200):
    """
    Generate a simple visual representation of a PDF-417 barcode.
    This is a basic approximation and not a true PDF-417 standard barcode.
    """
    # Create a white background image
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    # Convert text to binary representation
    binary_data = ' '.join(format(ord(c), '08b') for c in text)

    # Draw vertical bars based on binary data
    bar_width = width / (len(binary_data) + 1)
    x = 0
    for bit in binary_data:
        # Alternate bar heights based on bit value
        bar_height = height * 0.8 if bit == '1' else height * 0.3
        
        # Draw the bar
        draw.rectangle([x, height - bar_height, x + bar_width, height], 
                       fill='black')
        
        x += bar_width

    # Save the image
    image.save(output_path)
    logging.info(f"Barcode image generated: {output_path}")

def generate_aamva_barcode(json_path, output_dir):
    """Generate barcode from a JSON file containing AAMVA data."""
    try:
        # Read JSON file
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Construct AAMVA format barcode string
        barcode_text = ""
        
        # Mapping of JSON keys to AAMVA codes (reverse of previous mapping)
        aamva_keys = {v: k for k, v in FULL_FIELDS.items()}
        
        # Generate barcode text
        for key, value in data.items():
            if key in aamva_keys:
                barcode_text += f"{aamva_keys[key]}{value}\n"
        
        # Ensure we have some data
        if not barcode_text:
            logging.error("No valid AAMVA fields found in the JSON file.")
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename based on license number or use default
        filename = f"{data.get('LicenseNumber', 'license')}_barcode.png"
        output_path = os.path.join(output_dir, filename)
        
        # Generate barcode
        generate_simple_pdf417_barcode(barcode_text, output_path)
    
    except FileNotFoundError:
        logging.error(f"JSON file not found: {json_path}")
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON file: {json_path}")
    except Exception as e:
        logging.error(f"Error generating barcode: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Decode PDF417 barcode and output data in different formats."
    )
    parser.add_argument("image", help="Path to the barcode image or JSON file")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--simple", action="store_true", help="Decode and display key readable fields")
    group.add_argument("-f", "--full", action="store_true", help="Decode and display all readable fields")
    group.add_argument("-r", "--raw", action="store_true", help="Display raw barcode output")
    group.add_argument("-g", "--generate", action="store_true", help="Generate barcode from JSON file")
    parser.add_argument("-o", "--output", default=".", help="Output directory for generated barcode (default: current directory)")

    args = parser.parse_args()

    if args.generate:
        generate_aamva_barcode(args.image, args.output)
    else:
        if args.simple:
            mode = "simple"
        elif args.full:
            mode = "full"
        elif args.raw:
            mode = "raw"

        decode_barcode(args.image, mode)

if __name__ == "__main__":
    main()
