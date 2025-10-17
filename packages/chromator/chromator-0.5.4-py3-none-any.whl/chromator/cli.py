import argparse
import sys

from hsluv import hex_to_hsluv, hsluv_to_hex
from yachalk import chalk

from .colors import HSLuv, contrasting_color, shades


def colored(color: HSLuv, s: str = None):
    bg_hex = hsluv_to_hex(color)
    fg_hex = hsluv_to_hex(contrasting_color(color))
    return chalk.hex(fg_hex).bg_hex(bg_hex)(s or bg_hex)


def css_color_comment(color: HSLuv):
    hue, saturation, lightness = color
    return f"""
{colored(color)}:
- Hue: {hue:.1f}°
- Saturation: {saturation:.1f}%
- Lightness: {lightness:.1f}%"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("label", type=str)
    parser.add_argument("-c", "--color1", type=str)
    parser.add_argument("-k", "--color2", type=str, default=None)
    parser.add_argument("-s", "--step", type=int, default=5)
    parser.add_argument("-e", "--extrapolate", type=int, default=0)
    parser.add_argument("-i", "--inclusive", action="store_true", default=False)
    args = parser.parse_args()

    c_1 = hex_to_hsluv(f"#{args.color1}")

    if args.color2:
        c_2 = hex_to_hsluv(f"#{args.color2}")
        sys.stdout.write(f"""/*
Based on:
{css_color_comment(c_1)}
{css_color_comment(c_2)}
*/
""")

    else:
        c_2 = None
        sys.stdout.write(f"""/*
Based on:
{css_color_comment(c_1)}
*/
""")

    for h, s, i in shades(c_1, c_2, args.step, args.extrapolate / 100, args.inclusive):
        color_var = f"--{args.label}-{i:02d}: {hsluv_to_hex((h, s, i))};\n"
        sys.stdout.write(colored((h, s, i), color_var))
