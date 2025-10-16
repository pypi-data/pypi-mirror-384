import AsposePDFPython

from typing import overload


class TabStop:
    '''Represents a custom Tab stop position in a paragraph.'''

    @overload
    def __init__(self):
        '''Initializes a new instance of the :class:`TabStop` class.'''
        ...

    @overload
    def __init__(self, position: float):
        '''Initializes a new instance of the :class:`TabStop` class with specified position.

        :param position: The position of the tab stop.'''
        ...

    @overload
    def __init__(self, handle: AsposePDFPython.text_tab_stop_handle):
        '''Initialize from handle'''
        ...

    def __init__(self, arg0 : float | AsposePDFPython.text_tab_stop_handle | None = None):
        if arg0 is None:
            self.handle = AsposePDFPython.text_tab_stop_create()
        elif isinstance(arg0, float):
            self.handle = AsposePDFPython.text_tab_stop_create_from_position(arg0)
        elif isinstance(AsposePDFPython.text_tab_stop_handle):
            self.handle = arg0
        else:
            raise TypeError("Invalid arguments.")

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    @property
    def position(self) -> float:
        '''Gets or sets a float value that indicates the tab stop position.'''
        return AsposePDFPython.text_tab_stop_get_position(self.handle)

    @position.setter
    def position(self, value: float):
        AsposePDFPython.text_tab_stop_set_position(self.handle, value)

    @property
    def leader_type(self) -> AsposePDFPython.TabLeaderType:
        '''Gets or sets a :class:`TabLeaderType` enum that indicates the tab leader type.'''
        return AsposePDFPython.text_tab_stop_get_leader_type(self.handle)

    @leader_type.setter
    def leader_type(self, value: AsposePDFPython.TabLeaderType):
        AsposePDFPython.text_tab_stop_set_leader_type(self.handle, value)

    @property
    def alignment_type(self) -> AsposePDFPython.TabAlignmentType:
        '''Gets or sets a :attr:`TabStop.alignment_type` enum that indicates the tab tab alignment type.'''
        return AsposePDFPython.text_tab_stop_get_aligment_type(self.handle)

    @alignment_type.setter
    def alignment_type(self, value: AsposePDFPython.TabAlignmentType):
        AsposePDFPython.text_tab_stop_get_aligment_type(self.handle, value)

    @property
    def is_read_only(self) -> bool:
        '''Gets value indicating that this :class:`TabStop` instance is already attached to :class:`TextFragment` and became readonly'''
        return AsposePDFPython.text_tab_stop_is_readonly(self.handle)
