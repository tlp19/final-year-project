#!/bin/bash

# Activate the Python virtualenv
source .venv/bin/activate

# Run main.py as sudo
sudo .venv/bin/python3 main.py

# Deactivate the virtualenv
deactivate