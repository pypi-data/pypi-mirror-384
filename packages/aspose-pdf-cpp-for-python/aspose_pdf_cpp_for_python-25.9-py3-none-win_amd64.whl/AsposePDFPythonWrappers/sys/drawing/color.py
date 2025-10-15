from __future__ import annotations
import AsposePDFPython

from typing import overload

class Color:
    '''Represents an ARGB color.'''

    def __init__(self, handle: AsposePDFPython.sys_drawing_color_handle):
        '''Constructs instance of Color class from handle.'''
        ...

    def __init__(self):
        '''Constructs an "empty" instance of Color class that does not represent any color.'''
        ...

    def __init__(self, *args):
        if len(args) == 1:
            self.handle = AsposePDFPython.sys_drawing_color_create();
        else:
            self.handle = args[0]

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    @property
    def a(self) -> int:
        '''Gets the alpha component value.'''
        return AsposePDFPython.sys_drawing_color_get_a(self.handle)

    @property
    def r(self) -> int:
        '''Gets the red component value.'''
        return AsposePDFPython.sys_drawing_color_get_r(self.handle)

    @property
    def g(self) -> int:
        '''Gets the green component value.'''
        return AsposePDFPython.sys_drawing_color_get_g(self.handle)

    @property
    def b(self) -> int:
        '''Gets the blue component value.'''
        return  AsposePDFPython.sys_drawing_color_get_b(self.handle)

    @property
    def name(self) -> str:
        '''Gets the name of this Color.'''
        return AsposePDFPython.sys_drawing_color_get_name(self.handle)

    @property
    def is_empty(self) -> bool:
        '''Returns True if this is uninitialized color.'''
        return AsposePDFPython.sys_drawing_color_is_empty(self.handle)

    @staticmethod
    def empty()-> Color:
        '''An "empty" instance of Color class i.e. an instance that does not represent any color.'''
        return Color(AsposePDFPython.sys_drawing_color_empty())

    @staticmethod
    def alice_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_blue())

    @staticmethod
    def antique_white() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_antique_white())

    @staticmethod
    def aqua() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_aqua())

    @staticmethod
    def aquamarine() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_aquamarine())

    @staticmethod
    def azure() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_azure())

    @staticmethod
    def beige() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_beige())

    @staticmethod
    def bisque() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_bisque())

    @staticmethod
    def black() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_black())

    @staticmethod
    def blanched_almond() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_blanched_almond())

    @staticmethod
    def blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_blue())

    @staticmethod
    def blue_violet() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_blue_violet())

    @staticmethod
    def brown() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_brown())

    @staticmethod
    def burly_wood() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_burly_wood())

    @staticmethod
    def cadet_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_cadet_blue())

    @staticmethod
    def chartreuse() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_chartreuse())

    @staticmethod
    def chocolate() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_chocolate())

    @staticmethod
    def coral() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_coral())

    @staticmethod
    def cornflower_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_cornflower_blue())

    @staticmethod
    def cornsilk() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_cornsilk())

    @staticmethod
    def crimson() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_crimson())

    @staticmethod
    def cyan() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_cyan())

    @staticmethod
    def dark_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_blue())

    @staticmethod
    def dark_cyan() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_cyan())

    @staticmethod
    def dark_goldenrod() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_goldenrod())

    @staticmethod
    def dark_gray() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_gray())

    @staticmethod
    def dark_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_green())

    @staticmethod
    def dark_khaki() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_khaki())

    @staticmethod
    def dark_magenta() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_magenta())

    @staticmethod
    def dark_olive_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_olive_green())

    @staticmethod
    def dark_orange() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_orange())

    @staticmethod
    def dark_orchid() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_orchid())

    @staticmethod
    def dark_red() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_red())

    @staticmethod
    def dark_salmon() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_salmon())

    @staticmethod
    def dark_sea_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_sea_green())

    @staticmethod
    def dark_slate_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_slate_blue())

    @staticmethod
    def dark_slate_gray() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_slate_gray())

    @staticmethod
    def dark_turquoise() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_turquoise())

    @staticmethod
    def dark_violet() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dark_violet())

    @staticmethod
    def deep_pink() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_deep_pink())

    @staticmethod
    def deep_sky_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_deep_sky_blue())

    @staticmethod
    def dim_gray() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dim_gray())

    @staticmethod
    def dodger_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_dodger_blue())

    @staticmethod
    def firebrick() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_firebrick())

    @staticmethod
    def floral_white() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_floral_white())

    @staticmethod
    def forest_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_forest_green())

    @staticmethod
    def fuchsia() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_fuchsia())

    @staticmethod
    def gainsboro() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_gainsboro())

    @staticmethod
    def ghost_white() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_ghost_white())

    @staticmethod
    def gold() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_gold())

    @staticmethod
    def goldenrod() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_goldenrod())

    @staticmethod
    def gray() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_gray())

    @staticmethod
    def green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_green())

    @staticmethod
    def green_yellow() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_green_yellow())

    @staticmethod
    def honeydew() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_honeydew())

    @staticmethod
    def hot_pink() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_hot_pink())

    @staticmethod
    def indian_red() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_indian_red())

    @staticmethod
    def indigo() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_indigo())

    @staticmethod
    def ivory() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_ivory())

    @staticmethod
    def khaki() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_khaki())

    @staticmethod
    def lavender() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_lavender())

    @staticmethod
    def lavender_blush() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_lavender_blush())

    @staticmethod
    def lawn_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_lawn_green())

    @staticmethod
    def lemon_chiffon() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_lemon_chiffon())

    @staticmethod
    def light_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_blue())

    @staticmethod
    def light_coral() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_coral())

    @staticmethod
    def light_cyan() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_cyan())

    @staticmethod
    def light_goldenrod_yellow() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_goldenrod_yellow())

    @staticmethod
    def light_gray() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_gray())

    @staticmethod
    def light_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_green())

    @staticmethod
    def light_pink() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_pink())

    @staticmethod
    def light_salmon() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_salmon())

    @staticmethod
    def light_sea_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_sea_green())

    @staticmethod
    def light_sky_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_sky_blue())

    @staticmethod
    def light_slate_gray() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_slate_gray())

    @staticmethod
    def light_steel_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_steel_blue())

    @staticmethod
    def light_yellow() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_light_yellow())

    @staticmethod
    def lime() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_lime())

    @staticmethod
    def lime_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_lime_green())

    @staticmethod
    def linen() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_linen())

    @staticmethod
    def magenta() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_magenta())

    @staticmethod
    def maroon() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_maroon())

    @staticmethod
    def medium_aquamarine() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_aquamarine()
                     )
    @staticmethod
    def medium_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_blue())

    @staticmethod
    def medium_orchid() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_orchid())

    @staticmethod
    def medium_purple() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_purple())

    @staticmethod
    def medium_sea_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_sea_green())

    @staticmethod
    def medium_slate_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_slate_blue())

    @staticmethod
    def medium_spring_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_spring_green())

    @staticmethod
    def medium_turquoise() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_turquoise())

    @staticmethod
    def medium_violet_red() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_medium_violet_red())

    @staticmethod
    def midnight_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_midnight_blue())

    @staticmethod
    def mint_cream() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_mint_cream())

    @staticmethod
    def misty_rose() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_misty_rose())

    @staticmethod
    def moccasin() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_moccasin())

    @staticmethod
    def navajo_white() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_navajo_white())

    @staticmethod
    def navy() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_navy())

    @staticmethod
    def old_lace() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_old_lace())

    @staticmethod
    def olive() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_olive())

    @staticmethod
    def olive_drab() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_olive_drab())

    @staticmethod
    def orange() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_orange())

    @staticmethod
    def orange_red() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_orange_red())

    @staticmethod
    def orchid() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_orchid())

    @staticmethod
    def pale_goldenrod() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_pale_goldenrod())

    @staticmethod
    def pale_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_pale_green())

    @staticmethod
    def pale_turquoise() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_pale_turquoise())

    @staticmethod
    def pale_violet_red() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_pale_violet_red())

    @staticmethod
    def papaya_whip() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_papaya_whip())

    @staticmethod
    def peach_puff() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_peach_puff())

    @staticmethod
    def peru() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_peru())

    @staticmethod
    def pink() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_pink())

    @staticmethod
    def plum() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_plum())

    @staticmethod
    def powderblue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_powder_blue())

    @staticmethod
    def purple() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_purple())

    @staticmethod
    def red() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_red())

    @staticmethod
    def rosy_brown() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_rosy_brown())

    @staticmethod
    def royal_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_royal_blue())

    @staticmethod
    def saddle_brown() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_saddle_brown())

    @staticmethod
    def salmon() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_salmon())

    @staticmethod
    def sandy_brown() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_sandy_brown())

    @staticmethod
    def sea_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_sea_green())

    @staticmethod
    def sea_shell() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_sea_shell())

    @staticmethod
    def sienna() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_sienna())

    @staticmethod
    def silver() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_silver())

    @staticmethod
    def sky_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_sky_blue())

    @staticmethod
    def slate_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_slate_blue())

    @staticmethod
    def slate_gray() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_slate_gray())

    @staticmethod
    def snow() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_snow())

    @staticmethod
    def spring_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_spring_green())

    @staticmethod
    def steel_blue() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_steel_blue())

    @staticmethod
    def tan() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_tan())

    @staticmethod
    def teal() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_teal())

    @staticmethod
    def thistle() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_thistle())

    @staticmethod
    def tomato() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_tomato())

    @staticmethod
    def transparent() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_transparent())

    @staticmethod
    def turquoise() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_turquoise())

    @staticmethod
    def violet() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_violet())

    @staticmethod
    def wheat() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_wheat())

    @staticmethod
    def white() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_white())

    @staticmethod
    def white_smoke() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_white_smoke())

    @staticmethod
    def yellow() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_yellow())

    @staticmethod
    def yellow_green() -> Color:
        return Color(AsposePDFPython.sys_drawing_color_get_yellow_green())

    @overload
    @staticmethod
    def from_argb(value: int) -> Color:
        '''Creates a Color from a 32-bit ARGB value.'''
        return Color(AsposePDFPython.sys_drawing_color_from_argb(value))

    @overload
    @staticmethod
    def from_argb(aplha: int, color: Color) -> Color:
        '''Creates a Color from the specified color with the new alpha value.'''
        return Color(AsposePDFPython.sys_drawing_color_from_argb_and_color_handle(aplha, color.handle))

    @overload
    @staticmethod
    def from_argb(red: int, green: int, blue: int) -> Color:
        '''Creates a Color from the specified red, green, and blue components.'''
        return Color(AsposePDFPython.sys_drawing_color_from_argb_no_alpha(red, green, blue))

    @overload
    @staticmethod
    def from_argb(alpha: int, red: int, green: int, blue: int) -> Color:
        '''Creates a Color from the specified alpha, red, green, and blue components.'''
        return Color(AsposePDFPython.sys_drawing_color_from_argb(alpha, red, green, blue))

    @staticmethod
    def from_known_color(color: AsposePDFPython.KnownColor) -> Color:
        '''Creates a Color from the specified predefined color.'''
        return Color(AsposePDFPython.sys_drawing_color_from_known_color(color))

    @staticmethod
    def from_name(name: str) -> Color:
        '''Creates a Color with the specified name.'''
        return Color(AsposePDFPython.sys_drawing_color_from_name(str))

    def get_brightness(self) -> float:
        '''Gets the HSL lightness value.'''
        return AsposePDFPython.sys_drawing_color_get_brightness(self.handle)

    def to_argb(self) -> int:
        '''Gets the ARGB value.'''
        return AsposePDFPython.sys_drawing_color_to_argb(self.handle)
