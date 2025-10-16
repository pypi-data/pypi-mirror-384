import AsposePDFPython

from typing import overload


class Layer:
    '''Represents page layer.'''

    @overload
    def __init__(self, id: str, name: str):
        '''Initializes a new instance of the :class:`Layer` class.

        :param id: The layer id
        :param name: The layer name'''
        ...

    @overload
    def __init__(self, handle: AsposePDFPython.layer_handle):
        '''Initialize a new instance of the :class:`Layer` class from handle.'''
        ...

    def __init__(self, arg0: str | AsposePDFPython.layer_handle, arg1: str | None = None):
        if isinstance(arg0, AsposePDFPython.layer_handle) and arg1 is None:
            self.handle = arg0
        elif isinstance(arg0, str) and isinstance(arg1, str):
            self.handle = AsposePDFPython.layer_create(arg0, arg1)

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)


    @property
    def name(self) -> str:
        '''Gets the layer name.'''
        return AsposePDFPython.layer_get_name(self.handle)


    @property
    def id(self) -> str:
        '''Gets the layer id.'''
        return AsposePDFPython.layer_get_id(self.handle)