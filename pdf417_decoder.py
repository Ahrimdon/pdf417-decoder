import json
import re
import argparse
import logging
from typing import Dict, Optional, List
from pathlib import Path

import pdf417gen
from pyzxing import BarCodeReader

# Configure logging with more robust settings
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Use immutable dictionary for field mappings
SIMPLE_FIELDS: Dict[str, str] = {
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

FULL_FIELDS: Dict[str, str] = {
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
    "DDD": "NonResidentIndicator",
    "DLD": "IDType",
    "DCB": "RestrictionsCode",
    "DCD": "ClassificationCode",
    "DDB": "RecordCreationDate",
    "DDA": "AuditInformation",
    "DCA": "VehicleClass",
    "ZVZ": "SecurityData"
}

def parse_aamva(data: str, fields: Dict[str, str]) -> Dict[str, str]:
    """
    Extract selected fields from the AAMVA barcode with improved error handling.
    
    Args:
        data (str): Raw barcode data
        fields (Dict[str, str]): Mapping of field codes to human-readable names
    
    Returns:
        Dict[str, str]: Parsed data with field names as keys
    """
    try:
        parsed_data = {}
        for key, name in fields.items():
            match = re.search(rf"{key}([^\n\r]+)", data)
            if match:
                value = match.group(1).strip()
                # Optional: Add basic validation or cleaning
                parsed_data[name] = value
        return parsed_data
    except Exception as e:
        logger.error(f"Error parsing AAMVA data: {e}")
        return {}

def decode_barcode(image_path: str, mode: str) -> Optional[Dict]:
    """
    Decode PDF417 barcode with enhanced error handling and logging.
    
    Args:
        image_path (str): Path to the barcode image
        mode (str): Decoding mode (raw, simple, full)
    
    Returns:
        Optional[Dict]: Decoded barcode data or None
    """
    try:
        # Validate image path
        if not Path(image_path).is_file():
            logger.error(f"Image file not found: {image_path}")
            return None

        reader = BarCodeReader()
        results = reader.decode(image_path)

        if not results:
            logger.warning("No barcode detected in the image.")
            return None

        raw_text = results[0].get("parsed", b"").decode("utf-8")

        # Dynamic result processing based on mode
        if mode == "raw":
            # Convert byte-based results to a JSON-serializable format
            return {
                "results": [
                    {k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in result.items()}
                    for result in results
                ]
            }
        elif mode == "simple":
            return parse_aamva(raw_text, SIMPLE_FIELDS)
        elif mode == "full":
            return parse_aamva(raw_text, FULL_FIELDS)
        
    except Exception as e:
        logger.error(f"Barcode decoding error: {e}")
        return None

def generate_barcode(
    json_path: str, 
    output_path: str, 
    columns: int = 10, 
    security: int = 2, 
    scale: int = 3, 
    ratio: int = 3, 
    fg_color: str = "#000000", 
    bg_color: str = "#FFFFFF"
) -> bool:
    """
    Generate a PDF417 barcode from JSON with comprehensive error handling.
    
    Args:
        json_path (str): Path to JSON input file
        output_path (str): Path to save generated barcode
        ... (other parameters with defaults)
    
    Returns:
        bool: Success status of barcode generation
    """
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Validate required fields
        missing_fields = [field for field in FULL_FIELDS.values() if field not in data]
        if missing_fields:
            logger.warning(f"Missing fields in JSON: {missing_fields}")
        
        # Convert JSON to AAMVA-formatted string
        aamva_data = "\n".join(
            f"{code}{data[field]}" 
            for code, field in FULL_FIELDS.items() 
            if field in data
        )

        # Generate PDF417 barcode with custom options
        barcode = pdf417gen.encode(
            aamva_data, 
            columns=columns, 
            security_level=security
        )
        image = pdf417gen.render_image(
            barcode, 
            scale=scale, 
            ratio=ratio, 
            fg_color=fg_color, 
            bg_color=bg_color
        )
        image.save(output_path)
        
        logger.info(f"Barcode saved as {output_path}")
        return True
    
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON file: {json_path}")
    except Exception as e:
        logger.error(f"Barcode generation error: {e}")
    
    return False

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

    # Enhanced result handling
    if args.generate:
        result = generate_barcode(
            args.generate, args.output, args.columns, args.security,
            args.scale, args.ratio, args.fg_color, args.bg_color
        )
        print("Barcode generation successful" if result else "Barcode generation failed")
    else:
        # Determine decoding mode
        if args.simple:
            mode = "simple"
        elif args.full:
            mode = "full"
        elif args.raw:
            mode = "raw"
        else:
            parser.error("Decoding mode (-s, -f, or -r) is required when decoding a barcode.")

        result = decode_barcode(args.image, mode)
        if result:
            print(json.dumps(result, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
