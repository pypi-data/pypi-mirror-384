import AsposePDFPython
import AsposePDFPythonWrappers.text.position
import AsposePDFPythonWrappers.rectangle

class CharInfo:
    '''Represents a character info object.
    Provides character positioning information.'''

    def __init__(self, hanlde: AsposePDFPython.text_char_info_handle):
        '''Create from handle'''
        self.handle = hanlde

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    @property
    def position(self) -> AsposePDFPythonWrappers.text.position.Position:
        '''Gets position of the character.'''
        return AsposePDFPythonWrappers.text.position.Position(AsposePDFPython.text_char_info_get_position(self.handle))

    @property
    def rectangle(self) -> AsposePDFPythonWrappers.rectangle.Rectangle:
        '''Gets rectangle of the character.'''
        return AsposePDFPythonWrappers.text.char_info.CharInfo(AsposePDFPython.text_char_info_get_rectangle(self.handle))
