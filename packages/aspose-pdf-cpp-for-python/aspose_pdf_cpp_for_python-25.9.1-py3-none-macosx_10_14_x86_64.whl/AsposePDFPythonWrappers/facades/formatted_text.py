import AsposePDFPython

class FormattedText:
    '''Class which represents formatted text. Contains information about text and its color, size, style.'''

    def __init__(self):
        '''Initializes FormattedText.'''
        self.handle = AsposePDFPython.facades_formatted_text_create()

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)