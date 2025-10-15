import AsposePDFPython
import AsposePDFPythonWrappers.text.text_options

from typing import overload


class TextFormattingOptions(AsposePDFPythonWrappers.text.text_options.TextOptions):
    '''Represents text formatting options'''

    @overload
    def __init__(self, wrap_mode: AsposePDFPython.WordWrapMode):
        '''Initializes new instance of the :class:`TextFormattingOptions` object for the specified word wrap mode.

        :param wrap_mode: Word wrap mode.'''
        ...

    @overload
    def __init__(self):
        '''Initializes new instance of the :class:`TextFormattingOptions` object with undefined word wrap mode.'''
        ...

    def __init__(self, arg0: None | AsposePDFPython.WordWrapMode = None):
        if arg0 is None:
            super().__init__(AsposePDFPython.text_text_formatting_options_create())
        elif isinstance(arg0, AsposePDFPython.WordWrapMode):
            super().__init__(AsposePDFPython.text_text_formatting_options_create_from_word_wrap_mode(arg0))
        else:
            raise TypeError("Invalid arguments.")

    @property
    def wrap_mode(self) -> AsposePDFPython.WordWrapMode:
        '''Gets or sets word wrap mode.
        Default value is WordWrapMode.NoWrap'''
        return AsposePDFPython.text_text_formatting_options_get_wrap_mode(self.handle)

    @wrap_mode.setter
    def wrap_mode(self, value: AsposePDFPython.WordWrapMode):
        AsposePDFPython.text_text_formatting_options_set_wrap_mode(self.handle, value)

    @property
    def line_spacing(self) -> AsposePDFPython.LineSpacingMode:
        '''Gets or sets line spacing mode.
        Default value is LineSpacingMode.FontSize'''
        return AsposePDFPython.text_text_formatting_options_get_line_spacing(self.handle)

    @line_spacing.setter
    def line_spacing(self, value: AsposePDFPython.LineSpacingMode):
        AsposePDFPython.text_text_formatting_options_set_line_spacing(self.handle, value)

    @property
    def hyphen_symbol(self) -> str:
        '''Gets or sets hyphen symbol that is used in hyphenation process.

        To eliminate hyphen drawing (with wrapping procedure still in place) please set empty string string.Empty for HyphenSymbol.'''
        return AsposePDFPython.text_text_formatting_options_get_hyphen_symbol(self.handle)

    @hyphen_symbol.setter
    def hyphen_symbol(self, value: str):
        AsposePDFPython.text_text_formatting_options_set_hyphen_symbol(self.handle, value)

    @property
    def subsequent_lines_indent(self) -> float:
        '''Gets or sets subsequent lines indent value.'''
        return AsposePDFPython.text_text_formatting_options_get_subsequent_lines_indent(self.handle)

    @subsequent_lines_indent.setter
    def subsequent_lines_indent(self, value: float):
        AsposePDFPython.text_text_formatting_options_set_subsequent_lines_indent(self.handle, value)

    @property
    def first_line_indent(self) -> float:
        '''Gets or sets first line indent value.'''
        return AsposePDFPython.text_text_formatting_options_get_first_line_indent(self.handle)

    @first_line_indent.setter
    def first_line_indent(self, value: float):
        AsposePDFPython.text_text_formatting_options_set_first_line_indent(self.handle, value)
