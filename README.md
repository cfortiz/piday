# Pi Day

Celebrating Pi Day (March 14) with Python.

## Changes

### 2023-03-15
- Initial implementation using naive Bailey-Borwein-Plouffe formula.

### 2023-06-06
- Add implementation using Machin's formula.

### 2023-08-17
- Add command line argument parser with parameters for width (default 80),
height (default 24), source image (default pi.png), inverted colors (default 
False), and keeping the source image's aspect ratio (default False).
- Fix bug in Machin's formula implementation.
- Add command line parameter for raw output, with width parameter specifying the
number of decimal digits.
- Refactor to make formulas for computing pi modular.
- Add command line parameter to specify formula.
- Add command line parameters to test formulas, all formulas or specific ones.
