#!/bin/bash

# Install system dependencies (for Ubuntu/Debian)
echo "Updating package list..."
sudo apt-get update

# Ensure python3 and pip3 are installed
echo "Installing python3 and pip3..."
sudo apt-get install -y python3 python3-pip

# Enaure java is installed
echo "Installing Java..."
sudo apt-get install -y default-jre

# Install Python virtual environment (optional but recommended)
echo "Installing virtualenv..."
sudo apt-get install -y python3-venv

# Create a virtual environment (optional but recommended)
echo "Creating a virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies from requirements.txt
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Success message
echo "Installation complete! You can now run the script using the following command:"
echo "source venv/bin/activate && python3 decode_pdf417_full.py <image_file>"
