import sys
from decimal import Decimal, localcontext as local_decimal_context

import PIL.Image


DEFAULT_LINE_WIDTH: int = 80


def compute_pi(precision: int = 100) -> str:
    """Compute π to the specified precision using the Bailey-Borwein-Plouffe formula."""
    with local_decimal_context(prec=precision+2):
        pi = Decimal(0)
        precision_scale: int = 10**(precision)
        pi_int: int = 0
        old_pi_int: int = None
        for k in range(precision):
            old_pi_int = pi_int
            term1 = Decimal(4) / Decimal(8*k+1)
            term2 = Decimal(2) / Decimal(8*k+4)
            term3 = Decimal(1) / Decimal(8*k+5)
            term4 = Decimal(1) / Decimal(8*k+6)
            term = term1 - term2 - term3 - term4
            denominator = Decimal(16**k)
            pi += term / denominator
            pi_int = int(pi*precision_scale)
            if pi_int == old_pi_int:
                break
        pi_str = str(pi_int)
                    
        return f'{pi_str[0]}.{pi_str[1:]}'


def pi_ascii_art(width: int = None, *, inverted: bool = True) -> str:
    """Format π as ASCII art."""
    if width is None:
        width = DEFAULT_LINE_WIDTH

    def need_digit(pixel: int) -> int:
        return 1 if pixel and not inverted or not pixel and inverted else 0
    
    lines: list[str] = []
    line: list[str] = []
    with PIL.Image.open('pi.png') as image:
        image = image.convert('L')
        image_width, image_height = image.size
        aspect_ratio = image_width / image_height
        height = int(width / aspect_ratio)
        image = image.resize((width, height))
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
                lines.append(''.join(line).rstrip())
                line = []
                num_chars = 0
    return '\n'.join(lines)
            

def main():
    width: int
    if sys.argv[1:]:
        width = int(sys.argv[1])
    else:
        width = DEFAULT_LINE_WIDTH
    
    print(pi_ascii_art(width))

    return 0


if __name__ == '__main__':
    exit(main())
