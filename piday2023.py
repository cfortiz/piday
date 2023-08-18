import argparse
import contextlib
import sys
import traceback
from decimal import Decimal, localcontext

from PIL import Image

from typing import Type, Callable, TextIO


DEFAULT_PRECISION: int = 100
DEFAULT_TEXT_WIDTH: int = 80
DEFAULT_TEXT_HEIGHT: int = 24
DEFAULT_SOURCE_IMAGE: str = 'pi.png'

Formula = Type[Callable[[int], str]]


def compute_pi(precision: int = DEFAULT_PRECISION,
               formula: Formula = None) -> str:
    """Compute π to the specified decimal precision with the given formula."""
    
    if formula is None:
        formula = compute_pi_agm

    original_max_str_digits = sys.get_int_max_str_digits()
    conversion_precision = precision*2
    changed_max_str_digits: bool = False
    try:
        with contextlib.suppress(ValueError):        
            sys.set_int_max_str_digits(conversion_precision)
            changed_max_str_digits = True
        return formula(precision)
    finally:
        if changed_max_str_digits:
            with contextlib.suppress(ValueError):        
                sys.set_int_max_str_digits(original_max_str_digits)


def compute_pi_bbp(precision: int = DEFAULT_PRECISION) -> str:
    """Compute π to the specified decimal precision using the BBP formula."""
    precision_padding: int = 4
    
    with localcontext() as ctx:
        ctx.prec = precision + precision_padding

        pi = Decimal(0)
        precision_scale: int = 10**(precision+precision_padding)
        pi_int: int = 0
        old_pi_int: int = None
        for k in range(precision+precision_padding):
            _8k = 8*k
            old_pi_int = pi_int
            term1 = Decimal(4) / Decimal(_8k+1)
            term2 = Decimal(2) / Decimal(_8k+4)
            term3 = Decimal(1) / Decimal(_8k+5)
            term4 = Decimal(1) / Decimal(_8k+6)
            term = term1 - term2 - term3 - term4
            denominator = Decimal(16**k)
            pi += term / denominator
            pi_int = int(pi*precision_scale)
            if pi_int == old_pi_int:
                break
        pi_str = str(pi_int)
                    
        return f'{pi_str[0]}.{pi_str[1:]}'[:precision+2]


def compute_pi_machin(precision: int = DEFAULT_PRECISION) -> str:
    """Compute π to the specified decimal precision using Machin's formula."""
    precision_padding: int = 4
    with localcontext() as ctx:
        ctx.prec = precision + precision_padding
        
        pi: Decimal = 4 * (4 * decimal_atan2(Decimal(5)) - decimal_atan2(Decimal(239)))
        precision_scale: int = 10**(precision + 2)
        pi_int: int = 0
        pi_int = int(pi*precision_scale)
        pi_str: str = str(pi_int)[:precision + 1]
        assert len(pi_str) == precision + 1
        return f'{pi_str[0]}.{pi_str[1:]}'


def compute_pi_agm(precision: int = DEFAULT_PRECISION) -> str:
    """Compute π to the specified decimal precision using the AGM formula."""
    precision_padding: int = 3
    with localcontext() as ctx:
        ctx.prec = precision + precision_padding
        epsilon = Decimal(10)**(-precision) / Decimal(2)
        
        a = n = Decimal(1)
        g = 1 / Decimal(2).sqrt()
        z = Decimal('0.25')
        half = Decimal('0.5')
        old_pi, pi = None, 0
        
        def iterate():
            nonlocal a, g, z, n, old_pi, pi
            x = [(a + g) * half, (a * g).sqrt()]
            var = x[0] - a
            z -= var * var * n
            n += n
            a, g = x
            old_pi, pi = pi, a * a / z
        
        for i in range(18):
            iterate()
        
        while old_pi - pi > epsilon:
            iterate()
        
        return str(pi)[:precision+2]

        
def decimal_atan2(y: Decimal, x: Decimal = None) -> Decimal:
    """Compute the arctangent of y/x, if x > 0, or of 1/y if x is None.
    
    Sums terms of the power series expansion of arctangent.
    
    Args:
        y: The Decimal numerator of the fraction if x is not None, or the
           denominator otherwise.
        x: The Decimal denominator of the fraction if not None.
    
    Returns:
        The Decimal arctangent of y/x, if x > 0, or of 1/y if x is None.
    """
    
    if x is None:
        y, x = Decimal(1), y
    
    xp, yp = x, y
    x2, y2 = x*x, y*y
    
    pos_total, neg_total = Decimal(0), Decimal(0)
    sign = 1
    n = 1
    old_total, total = None, Decimal(0)
    term = Decimal(1)
    while old_total != total:
        old_total = total
        term = yp / xp
        if sign > 0:
            pos_total += term / n
        else:
            neg_total += term / n
        total = pos_total - neg_total
        n += 2
        xp, yp = xp * x2, yp * y2
        sign = -sign
    
    return total


def pi_ascii_art(width: int = None,
                 height: int = None,
                 source_image: str = None,
                 inverted: bool = False,
                 keep_aspect_ratio: bool = False) -> str:
    """Format π as ASCII art."""
    
    if width is None:
        width = DEFAULT_TEXT_WIDTH
    if height is None:
        height = DEFAULT_TEXT_HEIGHT
    if source_image is None:
        source_image = DEFAULT_SOURCE_IMAGE
    
    def need_digit(pixel: int) -> int:
        return 1 if pixel and inverted or not (pixel or inverted) else 0
    
    lines: list[str] = []
    line: list[str] = []
    
    with Image.open(source_image) as image:
        image = image.convert('L')
        image = resize_image(image, width, height,
                             keep_aspect_ratio=keep_aspect_ratio)
        image = image.convert('1')
        pixels = image.getdata()
        num_digits: int = sum(map(need_digit, pixels))
        if num_digits+1 > sys.get_int_max_str_digits():
            sys.set_int_max_str_digits(num_digits+1)
        pi_str: str = compute_pi(num_digits)
        pi_index: int = 0
        num_chars: int = 0
        for pixel in pixels:
            num_chars += 1
            if need_digit(pixel):
                line.append(pi_str[pi_index])
                pi_index += 1
            else:
                line.append(' ')
            if num_chars == width:
                lines.append(''.join(line))
                line = []
                num_chars = 0
    return '\n'.join(line for line in lines if line.strip())
            

def resize_image(image: Image,
                 width: int, height: int = None, *,
                 keep_aspect_ratio: bool = True) -> Image:
        
    image_width, image_height = image.size
    image_aspect_ratio = image_width / image_height

    if height is None:
        height = int(width / image_aspect_ratio)

    if keep_aspect_ratio:
        aspect_ratio = image_aspect_ratio
    else:
        aspect_ratio = width / height
    
    if image_aspect_ratio < aspect_ratio:
        height = int(width / image_aspect_ratio)
    
    resized_image = image.resize((width, height), Image.LANCZOS)
    return resized_image


def main():
    width: int

    success_code: int = 0
    failure_code: int = 1
    
    exit_code: int = failure_code
    
    try:
        opts = get_script_options()
        
        if opts.test_formulas:
            test_formulas()
            exit_code = success_code
        elif opts.test_formula is not None:
            formula: Formula = globals()[opts.test_formula]
            test_formula(formula)
            exit_code = success_code
        else:
            print_pi(opts)
            
    except Exception as e:
        print_exception(e)
    
    return 0


def get_script_options() -> argparse.Namespace:
    """Get the command line options for this script."""
    
    parser = argparse.ArgumentParser(description='Print π to the specified width and height.')
    
    parser.add_argument('-w', '--width',
                        type=int, default=DEFAULT_TEXT_WIDTH,
                        help='The width of the output.')
    parser.add_argument('-l', '--height', '--lines',
                        type=int, default=DEFAULT_TEXT_HEIGHT,
                        help='The height of the output.')
    parser.add_argument('-s', '--source-image',
                        type=str, default=DEFAULT_SOURCE_IMAGE,
                        help='The source image to use.')
    parser.add_argument('-i', '--inverted',
                        action='store_true', default=False,
                        help='Invert the colors.')
    parser.add_argument('-k', '--keep-aspect-ratio',
                        action='store_true', default=False,
                        help='Keep the aspect ratio of the source image.')
    parser.add_argument('-r', '--raw',
                        action='store_true', default=False,
                        help='Print the raw digits of π.  Width specifies '
                             'number of digits.')
    parser.add_argument('--test-formulas',
                        action='store_true', default=False,
                        help='Test the formulas for computing pi.')
    parser.add_argument('--test-formula',
                        type=str, default=None,
                        help='Test the specified formula for computing pi.')

    opts = parser.parse_args()
    return opts


def print_pi(opts: argparse.Namespace) -> None:
    """Print π to the specified width and height."""
    width: int
    height: int
    width, height = opts.width, opts.height
    
    source_image: str = opts.source_image
    
    inverted: bool = opts.inverted
    keep_aspect_ratio: bool = opts.keep_aspect_ratio
    
    raw: bool = opts.raw
    
    if not raw:
        print(pi_ascii_art(width, height, source_image, inverted,
                           keep_aspect_ratio))
    else:
        print(compute_pi(width))


def print_exception(e: Exception, *,
                    message: str = None,
                    file: TextIO = sys.stderr) -> None:

    stack_trace = traceback.format_exc()
    error_message = f"{message}: {e}"
    error_text = f"{error_message}\nStack Trace:\n{stack_trace}"
    print(error_text, file=file)


def test_formulas() -> None:
    """Test the formulas."""
    
    formulas = [
        compute_pi_bbp,
        compute_pi_machin,
        compute_pi_agm,
    ]

    for formula in formulas:
        test_formula(formula)


def test_formula(formula: Formula) -> None:
    expected_last_10_digits = {
        10**1: '1415926535',
        10**2: '3421170679',
        10**3: '2164201989',
        10**4: '5256375678',
        10**5: '5493624646',
    }
    
    for precision, expected in expected_last_10_digits.items():
        pi = compute_pi(precision, formula)
        actual = pi[-10:]
        assert actual == expected, f'Expected {expected}, got {actual} for {formula=} and {precision=}.'
        print(f'Formula {formula.__name__} passed for precision {precision}.')


if __name__ == '__main__':
    exit(main())
