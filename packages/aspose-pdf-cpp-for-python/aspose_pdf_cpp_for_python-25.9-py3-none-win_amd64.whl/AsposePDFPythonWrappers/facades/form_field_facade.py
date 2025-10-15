import AsposePDFPython
import AsposePDFPythonWrappers.sys.drawing.color
import AsposePDFPythonWrappers.sys.drawing.rectangle


class FormFieldFacade:
    ''' Class for representing field properties. '''

    def __init__(self):
        ''' Initializes a new instance of the FormFieldFacade '''
        self.handle = AsposePDFPython.facades_formfieldfacade_create()

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @property
    def border_color(self) -> AsposePDFPythonWrappers.sys.drawing.color.Color:
        ''' Get the color of a field border. '''
        return AsposePDFPythonWrappers.sys.drawing.color.Color(self.handle.facades_formfieldfacade_get_border_color())

    @border_color.setter
    def border_color(self, value : AsposePDFPythonWrappers.sys.drawing.color.Color):
        ''' The color of a field border. '''
        AsposePDFPython.facades_formfieldfacade_set_border_color(self.handle, value.handle)

    @property
    def border_style(self) -> int:
        ''' Get the style of a field border. '''
        return AsposePDFPython.facades_formfieldfacade_get_border_style(self.handle)

    @border_style.setter
    def border_style(self, value: int):
        ''' The style of a field border. '''
        AsposePDFPython.facades_formfieldfacade_set_border_style(self.handle, value)

    @property
    def border_width(self) -> float:
        ''' Get the width of a field border. '''
        return AsposePDFPython.facades_formfieldfacade_get_border_width(self.handle)

    @border_width.setter
    def border_width(self, value: float):
        ''' The width of a field border. '''
        AsposePDFPython.facades_formfieldfacade_set_border_width(self.handle, value)

    @property
    def font(self) -> AsposePDFPython.FontStyle:
        ''' Get the font type of a field text. '''
        return AsposePDFPython.facades_formfieldfacade_get_font(self.handle)

    @font.setter
    def font(self, value: AsposePDFPython.FontStyle):
        ''' The font type of a field text. '''
        AsposePDFPython.facades_formfieldfacade_set_font(self.handle, value.handle)

    @property
    def custom_font(self) -> str:
        ''' Gets name of the font when this is non-standart (other then 14 standard fonts). '''
        return AsposePDFPython.facades_formfieldfacade_get_custom_font(self.handle)

    @custom_font.setter
    def custom_font(self, value: str):
        ''' Sets name of the font when this is non-standart (other then 14 standard fonts). '''
        AsposePDFPython.facades_formfieldfacade_set_custom_font(self.handle, value)

    @property
    def font_size(self) -> float:
        ''' Get the size of a field text. '''
        AsposePDFPython.facades_formfieldfacade_get_font_size(self.handle)

    @font_size.setter
    def font_size(self, value: float):
        ''' The size of a field text. '''
        AsposePDFPython.facades_formfieldfacade_set_font_size(self.handle, value)

    @property
    def text_color(self) -> AsposePDFPythonWrappers.sys.drawing.color.Color:
        ''' Get the color of a field text. '''
        AsposePDFPython.facades_formfieldfacade_get_text_color(self.handle)

    @text_color.setter
    def text_color(self, value: AsposePDFPythonWrappers.sys.drawing.color.Color):
        ''' The color of a field text. '''
        AsposePDFPython.facades_formfieldfacade_set_text_color(self.handle, value.handle)

    @property
    def text_encoding(self) -> AsposePDFPython.EncodingType:
        ''' Get the encoding of a field text. '''
        return AsposePDFPython.facades_formfieldfacade_get_text_encoding(self.handle)

    @text_encoding.setter
    def text_encoding(self, value: AsposePDFPython.EncodingType):
        ''' The encoding of a field text. '''
        AsposePDFPython.facades_formfieldfacade_set_text_encoding(self.handle, value)

    @property
    def alignment(self) -> int:
        ''' Get the alignment of a field text. '''
        return AsposePDFPython.facades_formfieldfacade_get_alignment(self.handle)

    @alignment.setter
    def alignment(self, value: int):
        ''' The alignment of a field text. '''
        AsposePDFPython.facades_formfieldfacade_set_alignment(self.handle, value)

    @property
    def rotation(self) -> int:
        ''' Get the rotation of a field text. '''
        return AsposePDFPython.facades_formfieldfacade_get_rotation(self.handle)

    @rotation.setter
    def rotation(self, value: int):
        ''' The rotation of a field text. '''
        AsposePDFPython.facades_formfieldfacade_set_rotation(self.handle, value)

    @property
    def caption(self) -> str:
        ''' Get the normal caption of form field. '''
        return AsposePDFPython.facades_formfieldfacade_get_caption(self.handle)

    @caption.setter
    def caption(self, value: str):
        ''' The normal caption of form field. '''
        AsposePDFPython.facades_formfieldfacade_set_caption(self.handle, value)

    @property
    def button_style(self) -> int:
        ''' Get the style of check box or radio box field, defined by FormFieldFacade.CheckBoxStyle\*. '''
        return AsposePDFPython.facades_formfieldfacade_get_button_style(self.handle)

    @button_style.setter
    def button_style(self, value: int):
        ''' Set the style of check box or radio box field, defined by FormFieldFacade.CheckBoxStyle\*. '''
        AsposePDFPython.facades_formfieldfacade_set_button_style(self.handle, value)

    @property
    def box(self) -> AsposePDFPythonWrappers.sys.drawing.rectangle.Rectangle:
        ''' Get a rectangle object holding field's location. '''
        return AsposePDFPythonWrappers.sys.drawing.rectangle.Rectangle(AsposePDFPython.facades_formfieldfacade_get_box(self.handle))

    @box.setter
    def box(self, value: AsposePDFPythonWrappers.sys.drawing.rectangle.Rectangle):
        ''' Set a rectangle object holding field's location. '''
        AsposePDFPython.facades_formfieldfacade_set_box(self.handle, value.handle)

    @property
    def position(self) -> list[float]:
        ''' Get the rectangle object holding field's location. '''
        return AsposePDFPython.facades_formfieldfacade_get_position(self.handle)

    @position.setter
    def position(self, value: list[float]):
        ''' Set the rectangle object holding field's location. '''
        AsposePDFPython.facades_formfieldfacade_set_position(self.handle, value)

    @property
    def page_number(self) -> int:
        '''Get an integer value holding the number of page on which field locates.'''
        return AsposePDFPython.facades_formfieldfacade_get_page_number(self.handle)

    @page_number.setter
    def page_number(self, value: int):
        '''Set an integer value holding the number of page on which field locates.'''
        AsposePDFPython.facades_formfieldfacade_set_page_number(self.handle, value)

    @property
    def items(self) -> list[str]:
        '''Get an array of string, each representing an option of a combo box/list/radio box field. '''
        return AsposePDFPython.facades_formfieldfacade_get_items(self.handle)

    @items.setter
    def items(self, value: list[str]):
        ''' Set an array of string, each representing an option of a combo box/list/radio box field. '''
        AsposePDFPython.facades_formfieldfacade_set_items(self.handle, value)

    @property
    def export_items(self) -> list[str]:
        ''' Get the options for adding a list/combo/radio box. '''
        return AsposePDFPython.facades_formfieldfacade_get_export_items(self.handle)

    @export_items.setter
    def export_items(self, value: list[str]):
        ''' Set the options for adding a list/combo/radio box. '''
        AsposePDFPython.facades_formfieldfacade_set_export_items(self.handle, value)

    @property
    def backgroud_color(self) -> AsposePDFPythonWrappers.sys.drawing.color.Color:
        '''Get the color of a field background, default is white.'''
        return AsposePDFPython.facades_formfieldfacade_get_background_color(self.handle)

    @backgroud_color.setter
    def backgroud_color(self, value: AsposePDFPythonWrappers.sys.drawing.color.Color):
        '''Set the color of a field background, default is white.'''
        AsposePDFPython.facades_formfieldfacade_set_background_color(self.handle, value.handle)
