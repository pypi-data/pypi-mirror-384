import AsposePDFPython

class TextOptions:
    '''Represents text processing options'''

    def __init__(self, handle: AsposePDFPython.text_text_options_handle):
        self.handle = handle

    def __del__(self):
        AsposePDFPython.color_handle(self.handle)