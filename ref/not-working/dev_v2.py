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

class PDF417Encoder:
    """Comprehensive PDF-417 Barcode Encoder"""
    
    # PDF-417 encoding tables
    TEXT_COMPACTION_MODE = 0
    BYTE_COMPACTION_MODE = 1
    NUMERIC_COMPACTION_MODE = 2

    CODEWORD_TABLE = [
        0x1D5C, 0x1EAC, 0x1F56, 0x1F2A, 0x1D2E, 0x1E56, 0x1E2A, 0x1D4A,
        0x1E2C, 0x1D4C, 0x1E4A, 0x1D52, 0x1E52, 0x1D5A, 0x1E5A, 0x1D6A
    ]

    @staticmethod
    def text_to_codewords(text):
        """Convert text to PDF-417 codewords"""
        codewords = []
        current_word = 0
        bit_count = 0

        for char in text:
            # Simple conversion (this is a basic approximation)
            char_val = ord(char)
            
            # Pack bits into codewords
            current_word = (current_word << 8) | char_val
            bit_count += 8

            # When we have 16 bits, add to codewords
            while bit_count >= 16:
                codewords.append(current_word >> (bit_count - 16))
                current_word &= (1 << (bit_count - 16)) - 1
                bit_count -= 16

        # Handle any remaining bits
        if bit_count > 0:
            codewords.append(current_word << (16 - bit_count))

        return codewords

    @staticmethod
    def calculate_error_correction(codewords, error_correction_level=2):
        """
        Calculate Reed-Solomon error correction codewords
        This is a simplified approximation of the actual algorithm
        """
        # Primitive polynomial for Reed-Solomon
        generator_poly = [1, 3, 2, 1, 1]
        
        # Calculate error correction codewords
        error_codewords = [0] * error_correction_level
        
        for cw in codewords:
            for i in range(error_correction_level):
                error_codewords[i] ^= cw
                
        return error_codewords

    def encode(self, data):
        """Encode data into PDF-417 pattern"""
        # Convert text to codewords
        codewords = self.text_to_codewords(data)
        
        # Calculate error correction
        error_codewords = self.calculate_error_correction(codewords)
        
        # Combine data and error correction codewords
        full_codewords = codewords + error_codewords
        
        return full_codewords

def generate_pdf417_barcode(text, output_path, width=400, height=200):
    """Generate an approximation of a PDF-417 barcode"""
    # Create a white background image
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    # Encode the text
    encoder = PDF417Encoder()
    codewords = encoder.encode(text)

    # Draw the barcode
    x = 0
    bar_height = height
    for i, codeword in enumerate(codewords):
        # Convert codeword to binary pattern
        for j in range(16):  # 16-bit codewords
            bit = (codeword >> (15 - j)) & 1
            
            # Alternate bar widths based on bit
            bar_width = 3 if bit else 2
            
            # Alternate colors
            color = 'black' if i % 2 == 0 else 'white'
            
            # Draw bar
            draw.rectangle([x, 0, x + bar_width, bar_height], fill=color)
            
            # Move x position
            x += bar_width

    # Save the image
    image.save(output_path)
    logging.info(f"PDF-417 barcode image generated: {output_path}")

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
        generate_pdf417_barcode(barcode_text, output_path)
    
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
