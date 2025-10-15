from __future__ import annotations
import AsposePDFPython
import AsposePDFPythonWrappers.sys.drawing.color
import AsposePDFPythonWrappers.text.font
import AsposePDFPythonWrappers.color

from typing import overload


class TextState:
    '''Represents a text state of a text'''

    @overload
    def __init__(self):
        '''Creates text state object.'''
        ...

    @overload
    def __init__(self, handle: AsposePDFPython.text_textstate_handle):
        '''Crate from handle'''
        ...

    @overload
    def __init__(self, font_size: float):
        '''Creates text state object with font size specification.

        :param font_size: Font size.'''
        ...

    @overload
    def __init__(self, foreground_color: AsposePDFPythonWrappers.sys.drawing.color.Color):
        '''Creates text state object with foreground color specification.

        :param foreground_color: Foreground color.'''
        ...

    @overload
    def __init__(self, foreground_color: AsposePDFPythonWrappers.sys.drawing.color.Color, font_size: float):
        '''Creates text state object with foreground color and font size specification.

        :param foreground_color: Foreground color.
        :param font_size: Font size.'''
        ...

    @overload
    def __init__(self, font_family: str):
        '''Creates text state object with font family specification.

        :param font_family: Font family.'''
        ...

    @overload
    def __init__(self, font_family: str, bold: bool, italic: bool):
        '''Creates text state object with font family and font style specification.

        :param font_family: Font family.
        :param bold: Bold font style.
        :param italic: Italic font style.'''
        ...

    @overload
    def __init__(self, font_family: str, font_size: float):
        '''Creates text state object with font family and font size specification.

        :param font_family: Font family.
        :param font_size: Font size.'''
        ...

    def __init__(self, arg0: float | AsposePDFPythonWrappers.sys.drawing.color.Color | str | AsposePDFPython.text_textstate_handle | None = None
                     , arg1: float | bool | None = None
                     , arg2: bool | None = None):
        if arg0 is None and arg1 is None and arg2 is None:
            self.handle = AsposePDFPython.text_text_state_create()
        elif isinstance(arg0, float) and arg1 is None and arg2 is None:
            self.handle = AsposePDFPython.text_text_state_create_from_font_size(arg0)
        elif isinstance(arg0, AsposePDFPythonWrappers.sys.drawing.color.Color) and arg1 is None and arg2 is None:
            self.handle = AsposePDFPython.text_text_state_create_from_foreground_color(arg0.handle)
        elif isinstance(arg0, AsposePDFPython.text_textstate_handle) and arg1 is None and arg2 is None:
            self.handle = arg0
        elif isinstance(arg0, AsposePDFPythonWrappers.sys.drawing.color.Color) and isinstance(arg1, float) and arg2 is None:
            self.handle = AsposePDFPython.text_text_state_create_from_foreground_color_and_font_size(arg0.handle, arg2)
        elif isinstance(arg0, str) and arg1 is None and arg2 is None:
            self.handle = AsposePDFPython.text_text_state_create_from_font_family(arg0)
        elif isinstance(arg0, str) and isinstance(arg1, bool) and isinstance(arg2, bool):
            self.handle = AsposePDFPython.text_text_state_create_from_font_family_and_style(arg0, arg1, arg2)
        elif isinstance(arg0, str) and isinstance(arg1, float) and arg2 is None:
            self.handle = AsposePDFPython.text_text_state_create_from_font_family_and_font_size(arg0, arg1)
        else:
            raise TypeError("Invalid arguments.")

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    def apply_changes_from(self, text_state: TextState) -> None:
        '''Applies settings from another textState.

        Only those properties will be copied that were changed explicitly.

        :param text_state: Text state object.'''
        AsposePDFPython.text_text_state_apply_changes_from(self.handle, text_state.handle)

    def measure_string(self, str: str) -> float:
        '''Measures the string.

        :param str: The string.
        :returns: Width of the string represented with this text state.'''
        return AsposePDFPython.text_text_state_measure_string(self.handle, str)

    @property
    def character_spacing(self) -> float:
        '''Gets or sets character spacing of the text.'''
        return AsposePDFPython.text_text_state_get_character_spacing(self.handle)

    @character_spacing.setter
    def character_spacing(self, value: float):
        AsposePDFPython.text_text_state_set_character_spacing(self.handle, value)

    @property
    def line_spacing(self) -> float:
        '''Gets or sets line spacing of the text.

        Note that the value is not preserved as a text characteristic within the document.
        The LineSpacing property getter works for an object in case it was explicitly set previously with LineSpacing setter for those object.

        The property is used by runtime in context of current generation/modification process.'''
        return AsposePDFPython.text_text_state_get_line_spacing(self.handle)

    @line_spacing.setter
    def line_spacing(self, value: float):
        AsposePDFPython.text_text_state_set_line_spacing(self.handle, value)

    @property
    def horizontal_scaling(self) -> float:
        '''Gets or sets horizontal scaling of the text.'''
        return AsposePDFPython.text_text_state_get_horizontal_scaling(self.handle)

    @horizontal_scaling.setter
    def horizontal_scaling(self, value: float):
        AsposePDFPython.text_text_state_set_horizontal_scaling(self.handle, value)

    @property
    def subscript(self) -> bool:
        '''Gets or sets subscript of the text.'''
        return AsposePDFPython.text_text_state_get_subscript(self.handle)

    @subscript.setter
    def subscript(self, value: bool):
        AsposePDFPython.text_text_state_set_subscript(self.handle, value)

    @property
    def superscript(self) -> bool:
        '''Gets or sets superscript of the text.'''
        return AsposePDFPython.text_text_state_get_subscript(self.handle)

    @superscript.setter
    def superscript(self, value: bool):
        AsposePDFPython.text_text_state_set_superscript(self.handle, value)

    @property
    def word_spacing(self) -> float:
        '''Gets or sets word spacing of the text.'''
        return AsposePDFPython.text_text_state_get_word_spacing(self.handle)

    @word_spacing.setter
    def word_spacing(self, value: float):
        AsposePDFPython.text_text_state_set_word_spacing(self.handle, value)

    @property
    def invisible(self) -> bool:
        '''Gets or sets the invisibility of text. This basically reflects the :attr:`TextState.rendering_mode` state, except for some special cases (like clipping).'''
        return AsposePDFPython.text_text_state_get_invisible(self.handle)

    @invisible.setter
    def invisible(self, value: bool):
        AsposePDFPython.text_text_state_set_invisible(self.handle, value)

    @property
    def rendering_mode(self) -> AsposePDFPython.TextRenderingMode:
        '''Gets or sets rendering mode of text.'''
        return AsposePDFPython.text_text_state_get_rendering_mode(self.handle)

    @rendering_mode.setter
    def rendering_mode(self, value: AsposePDFPython.TextRenderingMode):
        AsposePDFPython.text_text_state_set_rendering_mode(self.handle, value)

    @property
    def font_size(self) -> float:
        '''Gets or sets font size of the text.'''
        return AsposePDFPython.text_text_state_get_font_size(self.handle)

    @font_size.setter
    def font_size(self, value: float):
        AsposePDFPython.text_text_state_set_font_size(self.handle, value)

    @property
    def font(self) -> AsposePDFPythonWrappers.text.font.Font:
        '''Gets or sets font of the text.'''
        return AsposePDFPythonWrappers.text.font.Font(AsposePDFPython.text_text_state_get_font(self.handle))

    @font.setter
    def font(self, value: AsposePDFPythonWrappers.text.font.Font):
        AsposePDFPython.text_text_state_set_font(self.handle, value.handle)

    @property
    def foreground_color(self) -> AsposePDFPythonWrappers.color.Color:
        '''Gets or sets foreground color of the text.'''
        return AsposePDFPythonWrappers.color.Color(AsposePDFPython.text_text_state_get_foreground_color(self.handle))

    @foreground_color.setter
    def foreground_color(self, value: AsposePDFPythonWrappers.color.Color):
        AsposePDFPython.text_text_state_set_foreground_color(self.handle, value.handle)

    @property
    def stroking_color(self) -> AsposePDFPythonWrappers.color.Color:
        '''Gets or sets foreground color of the text.'''
        return AsposePDFPythonWrappers.color.Color(AsposePDFPython.text_text_state_get_stroking_color(self.handle))

    @stroking_color.setter
    def stroking_color(self, value: AsposePDFPythonWrappers.color.Color):
        AsposePDFPython.text_text_state_set_stroking_color(self.handle, value.handle)

    @property
    def underline(self) -> bool:
        '''Gets or sets underline for the text, represented by the :class:`TextFragment` object'''
        return AsposePDFPython.text_text_state_get_underline(self.handle)

    @underline.setter
    def underline(self, value: bool):
        AsposePDFPython.text_text_state_set_underline(self.handle, value)

    @property
    def strike_out(self) -> bool:
        '''Sets strikeout for the text, represented by the :class:`TextFragment` object'''
        return AsposePDFPython.text_text_state_get_strike_out(self.handle);

    @strike_out.setter
    def strike_out(self, value: bool):
        AsposePDFPython.text_text_state_set_strike_out(self.handle, value)

    @property
    def background_color(self) -> AsposePDFPythonWrappers.color.Color:
        '''Sets background color of the text.

        Note that the value is not preserved as a text characteristic within the document.
        The BackgroundColor property getter works for an object in case it was explicitly set previously with BackgroundColor setter for those object.

        The property is used by runtime in context of current generation/modification process.'''
        return AsposePDFPythonWrappers.color.Color(AsposePDFPython.text_text_state_get_background_color(self.handle))

    @background_color.setter
    def background_color(self, value: AsposePDFPythonWrappers.color.Color):
        AsposePDFPython.text_text_state_set_background_color(self.handle, value.handle)

    @property
    def font_style(self) -> AsposePDFPython.FontStyles:
        '''Sets font style of the text.'''
        return AsposePDFPython.text_text_state_get_font_style(self.handle)

    @font_style.setter
    def font_style(self, value: AsposePDFPython.FontStyles):
        AsposePDFPython.text_text_state_set_font_style(self.handle, value)

    @property
    def horizontal_alignment(self) -> AsposePDFPython.HorizontalAlignment:
        '''Gets or sets horizontal alignment for the text.

        HorizontalAlignment.None is equal to HorizontalAlignment.Left.

        Note that TextState.HorizontalAlignment property works in new document generation scenarios only.'''
        return AsposePDFPython.text_text_state_get_horizontal_alignment(self.handle)

    @horizontal_alignment.setter
    def horizontal_alignment(self, value: AsposePDFPython.HorizontalAlignment):
        AsposePDFPython.text_text_state_set_horizontal_alignment(self.handle, value)

    @property
    def TAB_TAG(self) -> str:
        '''You can place this tag in text to declare tabulation.

        It has effect only in couple with :class:`TabStops`.'''
        return AsposePDFPython.text_text_state_get_tab_tag(self.handle)

    @property
    def TABSTOP_DEFAULT_VALUE(self) -> float:
        '''Default value of tabulation in widths of space character of default font.'''
        return AsposePDFPython.text_text_state_get_tabstop_default_value(self.handle)
