#
# This script can be run to build the package, and upload it to the test pypi location.
# For testing only.
# You must defined a $env:PYPI_TOKEN value in the environment before running this.

$ErrorActionPreference = "Stop"

venv\Scripts\Activate.ps1
pip install build

Write-Host "Building package..." -ForegroundColor Green
python -m build

Write-Host "Checking package..." -ForegroundColor Green
pip install twine
twine check dist/*

Write-Host "Uploading package to test PyPI..." -ForegroundColor Green
twine upload --verbose `
    --repository-url "https://test.pypi.org/legacy/" -u "__token__" -p "${env:PYPI_TOKEN}" ./dist/*
