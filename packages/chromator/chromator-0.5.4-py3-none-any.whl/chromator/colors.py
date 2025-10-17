from collections.abc import Iterator
from functools import cached_property
from math import pi

HSLuv = tuple[float, float, float]


def trim(n: float, lower: float, upper: float):
    return min(max(lower, n), upper)


class Bounds:
    def __init__(self, begin: float, end: float):
        self._begin = begin
        self._end = end

    @cached_property
    def _span(self):
        return self._end - self._begin

    def interpolate(self, f: float):
        return self._begin + self._span * f

    def inverse_interpolate(self, n: float, inside=True):
        try:
            f = (n - self._begin) / self._span
        except ZeroDivisionError:
            return 0.0
        return trim(f, 0.0, 1.0) if inside else f


class CyclicBounds(Bounds):
    def __init__(self, begin: float, end: float, period: float = pi * 2):
        begin, end = begin % period, end % period

        # To ensure interpolation over the smallest angle,
        # phase shift {begin} over whole periods, such that the
        # (absolute) difference between {begin} <-> {end} <= 1/2 {period}.
        #
        #                          v------ period ------v
        #    -1                    0                    1                    2
        #     |                    |                    |     begin < end:   |
        # Old:|                    |   B ~~~~~~~~~> E   |                    |
        # New:|                    |                E <~|~~ B' = B + period  |
        #     |    begin > end:    |                    |                    |
        # Old:|                    |   E <~~~~~~~~~ B   |                    |
        # New:|  B - period =  B'~~|~> E                |                    |

        if abs(end - begin) > period / 2:
            begin += period if begin < end else -period

        super().__init__(begin, end)
        self._period = period

    def interpolate(self, f: float):
        return super().interpolate(f) % self._period

    def inverse_interpolate(self, n: float, inside=True):
        return super().inverse_interpolate(n % self._period, inside)


def contrasting_color(color: HSLuv) -> HSLuv:
    hue, saturation, lightness = color
    return hue, saturation, (lightness + 50) % 100


def shades_1(
    color: HSLuv,
    step: int = 5,
    inclusive: bool = False,
) -> Iterator[HSLuv]:
    hue, saturation, _ = color
    s = step if inclusive else 0
    for lightness in range(step - s, 100 + s, step):
        yield hue, saturation, lightness


def shades_2(
    color_1: HSLuv,
    color_2: HSLuv,
    step: int = 5,
    extrapolate: float = 0,
    inclusive: bool = False,
) -> Iterator[HSLuv]:
    _, _, l_1 = color_1
    _, _, l_2 = color_2
    if l_1 > l_2:
        color_1, color_2 = color_2, color_1
    h_1, s_1, l_1 = color_1
    h_2, s_2, l_2 = color_2

    l_1 = Bounds(l_1, 0).interpolate(extrapolate)
    l_2 = Bounds(l_2, 100).interpolate(extrapolate)

    hue_bounds = CyclicBounds(h_1, h_2, 360)
    saturation_bounds = Bounds(s_1, s_2)
    lightness_bounds = Bounds(l_1, l_2)

    s = step if inclusive else 0
    for lightness in range(step - s, 100 + s, step):
        f = lightness_bounds.inverse_interpolate(lightness)
        hue = hue_bounds.interpolate(f)
        saturation = saturation_bounds.interpolate(f)
        yield hue, saturation, lightness


def shades(
    color_1: HSLuv,
    color_2: HSLuv = None,
    step: int = 5,
    extrapolate: float = 0,
    inclusive: bool = False,
):
    if color_2:
        yield from shades_2(color_1, color_2, step, extrapolate, inclusive)
    else:
        yield from shades_1(color_1, step, inclusive)
