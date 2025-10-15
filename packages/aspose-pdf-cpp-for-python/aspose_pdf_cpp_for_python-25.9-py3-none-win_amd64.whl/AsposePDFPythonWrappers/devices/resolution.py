import AsposePDFPython

from typing import overload

class Resolution:
    '''Represents class for holding image resolution.'''

    @overload
    def __init__(self, value:int):
        '''Initializes a new instance of the Resolution class.

        :param: value: which represents the horizontal and vertical resolution.'''
        ...

    @overload
    def __init__(self, value_x: int, value_y: int):
        '''Initializes a new instance of the Resolution class.

        :param: value_x: Horizontal resolution.
        :param: value_y: Vertical resolution.'''
        ...

    def __init__(self, handle: AsposePDFPython.resolution_handle):
        '''Initializes a new instance of the Resolution class from handle.
        
        :param: handle: Resolution handle.'''
        ...

    def __init__(self, *args):
        if len(args) == 1:
            if isinstance(args[0], int):
                self.handle = AsposePDFPython.devices_resolution_create(args[0])
            elif isinstance(args[0], AsposePDFPython.resolution_handle):
                self.handle = args[0]
            else:
                raise TypeError("Invalid argument type.")
        elif len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], int):
            self.handle = AsposePDFPython.devices_resolution_create_xy(args[0], args[1])
        else:
            raise TypeError("Invalid number of arguments.")

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @property
    def x(self) -> float:
        '''Get horizontal image resolution.'''
        return AsposePDFPython.devices_resolution_get_x(self.handle)

    @x.setter
    def x(self, value: float):
        '''Set horizontal image resolution.'''
        AsposePDFPython.devices_resolution_set_x(self.handle, value)

    @property
    def y(self) -> float:
        '''Get vertical image resolution.'''
        return AsposePDFPython.devices_resolution_get_y(self.handle)

    @y.setter
    def y(self, value: float):
        '''Set vertical image resolution.'''
        AsposePDFPython.devices_resolution_set_y(self.handle, value)