# pip install pyzxing

from pyzxing import BarCodeReader

reader = BarCodeReader()
results = reader.decode("barcode.png")

print(results)  # Returns a list of decoded barcodes
