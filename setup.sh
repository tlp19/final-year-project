#!/bin/bash

# Install general Linux dependencies
echo "Installing Linux dependencies..."
sudo apt-get update
sudo apt-get install -y libatlas-base-dev

# Setting up Raspberry Pi GPIO
echo "Setting up Raspberry Pi GPIO..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_serial 0
sudo raspi-config nonint do_ssh 0
sudo apt-get install -y i2c-tools libgpiod-dev

echo ""
echo "To change the I2C baud rate, run \"sudo nano /boot/config.txt\" and add"
echo "\",i2c_arm_baudrate=5000\" right after \"dtparam=i2c_arm=on\" on the same line."
echo "Then reboot your Raspberry Pi by running \"sudo reboot\"."
echo ""

# Create a python virtualenv and install project dependencies
echo "Installing Python dependencies..."
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

# Create a data folder and initialise a csv file with headers
echo "Creating data folder and empty collections.csv..."
mkdir data
touch data/collections.csv
echo "timestamp,container_type,container_id" > data/collections.csv

# Deactivate the virtualenv
deactivate

echo ""
echo "Setup complete! Please reboot your Raspberry Pi by running \"sudo reboot\"."