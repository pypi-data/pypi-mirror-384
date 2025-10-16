import AsposePDFPython
import AsposePDFPythonWrappers.paragraphs
import AsposePDFPythonWrappers.text.text_state

from typing import overload


class Note:
    '''This class represents generator paragraph note.'''

    @overload
    def __init__(self, handle: AsposePDFPython.note_handle):
        '''Init from handle'''
        ...

    @overload
    def __init__(self):
        '''Initializes a new instance of the :class:`Note` class.'''
        ...

    @overload
    def __init__(self, content: str):
        '''Initializes a new instance of the :class:`Note` class.

        :param content: The note content.'''
        ...

    def __init__(self, arg0: AsposePDFPython.note_handle | str | None):
        if isinstance(arg0, AsposePDFPython.note_handle):
            self.handle = arg0
        elif isinstance(arg0, str):
            self.handle = AsposePDFPython.note_create_from_string(arg0)
        elif arg0 is None:
            self.handle = AsposePDFPython.note_create()
        else:
            raise TypeError("Invalid arguments.")

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    @property
    def paragraphs(self) -> AsposePDFPythonWrappers.paragraphs.Paragraphs:
        '''Gets or sets a collection that indicates all paragraphs in the FootNote.'''
        return AsposePDFPythonWrappers.paragraphs.Paragraphs(AsposePDFPython.note_get_paragraphs(self.handle))

    @paragraphs.setter
    def paragraphs(self, value: AsposePDFPythonWrappers.paragraphs.Paragraphs):
        AsposePDFPython.note_set_paragraphs(self.handle, value.handle)

    @property
    def text(self) -> str:
        '''Gets or sets a note text.'''
        return AsposePDFPython.note_get_text(self.handle)

    @text.setter
    def text(self, value: str):
        AsposePDFPython.note_set_text(self.handle, value)

    @property
    def text_state(self) -> AsposePDFPythonWrappers.text.text_state.TextState:
        '''Gets or sets a note text state.'''
        return AsposePDFPythonWrappers.text.text_state.TextState(AsposePDFPython.note_get_text_state(self.handle))

    @text_state.setter
    def text_state(self, value: AsposePDFPythonWrappers.text.text_state.TextState):
        AsposePDFPython.note_set_text_state(self.handle, value.handle)
