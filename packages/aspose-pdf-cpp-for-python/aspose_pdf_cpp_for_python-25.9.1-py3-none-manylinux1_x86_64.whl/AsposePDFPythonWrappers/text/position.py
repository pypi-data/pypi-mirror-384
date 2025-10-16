from __future__ import annotations
import AsposePDFPython

from typing import overload


class Position:
    '''Represents a position object'''

    @overload
    def __init__(self, handle: AsposePDFPython.text_position_handle):
        '''Init form handle'''
        ...

    @overload
    def __init__(self, x_indent: float, y_indent: float):
        '''Initializes a new instance of :class:`Position` class

        :param x_indent: X coordinate value.
        :param y_indent: Y coordinate value.'''
        ...

    def __init__(self, arg0: AsposePDFPython.text_position_handle | float | int, arg1: float | int):
        if isinstance(arg0, AsposePDFPython.text_position_handle):
            self.handle = arg0
        elif isinstance(arg0, float) and isinstance(arg1, float):
            self.handle = AsposePDFPython.text_position_create(arg0, arg1)
        elif isinstance(arg0, int) and isinstance(arg1, int):
            self.handle = AsposePDFPython.text_position_create(arg0, arg1)
        else:
            raise TypeError("Invalid arguments.")

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    @property
    def x_indent(self) -> float:
        '''Gets the X coordinate of the object'''
        return AsposePDFPython.text_position_get_x_indent(self.handle)

    @x_indent.setter
    def x_indent(self, value: float):
        AsposePDFPython.text_position_set_x_indent(self.handle, value)

    @property
    def y_indent(self) -> float:
        '''Gets the Y coordinate of the object'''
        return AsposePDFPython.text_position_get_y_indent(self.handle)

    @y_indent.setter
    def y_indent(self, value: float):
        AsposePDFPython.text_position_set_y_indent(self.handle, value)

    def __eq__(self, other: Position):
        return AsposePDFPython.text_position_equals(self.handle, other.handle)