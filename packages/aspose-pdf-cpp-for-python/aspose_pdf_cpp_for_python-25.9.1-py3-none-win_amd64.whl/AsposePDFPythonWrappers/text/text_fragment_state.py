import AsposePDFPython
import AsposePDFPythonWrappers.text.text_state
import AsposePDFPythonWrappers.text.text_fragment
import AsposePDFPythonWrappers.rectangle
import AsposePDFPythonWrappers.text.font
import AsposePDFPythonWrappers.color
import AsposePDFPythonWrappers.text.tab_stops
import AsposePDFPythonWrappers.text.text_formatting_options

from typing import overload

class TextFragmentState(AsposePDFPythonWrappers.text.text_state.TextState):
    '''Represents a text state of a text fragment.

    Provides a way to change following properties of the text:
    font (:attr:`TextFragmentState.font` property)
    font size (:attr:`TextFragmentState.font_size` property)
    font style (:attr:`TextFragmentState.font_style` property)
    foreground color (:attr:`TextFragmentState.foreground_color` property)
    background color (:attr:`TextFragmentState.background_color` property)

    Note that changing :class:`TextFragmentState` properties may change inner :attr:`TextFragment.segments` collection because TextFragment is an aggregate object
    and it may rearrange internal segments or merge them into single segment.
    If your requirement is to leave the :attr:`TextFragment.segments` collection unchanged, please change inner segments individually.'''

    @overload
    def __init__(self, handle : AsposePDFPython.text_textstate_handle):
        '''Init from handle.'''
        ...

    @overload
    def __init__(self, fragment):
        '''Initializes new instance of the :class:`TextFragmentState` object with specified :class:`TextFragment` object.
        This :class:`TextFragmentState` initialization is not supported.
        TextFragmentState is only available with :attr:`TextFragment.text_state` property.

        :param fragment: Text fragment object.'''
        ...

    def __init__(self, *args):
        if isinstance(args[0], AsposePDFPython.text_textstate_handle):
            super().__init__(args[0])
        elif isinstance(args[0], AsposePDFPythonWrappers.text.text_fragment.TextFragment):
            super().__init__(AsposePDFPython.text_text_fragment_state_create(args[0].handle))
        else:
            raise "Invalid argument type!"

    def __del__(self):
        super().__del__()

    def apply_changes_from(self, text_state: AsposePDFPythonWrappers.text.text_state.TextState) -> None:
        '''Applies settings from another textState.

        Only those properties will be copied that were changed explicitly.

        :param text_state: Text state object.'''
        super().apply_changes_from(text_state.handle)

    def measure_string(self, str: str) -> float:
        '''Measures the string.

        :param str: The string.
        :returns: Width of the string.'''
        return super().measure_string(str)

    def is_fit_rectangle(self, str: str, rect: AsposePDFPythonWrappers.rectangle.Rectangle) -> bool:
        '''Checks if input string could be placed inside defined rectangle.

        :param str: String to check.
        :param rect: Rectangle to check.
        :returns: True if string fit rectangle; otherwise false.'''
        return AsposePDFPython.text_text_fragment_state_measure_height(self.handle, str, rect.handle)

    @property
    def character_spacing(self) -> float:
        '''Gets or sets character spacing of the text, represented by the :class:`TextFragment` object.'''
        return super(__class__, self).character_spacing

    @character_spacing.setter
    def character_spacing(self, value: float):
        super(__class__, self.__class__).character_spacing.__set__(self, value)

    @property
    def line_spacing(self) -> float:
        '''Gets or sets line spacing of the text.

        Note that the value is not preserved as a text characteristic within the document.
        The LineSpacing property getter works for an object in case it was explicitly set previously with LineSpacing setter for those object.

        The property is used by runtime in context of current generation/modification process.'''
        return super(__class__, self).line_spacing

    @line_spacing.setter
    def line_spacing(self, value: float):
        super(__class__, self.__class__).line_spacing.__set__(self, value)

    @property
    def horizontal_scaling(self) -> float:
        '''Gets or sets horizontal scaling of the text, represented by the :class:`TextFragment` object.'''
        return super(__class__, self).horizontal_scaling

    @horizontal_scaling.setter
    def horizontal_scaling(self, value: float):
        super(__class__, self.__class__).horizontal_scaling.__set__(self, value)

    @property
    def subscript(self) -> bool:
        '''Gets or sets subscript of the text, represented by the :class:`TextFragment` object.'''
        return super(__class__, self).subscript

    @subscript.setter
    def subscript(self, value: bool):
        super(__class__, self.__class__).subscript.__set__(self, value)

    @property
    def superscript(self) -> bool:
        '''Gets or sets superscript of the text, represented by the :class:`TextFragment` object.'''
        return super(__class__, self).superscript

    @superscript.setter
    def superscript(self, value: bool):
        super(__class__, self.__class__).superscript.__set__(self, value)

    @property
    def word_spacing(self) -> float:
        '''Gets or sets word spacing of the text.'''
        return super(__class__, self).word_spacing

    @word_spacing.setter
    def word_spacing(self, value: float):
        super(__class__, self.__class__).word_spacing.__set__(self, value)

    @property
    def invisible(self) -> bool:
        '''Gets or sets invisibility of the text.'''
        return super(__class__, self).invisible

    @invisible.setter
    def invisible(self, value: bool):
        super(__class__, self.__class__).invisible.__set__(self, value)

    @property
    def rendering_mode(self) -> AsposePDFPython.TextRenderingMode:
        '''Gets or sets rendering mode of the text.'''
        return super(__class__, self).rendering_mode

    @rendering_mode.setter
    def rendering_mode(self, value: AsposePDFPython.TextRenderingMode):
        super(__class__, self.__class__).rendering_mode.__set__(self, value)

    @property
    def font_size(self) -> float:
        '''Gets or sets font size of the text, represented by the :class:`TextFragment` object'''
        return super(__class__, self).font_size

    @font_size.setter
    def font_size(self, value: float):
        super(__class__, self.__class__).font_size.__set__(self, value)

    @property
    def font(self) -> AsposePDFPythonWrappers.text.font.Font:
        '''Gets or sets font of the text, represented by the :class:`TextFragment` object'''
        return super(__class__, self).font

    @font.setter
    def font(self, value: AsposePDFPythonWrappers.text.font.Font):
        super(__class__, self.__class__).font.__set__(self, value)

    @property
    def foreground_color(self) -> AsposePDFPythonWrappers.color.Color:
        '''Gets or sets foreground color of the text, represented by the :class:`TextFragment` object'''
        return super(__class__, self).foreground_color

    @foreground_color.setter
    def foreground_color(self, value: AsposePDFPythonWrappers.color.Color):
        super(__class__, self.__class__).foreground_color.__set__(self, value)

    @property
    def stroking_color(self) -> AsposePDFPythonWrappers.color.Color:
        '''Gets or sets color stroking operations of :class:`TextFragment` rendering (stroke text, rectangle border)'''
        return super(__class__, self).stroking_color

    @stroking_color.setter
    def stroking_color(self, value: AsposePDFPythonWrappers.color.Color):
        super(__class__, self.__class__).stroking_color.__set__(self, value)

    @property
    def underline(self) -> bool:
        '''Gets or sets underline for the text, represented by the :class:`TextFragment` object'''
        return super(__class__, self).underline

    @underline.setter
    def underline(self, value: bool):
        super(__class__, self.__class__).underline.__set__(self, value)

    @property
    def strike_out(self) -> bool:
        '''Sets strikeout for the text, represented by the :class:`TextFragment` object'''
        return super(__class__, self).strike_out

    @strike_out.setter
    def strike_out(self, value: bool):
        super(__class__, self.__class__).strike_out.__set__(self, value)

    @property
    def background_color(self) -> AsposePDFPythonWrappers.color.Color:
        '''Sets background color of the text, represented by the :class:`TextFragment` object'''
        return super(__class__, self).background_color

    @background_color.setter
    def background_color(self, value: AsposePDFPythonWrappers.color.Color):
        super(__class__, self.__class__).background_color.__set__(self, value)

    @property
    def font_style(self) -> AsposePDFPython.FontStyles:
        '''Sets font style of the text, represented by the :class:`TextFragment` object'''
        return super(__class__, self).font_style

    @font_style.setter
    def font_style(self, value: AsposePDFPython.FontStyles):
        super(__class__, self.__class__).font_style.__set__(self, value)

    @property
    def horizontal_alignment(self) -> AsposePDFPython.HorizontalAlignment:
        '''Gets or sets horizontal alignment for the text.

        HorizontalAlignment.None is equal to HorizontalAlignment.Left.

        Note that TextFragmentState.VerticalAlignment property works in new document generation scenarios only.'''
        return super(__class__, self).horizontal_alignment

    @horizontal_alignment.setter
    def horizontal_alignment(self, value: AsposePDFPython.HorizontalAlignment):
        super(__class__, self.__class__).horizontal_alignment.__set__(self, value)

    @property
    def tab_stops(self) -> AsposePDFPythonWrappers.text.tab_stops.TabStops:
        '''Gets tabstops for the text.

        Note that Tabstops property works in new document generation scenarios only.
        Tabstops may be added during :class:`TextFragment` initialization. Tabstops must be constructed before the text.'''
        return AsposePDFPythonWrappers.text.tab_stops.TabStops(AsposePDFPython.text_text_fragment_state_get_tab_stops(self.handle))

    @property
    def formatting_options(self) -> AsposePDFPythonWrappers.text.text_formatting_options.TextFormattingOptions:
        '''Gets or sets formatting options.
        Setting of the options will be effective in generator scenarios only.'''
        return AsposePDFPythonWrappers.text.text_formatting_options.TextFormattingOptions(AsposePDFPython.text_text_fragment_state_get_formatting_options(self.handle))

    @formatting_options.setter
    def formatting_options(self, value: AsposePDFPythonWrappers.text.text_formatting_options.TextFormattingOptions):
        AsposePDFPython.text_text_fragment_state_set_formatting_options(self.handle, value.handle)

    @property
    def rotation(self) -> float:
        '''Gets or sets rotation angle in degrees.'''
        return AsposePDFPython.text_text_fragment_state_get_rotation(self.handle)

    @rotation.setter
    def rotation(self, value: float):
        AsposePDFPython.AsposePDFPython.text_text_fragment_state_set_rotation(self.handle, value)

    @property
    def draw_text_rectangle_border(self) -> bool:
        '''Gets or sets if text rectangle border drawn flag.'''
        return AsposePDFPython.text_text_fragment_state_get_draw_text_rectangle_border(self.handle)

    @draw_text_rectangle_border.setter
    def draw_text_rectangle_border(self, value: bool):
        AsposePDFPython.text_text_fragment_state_set_draw_text_rectangle_border(self.handle, value)
