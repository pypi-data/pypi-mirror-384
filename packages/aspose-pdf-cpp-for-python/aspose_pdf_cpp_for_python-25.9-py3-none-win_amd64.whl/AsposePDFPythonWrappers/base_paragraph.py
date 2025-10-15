import AsposePDFPython
import AsposePDFPythonWrappers.margin_info
import AsposePDFPythonWrappers.hyperlink


class BaseParagraph:
    '''Represents a abstract base object can be added to the page.'''

    def __init__(self, handle):
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @property
    def vertical_alignment(self) -> AsposePDFPython.VerticalAlignment:
        '''Gets or sets a vertical alignment of paragraph'''
        return AsposePDFPython.base_paragraph_get_vertical_alignment(self.handle)

    @vertical_alignment.setter
    def vertical_alignment(self, value: AsposePDFPython.VerticalAlignment):
        AsposePDFPython.base_paragraph_set_vertical_alignment(self.handle, value)

    @property
    def horizontal_alignment(self) -> AsposePDFPython.HorizontalAlignment:
        '''Gets or sets a horizontal alignment of paragraph'''
        return AsposePDFPython.base_paragraph_get_horizontal_alignment(self.handle)

    @horizontal_alignment.setter
    def horizontal_alignment(self, value: AsposePDFPython.HorizontalAlignment):
        AsposePDFPython.base_paragraph_set_horizontal_alignment(self.handle, value)

    @property
    def margin(self) -> AsposePDFPythonWrappers.margin_info.MarginInfo:
        '''Gets or sets a outer margin for paragraph (for pdf generation)'''
        return AsposePDFPythonWrappers.margin_info.MarginInfo(AsposePDFPython.base_paragraph_get_margin(self.handle))

    @margin.setter
    def margin(self, value: AsposePDFPythonWrappers.margin_info.MarginInfo):
        AsposePDFPython.base_paragraph_set_margin(self.handle, value.handle)

    @property
    def is_first_paragraph_in_column(self) -> bool:
        '''Gets or sets a bool value that indicates whether this paragraph will be at next column.
        Default is false.(for pdf generation)'''
        return AsposePDFPython.base_paragraph_get_is_first_paragraph_in_column(self.handle)

    @is_first_paragraph_in_column.setter
    def is_first_paragraph_in_column(self, value: bool):
        AsposePDFPython.base_paragraph_set_is_first_paragraph_in_column(self.handle, value)

    @property
    def is_kept_with_next(self) -> bool:
        '''Gets or sets a bool value that indicates whether current paragraph remains in the same page along with next paragraph.
        Default is false.(for pdf generation)'''
        return AsposePDFPython.base_paragraph_get_is_kept_with_next(self.handle)

    @is_kept_with_next.setter
    def is_kept_with_next(self, value: bool):
        AsposePDFPython.base_paragraph_set_is_kept_with_next(self.handle, value)

    @property
    def is_in_new_page(self) -> bool:
        '''Gets or sets a bool value that force this paragraph generates at new page.
        Default is false.(for pdf generation)'''
        return AsposePDFPython.base_paragraph_get_is_in_new_page(self.handle)

    @is_in_new_page.setter
    def is_in_new_page(self, value: bool):
        AsposePDFPython.base_paragraph_set_is_in_new_page(self.handle, value)

    @property
    def is_in_line_paragraph(self) -> bool:
        '''Gets or sets a paragraph is inline.
        Default is false.(for pdf generation)'''
        return AsposePDFPython.base_paragraph_get_is_in_new_page(self.handle)

    @is_in_line_paragraph.setter
    def is_in_line_paragraph(self, value: bool):
        AsposePDFPython.base_paragraph_set_is_in_new_page(self.handle, value)

    @property
    def hyperlink(self) -> AsposePDFPythonWrappers.hyperlink.Hyperlink:
        '''Gets or sets the fragment hyperlink(for pdf generator).'''
        return AsposePDFPythonWrappers.hyperlink.Hyperlink( AsposePDFPython.base_paragraph_get_hyperlink(self.handle))

    @hyperlink.setter
    def hyperlink(self, value: AsposePDFPythonWrappers.hyperlink.Hyperlink):
        AsposePDFPython.base_paragraph_set_hyperlink(self.handle, value.handle)

    @property
    def z_index(self) -> int:
        '''Gets a int value that indicates the Z-order of the graph. A graph with larger ZIndex
        will be placed over the graph with smaller ZIndex. ZIndex can be negative. Graph with negative
        ZIndex will be placed behind the text in the page.'''
        return AsposePDFPython.base_paragraph_get_zindex(self.handle)

    @z_index.setter
    def z_index(self, value: int):
        '''Sets a int value that indicates the Z-order of the graph. A graph with larger ZIndex
        will be placed over the graph with smaller ZIndex. ZIndex can be negative. Graph with negative
        ZIndex will be placed behind the text in the page.'''
        AsposePDFPython.base_paragraph_set_zindex(self.handle, value)