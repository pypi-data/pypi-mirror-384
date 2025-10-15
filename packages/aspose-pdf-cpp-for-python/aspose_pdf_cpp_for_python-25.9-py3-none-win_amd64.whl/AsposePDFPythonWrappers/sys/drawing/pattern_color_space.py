import AsposePDFPython


class PatternColorSpace:
    '''Represents base pattern class.'''

    def __init__(self, handle: AsposePDFPython.drawing_pattern_color_space_handle):
        self.handle = handle

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)