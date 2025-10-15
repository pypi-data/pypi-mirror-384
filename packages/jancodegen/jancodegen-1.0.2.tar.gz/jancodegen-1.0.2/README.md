# JAN Code Generator

[![PyPI version]( https://img.shields.io/badge/pypi-1.0.2-blue)](https://pypi.org/project/jancodegen/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package for generating random JAN (Japanese Article Number) codes and related product identification codes with valid check digits.

The check digit calculation follows the standard GS1 algorithm as documented on the [GS1 Japan website](https://www.gs1jp.org/code/jan/check_digit.html).

## Features

- Generate random GTIN-13, GTIN-8, GTIN-14, UPC-12, SSCC-18, and GRAI-14 codes
- Support custom prefix for all code generation functions
- Generate JAN codes of arbitrary length with `random_jan_code`
- Validate JAN/GTIN/UPC codes with `is_valid`
- All codes include automatically calculated valid check digits
- Pure Python implementation with no external dependencies

## Installation

Install from PyPI:

```bash
pip install jancodegen
```

Or install from source:

```bash
git clone https://github.com/kientt137/jancodegen.git
cd jancodegen
pip install .
```

## Usage

### Basic Usage

```python
from jancodegen import jan

# Generate codes with default random values
gtin13 = jan.random_gtin_13()                   # 13-digit GTIN-13 code
upc12 = jan.random_upc_12()                     # 12-digit UPC-12 code
sscc18 = jan.random_sscc_18()                   # 18-digit SSCC-18 code
grai14 = jan.random_grai_14()                   # 14-digit GRAI-14 code
gtin8_prefixed = jan.random_gtin_8("12")        # GTIN-8 starting with '12'
gtin14_prefixed = jan.random_gtin_14("123")     # GTIN-14 starting with '123'

# Generate arbitrary length JAN code
custom_jan_prefixed = jan.random_jan_code(13, "12345") # 13-digit JAN code starting with '12345'

# Validate codes
assert jan.is_valid(gtin13)
```

## Code Formats

| Format      | Length      | Description                              | Prefix (default) |
|-------------|------------|------------------------------------------|------------------|
| GTIN-13     | 13 digits  | Global Trade Item Number                 | Customizable     |
| GTIN-8      | 8 digits   | Global Trade Item Number (short)         | Customizable     |
| GTIN-14     | 14 digits  | Global Trade Item Number (carton)        | '1' or custom    |
| UPC-12      | 12 digits  | Universal Product Code                   | Customizable     |
| SSCC-18     | 18 digits  | Serial Shipping Container Code           | '0' or custom    |
| GRAI-14     | 14 digits  | Global Returnable Asset Identifier       | '0' or custom    |
| JAN (custom)| 4-32 digits| Arbitrary-length JAN code                | Customizable     |

## Requirements

- Python 3.7 or higher
- No external dependencies required

## Development

### Running Tests

```bash
pip install pytest
python -m pytest tests/
```

### Building the Package

```bash
python setup.py sdist bdist_wheel
```

## License

This project is licensed under the MIT License

## Issues

If you find any bugs or have suggestions for improvements, please open an issue on GitHub.
