if (test-path build)
{
    rm -Recurse -Force build
}

if (test-path dist)
{
    rm -Recurse -Force dist
}

pyinstaller gui.py --onefile `
    --add-data "*.png;." `
    --add-data "*.svg;." `
    --add-data "*.wav;." `
    --add-data "*.ico;." `
    --name rompecabezas `
    --icon icon.ico
