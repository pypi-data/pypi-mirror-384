from __future__ import annotations
import AsposePDFPython

class Point:
    '''Represent point with fractional coordinates.'''

    def __init__(self, handle: AsposePDFPython.point_handle):
        '''Initializes PageCollection with handle.'''
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @property
    def x(self) -> float:
        '''Get X coordinate value.'''
        return AsposePDFPython.point_get_x(self.handle)

    @x.setter
    def x(self, value: float):
        '''Set X coordinate value.'''
        AsposePDFPython.point_set_x(self.handle, value)

    @property
    def y(self) -> float:
        '''Get Y coordinate value.'''
        return AsposePDFPython.point_get_y(self.handle)

    @y.setter
    def y(self, value: float):
        '''Set Y coordinate value.'''
        AsposePDFPython.point_set_y(self.handle, value)

    @staticmethod
    def trivial() -> Point:
        '''Initializes trivial rectangle i.e. rectangle with zero position and size.'''
        return Point(AsposePDFPython.point_get_trivial())