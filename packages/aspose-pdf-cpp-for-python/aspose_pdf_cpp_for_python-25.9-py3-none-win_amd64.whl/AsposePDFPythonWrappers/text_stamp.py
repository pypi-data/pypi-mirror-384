import AsposePDFPython
import AsposePDFPythonWrappers.page
import AsposePDFPythonWrappers.stamp

from typing import overload


class TextStamp(AsposePDFPythonWrappers.stamp.Stamp):
    '''Reresents textual stamp.'''

    @overload
    def __init__(self, value: str):
        '''Initializes a new instance of the :class:`TextStamp` class.

        :param value: Stamp value.'''
        ...

    @overload
    def __init__(self, handle: AsposePDFPython.stamp_handle):
        ...

    def __init__(self, arg0: str | AsposePDFPython.stamp_handle):
        if isinstance(arg0,  str):
            super().__init__(AsposePDFPython.text_stamp_create(arg0))
        elif isinstance(arg0, AsposePDFPython.stamp_handle):
            super().__init__(arg0)
        else:
            raise TypeError("Invalid number of arguments.")

    def __del__(self):
        '''Close handle.'''
        super().__del__()

    @property
    def draw(self) -> bool:
        '''This property determines how stamp is drawn on page. If Draw = true stamp is drawn as graphic operators and if draw = false then stamp is drawn as text.'''
        return AsposePDFPython.text_stamp_get_draw(self.handle)

    @draw.setter
    def draw(self, value: bool):
        '''This property determines how stamp is drawn on page. If Draw = true stamp is drawn as graphic operators and if draw = false then stamp is drawn as text.'''
        AsposePDFPython.text_stamp_set_draw(self.handle, value)

    @property
    def treat_y_indent_as_base_line(self) -> bool:
        '''Defines coordinate origin for placing text.
        If TreatYIndentAsBaseLine = true (default when Draw = true) YIndent value will be treated as text base line.
        If TreatYIndentAsBaseLine = false (default when Draw = false) YIndent value will be treated as bottom (descent line) of text.'''
        return AsposePDFPython.text_stamp_get_treat_yindent_as_base_line(self.handle)

    @treat_y_indent_as_base_line.setter
    def treat_y_indent_as_base_line(self, value: bool):
        '''Defines coordinate origin for placing text.
        If TreatYIndentAsBaseLine = true (default when Draw = true) YIndent value will be treated as text base line.
        If TreatYIndentAsBaseLine = false (default when Draw = false) YIndent value will be treated as bottom (descent line) of text.'''
        AsposePDFPython.text_stamp_set_treat_yindent_as_base_line(self.handle, value)

    @property
    def word_wrap(self) -> bool:
        '''Defines word wrap. If this property set to true and Width value specified, text will be broken in the several lines to fit into specified width. Default value: false.'''
        return AsposePDFPython.text_stamp_get_draw(self.handle)

    @word_wrap.setter
    def word_wrap(self, value: bool):
        '''Defines word wrap. If this property set to true and Width value specified, text will be broken in the several lines to fit into specified width. Default value: false.'''
        AsposePDFPython.text_stamp_set_draw(self.handle, value)

    def put(self, page: AsposePDFPythonWrappers.page.Page):
        '''Adds textual stamp on the page.

        :param page: Page for stamping.'''
        AsposePDFPython.text_stamp_put(self.handle, page.handle)