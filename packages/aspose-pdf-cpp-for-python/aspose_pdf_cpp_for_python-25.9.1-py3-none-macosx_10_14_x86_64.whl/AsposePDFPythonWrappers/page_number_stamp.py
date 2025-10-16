import AsposePDFPython
import AsposePDFPythonWrappers.text_stamp
import AsposePDFPythonWrappers.facades.formatted_text

from typing import overload


class PageNumberStamp(AsposePDFPythonWrappers.text_stamp.TextStamp):
    '''Represents page number stamp and used to number pages.'''

    @overload
    def __init__(self):
        '''Initializes a new instance of the :class:`PageNumberStamp` class. Format is set to "#".'''
        ...

    @overload
    def __init__(self, format: str):
        '''Initializes a new instance of the :class:`PageNumberStamp` class.

        :param format: String value used for stamping. See :attr:`PageNumberStamp.format` property for details.'''
        ...

    @overload
    def __init__(self, formatted_text: AsposePDFPythonWrappers.facades.formatted_text.FormattedText):
        '''Creates PageNumberStamp by formatted text.

        :param formatted_text: Formatted text which used to create Page Number Stamp.'''
        ...

    def __init__(self, arg0: None | str | AsposePDFPythonWrappers.facades.formatted_text.FormattedText):
        if arg0 is None:
            super().__init__(AsposePDFPython.page_number_stamp_create())
        elif isinstance(arg0, str):
            super().__init__(AsposePDFPython.page_number_stamp_create_from_format(arg0))
        elif isinstance(arg0, AsposePDFPythonWrappers.facades.formatted_text.FormattedText):
            super().__init__(AsposePDFPython.page_number_stamp_create_from_formated_text(arg0.handle))

    def __del__(self):
        '''Close handle.'''
        super().__del__()

    @property
    def starting_number(self) -> int:
        '''Gets value of the number of starting page. Other pages will be numbered starting from this value.'''
        return AsposePDFPython.page_number_stamp_get_starting_number(self.handle)

    @starting_number.setter
    def starting_number(self, value: int):
        '''Sets value of the number of starting page. Other pages will be numbered starting from this value.'''
        AsposePDFPython.page_number_stamp_set_starting_number(self.handle, value)

    @property
    def format(self) -> str:
        '''String value for stamping page numbers.
        Value must include char '#' which is replaced with the page number in the process of stamping.'''
        return AsposePDFPython.page_number_stamp_get_format(self.handle)

    @format.setter
    def format(self, value: str):
        '''String value for stamping page numbers.
        Value must include char '#' which is replaced with the page number in the process of stamping.'''
        AsposePDFPython.page_number_stamp_set_format(self.handle, str)

    def put(self, page: AsposePDFPythonWrappers.page.Page) -> None:
        '''Adds page number.
        :param page: Page for stamping.'''
        AsposePDFPython.page_number_stamp_put(self.handle, page.handle)

    @property
    def numbering_style(self) -> AsposePDFPython.NumberingStyle:
        '''Numbering style which used by this stamp.'''
        return AsposePDFPython.page_number_stamp_set_numbering_style(self.handle)

    @numbering_style.setter
    def numbering_style(self, value: AsposePDFPython.NumberingStyle):
        '''Numbering style which used by this stamp.'''
        AsposePDFPython.page_number_stamp_set_numbering_style(self.handle, value)