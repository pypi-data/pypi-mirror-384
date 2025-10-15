import AsposePDFPython
import AsposePDFPythonWrappers.image

from typing import overload

class Paragraphs:
    '''This class represents paragraph collection.'''

    @overload
    def __init__(self):
        '''Construct paragraph collection.'''
        ...

    @overload
    def __init__(self, handle: AsposePDFPython.paragraphs_handle):
        '''Initializes Paragraphs with handle.'''
        ...

    def __init__(self, arg0: None | AsposePDFPython.paragraphs_handle = None):
        if arg0 is None:
            self.handle = AsposePDFPython.paragraphs_create()
        elif isinstance(arg0, AsposePDFPython.paragraphs_handle):
            self.handle = arg0
        else:
            raise TypeError("Invalid number of arguments.")

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)


    def add(self, iamge: AsposePDFPythonWrappers.image.Image):
        '''Add image to collection.
        :param: image: image.Image'''
        AsposePDFPython.paragraphs_add_image(self.handle, iamge.handle)