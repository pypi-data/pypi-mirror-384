import AsposePDFPython

from typing import overload


class MarginInfo:
    '''This class represents a margin for different objects.'''

    @overload
    def __init__(self):
        '''Initializes a new instance of the :class:`MarginInfo` class.'''
        ...

    @overload
    def __init__(self, left: float, bottom: float, right: float, top: float):
        '''Constructor of Rectangle.

        :param left: Left margin.
        :param bottom: Bottom margin
        :param right: Right margin.
        :param top: Top margin.'''
        ...

    @overload
    def __init__(self, handle: AsposePDFPython.margin_info_handle):
        '''Init from handle'''
        ...

    def __int__(self, arg0: None | float | AsposePDFPython.margin_info_handle = None
                    , arg1: float | None = None
                    , arg2: float | None = None
                    , arg3: float | None = None):
        if arg0 is None and arg1 is None and arg2 is None and arg3 is None:
            self.handle = AsposePDFPython.margin_info_create()
        elif isinstance(arg0, AsposePDFPython.margin_info_handle) and arg1 is None and arg2 is None and arg3 is None:
            self.handle = arg0
        elif isinstance(arg0, float) and isinstance(arg1, float) and isinstance(arg2, float) and isinstance(arg3, float):
            self.handle = AsposePDFPython.margin_info_create_from_lbrt(arg0, arg1, arg2, arg3)

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)
    @property
    def left(self) -> float:
        '''Gets or sets a float value that indicates the left margin.'''
        return AsposePDFPython.margin_info_get_left(self.handle)

    @left.setter
    def left(self, value: float):
        AsposePDFPython.margin_info_set_left(self.handle, value)

    @property
    def right(self) -> float:
        '''Gets or sets a float value that indicates the right margin.'''
        return AsposePDFPython.margin_info_get_right(self.handle)

    @right.setter
    def right(self, value: float):
        AsposePDFPython.margin_info_set_right(self.handle, value)

    @property
    def top(self) -> float:
        '''Gets or sets a float value that indicates the top margin.'''
        AsposePDFPython.margin_info_get_top(self.handle)

    @top.setter
    def top(self, value: float):
        AsposePDFPython.margin_info_set_top(self.handle, value)

    @property
    def bottom(self) -> float:
        '''Gets or sets a float value that indicates the bottom margin.'''
        AsposePDFPython.margin_info_get_bottom(self.handle)

    @bottom.setter
    def bottom(self, value: float):
        AsposePDFPython.margin_info_set_bottom(self.handle, value)
