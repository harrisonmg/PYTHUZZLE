#!/bin/bash
rm -rf build dist
pyinstaller gui.py --onefile \
    --add-data "*.png:." \
    --add-data "*.svg:." \
    --add-data "*.wav:." \
    --add-data "*.ico:." \
    --name rompecabezas \
    --icon icon.ico
