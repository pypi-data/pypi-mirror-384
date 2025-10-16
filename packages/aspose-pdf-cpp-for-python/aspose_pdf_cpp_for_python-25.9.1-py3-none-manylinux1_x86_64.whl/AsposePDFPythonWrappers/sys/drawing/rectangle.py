import AsposePDFPython

class Rectangle:
    '''
    Represents a rectangular area of an image defined as integer X and Y coordinates of its upper left corner and its width and height.
    This type should be allocated on stack and passed to functions by value or by reference.
    '''

    def __init__(self, handle: AsposePDFPython.sys_drawing_rectangle_handle):
        self.handle = handle

