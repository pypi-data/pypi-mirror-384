from __future__ import annotations
import AsposePDFPython
from AsposePDFPythonWrappers.sys.drawing.color import Color as SysDrawingColor

from typing import overload


class Color:
    '''Represents class for color value which can be expressed in different color space.'''

    @overload
    def __init__(self):
        '''Default constructor.'''
        ...

    @overload
    def __init__(self, handle: AsposePDFPython.color_handle):
        '''Construct from handle.'''
        ...

    def __init__(self, arg0: AsposePDFPython.color_handle | None = None):
        if isinstance(arg0, AsposePDFPython.color_handle):
            self.handle = arg0
        elif arg0 is None:
            self.handle = AsposePDFPython.color_create()

    @overload
    @staticmethod
    def from_rgb(color: SysDrawingColor) -> Color:
        '''Gets valid pdf Color object from System.Drawing.Color value.

        :param color: System.Drawing.Color value.
        :returns: Color object with each component value in [0..1] range.'''
        ...

    @overload
    @staticmethod
    def from_rgb(r: float, g: float, b: float) -> Color:
        '''Gets valid pdf Color object from RGB color components.

        :param r: The Red color component (value 0 - 1).
        :param g: The Green color component (value 0 - 1).
        :param b: The Blue color component (value 0 - 1).
        :returns: Color object with each component value in [0..1] range.'''
        ...

    @staticmethod
    def from_rgb(a0: SysDrawingColor|float, a1:float | None = None, a2:float | None = None):
        if isinstance(a0, SysDrawingColor):
            return Color(AsposePDFPython.color_from_rgb_drawing_color_handle(a0.handle))
        else:
            return Color(AsposePDFPython.color_from_rgb_double(a0, a1, a2))

    @overload
    @staticmethod
    def from_argb(r: int, g: int, b: int) -> Color:
        '''Gets valid pdf Color object from RGB color components.

        :param r: The Red color component (value 0 - 255).
        :param g: The Green color component (value 0 - 255).
        :param b: The Blue color component (value 0 - 255).
        :returns: Color object with each component value in [0..255] range.'''
        ...

    @overload
    @staticmethod
    def from_argb(a: int, r: int, g: int, b: int) -> Color:
        '''Gets valid pdf Color object from RGB color components.

        :param a: The alpha component value (value 0 - 255).
        :param r: The Red color component (value 0 - 255).
        :param g: The Green color component (value 0 - 255).
        :param b: The Blue color component (value 0 - 255).
        :returns: Color object with each component value in [0..255] range.'''
        ...

    @staticmethod
    def from_argb(a0: int, a1: int, a2: int, a3:int|None = None):
        if a3 is None:
            return Color(AsposePDFPython.sys_drawing_color_from_argb_no_alpha(a0, a1, a2))
        else:
            return Color(AsposePDFPython.color_from_argb(a0, a1, a2, a3))


    @staticmethod
    def parse(self, value: str) -> Color:
        '''Extracts color components from the string.

        :param value: String value with color component values.
        :returns: Color object.'''
        return Color(AsposePDFPython.color_parse(value))

    def to_rgb(self) -> SysDrawingColor:
        '''Converts color into rgb.

        :returns: Rgb color value.'''
        return SysDrawingColor(AsposePDFPython.color_to_rgb(self.handle))

    @staticmethod
    def from_gray(self, g: float) -> Color:
        '''Gets valid pdf Color object from Gray color component.

        :param g: The Gray color component (value 0 - 1).
        :returns: Color object with each component value in [0..1] range.'''
        return Color(AsposePDFPython.color_from_gray(g))

    @staticmethod
    def from_cmyk(self, c: float, m: float, y: float, k: float) -> Color:
        '''Gets valid pdf Color object from RGB color components.

        :param c: The Cyan color component (value 0 - 1).
        :param m: The Magenta color component (value 0 - 1).
        :param y: The Yellow color component (value 0 - 1).
        :param k: The Key color component (value 0 - 1).
        :returns: Color object with each component value in [0..1] range.'''
        return Color(AsposePDFPython.color_from_from_cmyk(c, m, y, k))

    @property
    def a(self) -> float:
        '''Gets the alpha component value'''
        return AsposePDFPython.color_a(self.handle)

    @property
    def data(self) -> list[float]:
        '''Gets color value.'''
        return AsposePDFPython.color_get_data()

    @property
    def color_space(self) -> AsposePDFPython.ColorSpace:
        '''Gets color space that the color represents.'''
        return AsposePDFPython.color_get_color_space(self.handle)

    @property
    def pattern_color_space(self) -> AsposePDFPython.PatternColorSpace:
        '''Represents a object that indicates the pattern colorspace.'''
        return AsposePDFPython.color_get_pattern_color_space(self.handle)

    @pattern_color_space.setter
    def pattern_color_space(self, value: AsposePDFPython.PatternColorSpace):
        AsposePDFPython.color_set_pattern_color_space(self.handle, value)

    @staticmethod
    def transparent() -> Color:
        return Color(AsposePDFPython.color_get_transparent())

    @staticmethod
    def alice_blue() -> Color:
        return Color(AsposePDFPython.color_get_alice_blue())

    @staticmethod
    def antique_white() -> Color:
        return Color(AsposePDFPython.color_get_antique_white())

    @staticmethod
    def aqua() -> Color:
        return Color(AsposePDFPython.color_get_aqua())

    @staticmethod
    def aquamarine() -> Color:
        return Color(AsposePDFPython.color_get_aquamarine())

    @staticmethod
    def azure() -> Color:
        return Color(AsposePDFPython.color_get_azure())

    @staticmethod
    def beige() -> Color:
        return Color(AsposePDFPython.color_get_beige())

    @staticmethod
    def bisque() -> Color:
        return Color(AsposePDFPython.color_get_bisque())

    @staticmethod
    def black() -> Color:
        return Color(AsposePDFPython.color_get_black())

    @staticmethod
    def blanched_almond() -> Color:
        return Color(AsposePDFPython.color_get_blanched_almond())

    @staticmethod
    def blue() -> Color:
        return Color(AsposePDFPython.color_get_blue())

    @staticmethod
    def blue_violet() -> Color:
        return Color(AsposePDFPython.color_get_blue_violet())

    @staticmethod
    def brown() -> Color:
        return Color(AsposePDFPython.color_get_brown())

    @staticmethod
    def burly_wood() -> Color:
        return Color(AsposePDFPython.color_get_burly_wood())

    @staticmethod
    def cadet_blue() -> Color:
        return Color(AsposePDFPython.color_get_cadet_blue())

    @staticmethod
    def chartreuse() -> Color:
        return Color(AsposePDFPython.color_get_chartreuse())

    @staticmethod
    def chocolate() -> Color:
        return Color(AsposePDFPython.color_get_chocolate())

    @staticmethod
    def coral() -> Color:
        return Color(AsposePDFPython.color_get_coral())

    @staticmethod
    def cornflower_blue() -> Color:
        return Color(AsposePDFPython.color_get_cornflower_blue())

    @staticmethod
    def cornsilk() -> Color:
        return Color(AsposePDFPython.color_get_cornsilk())

    @staticmethod
    def crimson() -> Color:
        return Color(AsposePDFPython.color_get_crimson())

    @staticmethod
    def cyan() -> Color:
        return Color(AsposePDFPython.color_get_cyan())

    @staticmethod
    def dark_blue() -> Color:
        return Color(AsposePDFPython.color_get_dark_blue())

    @staticmethod
    def dark_cyan() -> Color:
        return Color(AsposePDFPython.color_get_dark_cyan())

    @staticmethod
    def dark_goldenrod() -> Color:
        return Color(AsposePDFPython.color_get_dark_goldenrod())

    @staticmethod
    def dark_gray() -> Color:
        return Color(AsposePDFPython.color_get_dark_gray())

    @staticmethod
    def dark_green() -> Color:
        return Color(AsposePDFPython.color_get_dark_green())

    @staticmethod
    def dark_khaki() -> Color:
        return Color(AsposePDFPython.color_get_dark_khaki())

    @staticmethod
    def dark_magenta() -> Color:
        return Color(AsposePDFPython.color_get_dark_magenta())

    @staticmethod
    def dark_olive_green() -> Color:
        return Color(AsposePDFPython.color_get_dark_olive_green())

    @staticmethod
    def dark_orange() -> Color:
        return Color(AsposePDFPython.color_get_dark_orange())

    @staticmethod
    def dark_orchid() -> Color:
        return Color(AsposePDFPython.color_get_dark_orchid())

    @staticmethod
    def dark_red() -> Color:
        return Color(AsposePDFPython.color_get_dark_red())

    @staticmethod
    def dark_salmon() -> Color:
        return Color(AsposePDFPython.color_get_dark_salmon())

    @staticmethod
    def dark_sea_green() -> Color:
        return Color(AsposePDFPython.color_get_dark_sea_green())

    @staticmethod
    def dark_slate_blue() -> Color:
        return Color(AsposePDFPython.color_get_dark_slate_blue())

    @staticmethod
    def dark_slate_gray() -> Color:
        return Color(AsposePDFPython.color_get_dark_slate_gray())

    @staticmethod
    def dark_turquoise() -> Color:
        return Color(AsposePDFPython.color_get_dark_turquoise())

    @staticmethod
    def dark_violet() -> Color:
        return Color(AsposePDFPython.color_get_dark_violet())

    @staticmethod
    def deep_pink() -> Color:
        return Color(AsposePDFPython.color_get_deep_pink())

    @staticmethod
    def deep_sky_blue() -> Color:
        return Color(AsposePDFPython.color_get_deep_sky_blue())

    @staticmethod
    def dim_gray() -> Color:
        return Color(AsposePDFPython.color_get_dim_gray())

    @staticmethod
    def dodger_blue() -> Color:
        return Color(AsposePDFPython.color_get_dodger_blue())

    @staticmethod
    def firebrick() -> Color:
        return Color(AsposePDFPython.color_get_firebrick())

    @staticmethod
    def floral_white() -> Color:
        return Color(AsposePDFPython.color_get_floral_white())

    @staticmethod
    def forest_green() -> Color:
        return Color(AsposePDFPython.color_get_forest_green())

    @staticmethod
    def fuchsia() -> Color:
        return Color(AsposePDFPython.color_get_fuchsia())

    @staticmethod
    def gainsboro() -> Color:
        return Color(AsposePDFPython.color_get_gainsboro())

    @staticmethod
    def ghost_white() -> Color:
        return Color(AsposePDFPython.color_get_ghost_white())

    @staticmethod
    def gold() -> Color:
        return Color(AsposePDFPython.color_get_gold())

    @staticmethod
    def goldenrod() -> Color:
        return Color(AsposePDFPython.color_get_goldenrod())

    @staticmethod
    def gray() -> Color:
        return Color(AsposePDFPython.color_get_gray())

    @staticmethod
    def green() -> Color:
        return Color(AsposePDFPython.color_get_green())

    @staticmethod
    def green_yellow() -> Color:
        return Color(AsposePDFPython.color_get_green_yellow())

    @staticmethod
    def honeydew() -> Color:
        return Color(AsposePDFPython.color_get_honeydew())

    @staticmethod
    def hot_pink() -> Color:
        return Color(AsposePDFPython.color_get_hot_pink())

    @staticmethod
    def indian_red() -> Color:
        return Color(AsposePDFPython.color_get_indian_red())

    @staticmethod
    def indigo() -> Color:
        return Color(AsposePDFPython.color_get_indigo())

    @staticmethod
    def ivory() -> Color:
        return Color(AsposePDFPython.color_get_ivory())

    @staticmethod
    def khaki() -> Color:
        return Color(AsposePDFPython.color_get_khaki())

    @staticmethod
    def lavender() -> Color:
        return Color(AsposePDFPython.color_get_lavender())

    @staticmethod
    def lavender_blush() -> Color:
        return Color(AsposePDFPython.color_get_lavender_blush())

    @staticmethod
    def lawn_green() -> Color:
        return Color(AsposePDFPython.color_get_lawn_green())

    @staticmethod
    def lemon_chiffon() -> Color:
        return Color(AsposePDFPython.color_get_lemon_chiffon())

    @staticmethod
    def light_blue() -> Color:
        return Color(AsposePDFPython.color_get_light_blue())

    @staticmethod
    def light_coral() -> Color:
        return Color(AsposePDFPython.color_get_light_coral())

    @staticmethod
    def light_cyan() -> Color:
        return Color(AsposePDFPython.color_get_light_cyan())

    @staticmethod
    def light_goldenrod_yellow() -> Color:
        return Color(AsposePDFPython.color_get_light_goldenrod_yellow())

    @staticmethod
    def light_green() -> Color:
        return Color(AsposePDFPython.color_get_light_green())

    @staticmethod
    def light_gray() -> Color:
        return Color(AsposePDFPython.color_get_light_gray())

    @staticmethod
    def light_pink() -> Color:
        return Color(AsposePDFPython.color_get_light_pink())

    @staticmethod
    def light_salmon() -> Color:
        return Color(AsposePDFPython.color_get_light_salmon())

    @staticmethod
    def light_sea_green() -> Color:
        return Color(AsposePDFPython.color_get_light_sea_green())

    @staticmethod
    def light_sky_blue() -> Color:
        return Color(AsposePDFPython.color_get_light_sky_blue())

    @staticmethod
    def light_slate_gray() -> Color:
        return Color(AsposePDFPython.color_get_light_slate_gray())

    @staticmethod
    def light_steel_blue() -> Color:
        return Color(AsposePDFPython.color_get_light_steel_blue())

    @staticmethod
    def light_yellow() -> Color:
        return Color(AsposePDFPython.color_get_light_yellow())

    @staticmethod
    def lime() -> Color:
        return Color(AsposePDFPython.color_get_lime())

    @staticmethod
    def lime_green() -> Color:
        return Color(AsposePDFPython.color_get_lime_green())

    @staticmethod
    def linen() -> Color:
        return Color(AsposePDFPython.color_get_linen())

    @staticmethod
    def magenta() -> Color:
        return Color(AsposePDFPython.color_get_magenta())

    @staticmethod
    def maroon() -> Color:
        return Color(AsposePDFPython.color_get_maroon())

    @staticmethod
    def medium_aquamarine() -> Color:
        return Color(AsposePDFPython.color_get_medium_aquamarine())

    @staticmethod
    def medium_blue() -> Color:
        return Color(AsposePDFPython.color_get_medium_blue())

    @staticmethod
    def medium_orchid() -> Color:
        return Color(AsposePDFPython.color_get_medium_orchid())

    @staticmethod
    def medium_purple() -> Color:
        return Color(AsposePDFPython.color_get_medium_purple())

    @staticmethod
    def medium_sea_green() -> Color:
        return Color(AsposePDFPython.color_get_medium_sea_green())

    @staticmethod
    def medium_slate_blue() -> Color:
        return Color(AsposePDFPython.color_get_medium_slate_blue())

    @staticmethod
    def medium_spring_green() -> Color:
        return Color(AsposePDFPython.color_get_medium_spring_green())

    @staticmethod
    def medium_turquoise() -> Color:
        return Color(AsposePDFPython.color_get_medium_turquoise())

    @staticmethod
    def medium_violet_red() -> Color:
        return Color(AsposePDFPython.color_get_medium_violet_red())

    @staticmethod
    def midnight_blue() -> Color:
        return Color(AsposePDFPython.color_get_midnight_blue())

    @staticmethod
    def mint_cream() -> Color:
        return Color(AsposePDFPython.color_get_mint_cream())

    @staticmethod
    def misty_rose() -> Color:
        return Color(AsposePDFPython.color_get_misty_rose())

    @staticmethod
    def moccasin() -> Color:
        return Color(AsposePDFPython.color_get_moccasin())

    @staticmethod
    def navajo_white() -> Color:
        return Color(AsposePDFPython.color_get_navajo_white())

    @staticmethod
    def navy() -> Color:
        return Color(AsposePDFPython.color_get_navy())

    @staticmethod
    def old_lace() -> Color:
        return Color(AsposePDFPython.color_get_old_lace())

    @staticmethod
    def olive() -> Color:
        return Color(AsposePDFPython.color_get_olive())

    @staticmethod
    def olive_drab() -> Color:
        return Color(AsposePDFPython.color_get_olive_drab())

    @staticmethod
    def orange() -> Color:
        return Color(AsposePDFPython.color_get_orange())

    @staticmethod
    def orange_red() -> Color:
        return Color(AsposePDFPython.color_get_orange_red())

    @staticmethod
    def orchid() -> Color:
        return Color(AsposePDFPython.color_get_orchid())

    @staticmethod
    def pale_goldenrod() -> Color:
        return Color(AsposePDFPython.color_get_pale_goldenrod())

    @staticmethod
    def pale_green() -> Color:
        return Color(AsposePDFPython.color_get_pale_green())

    @staticmethod
    def pale_turquoise() -> Color:
        return Color(AsposePDFPython.color_get_pale_turquoise())

    @staticmethod
    def pale_violet_red() -> Color:
        return Color(AsposePDFPython.color_get_pale_violet_red())

    @staticmethod
    def papaya_whip() -> Color:
        return Color(AsposePDFPython.color_get_papaya_whip())

    @staticmethod
    def peach_puff() -> Color:
        return Color(AsposePDFPython.color_get_peach_puff())

    @staticmethod
    def peru() -> Color:
        return Color(AsposePDFPython.color_get_peru())

    @staticmethod
    def pink() -> Color:
        return Color(AsposePDFPython.color_get_pink())

    @staticmethod
    def plum() -> Color:
        return Color(AsposePDFPython.color_get_plum())

    @staticmethod
    def powder_blue() -> Color:
        return Color(AsposePDFPython.color_get_powder_blue())

    @staticmethod
    def purple() -> Color:
        return Color(AsposePDFPython.color_get_purple())

    @staticmethod
    def red() -> Color:
        return Color(AsposePDFPython.color_get_red())

    @staticmethod
    def rosy_brown() -> Color:
        return Color(AsposePDFPython.color_get_rosy_brown())

    @staticmethod
    def royal_blue() -> Color:
        return Color(AsposePDFPython.color_get_royal_blue())

    @staticmethod
    def saddle_brown() -> Color:
        return Color(AsposePDFPython.color_get_saddle_brown())

    @staticmethod
    def salmon() -> Color:
        return Color(AsposePDFPython.color_get_salmon())

    @staticmethod
    def sandy_brown() -> Color:
        return Color(AsposePDFPython.color_get_sandy_brown())

    @staticmethod
    def sea_green() -> Color:
        return Color(AsposePDFPython.color_get_sea_green())

    @staticmethod
    def sea_shell() -> Color:
        return Color(AsposePDFPython.color_get_sea_shell())

    @staticmethod
    def sienna() -> Color:
        return Color(AsposePDFPython.color_get_sienna())

    @staticmethod
    def silver() -> Color:
        return Color(AsposePDFPython.color_get_silver())

    @staticmethod
    def sky_blue() -> Color:
        return Color(AsposePDFPython.color_get_sky_blue())

    @staticmethod
    def slate_blue() -> Color:
        return Color(AsposePDFPython.color_get_slate_blue())

    @staticmethod
    def slate_gray() -> Color:
        return Color(AsposePDFPython.color_get_slate_gray())

    @staticmethod
    def snow() -> Color:
        return Color(AsposePDFPython.color_get_snow())

    @staticmethod
    def spring_green() -> Color:
        return Color(AsposePDFPython.color_get_spring_green())

    @staticmethod
    def steel_blue() -> Color:
        return Color(AsposePDFPython.color_get_steel_blue())

    @staticmethod
    def tan() -> Color:
        return Color(AsposePDFPython.color_get_tan())

    @staticmethod
    def teal() -> Color:
        return Color(AsposePDFPython.color_get_teal())

    @staticmethod
    def thistle() -> Color:
        return Color(AsposePDFPython.color_get_thistle())

    @staticmethod
    def tomato() -> Color:
        return Color(AsposePDFPython.color_get_tomato())

    @staticmethod
    def turquoise() -> Color:
        return Color(AsposePDFPython.color_get_turquoise())

    @staticmethod
    def violet() -> Color:
        return Color(AsposePDFPython.color_get_violet())

    @staticmethod
    def wheat() -> Color:
        return Color(AsposePDFPython.color_get_wheat())

    @staticmethod
    def white() -> Color:
        return Color(AsposePDFPython.color_get_white())

    @staticmethod
    def white_smoke() -> Color:
        return Color(AsposePDFPython.color_get_white_smoke())

    @staticmethod
    def yellow() -> Color:
        return Color(AsposePDFPython.color_get_yellow())

    @staticmethod
    def yellow_green() -> Color:
        return Color(AsposePDFPython.color_get_yellow_green())

    @staticmethod
    def empty() -> Color:
        return Color(AsposePDFPython.color_get_empty())
