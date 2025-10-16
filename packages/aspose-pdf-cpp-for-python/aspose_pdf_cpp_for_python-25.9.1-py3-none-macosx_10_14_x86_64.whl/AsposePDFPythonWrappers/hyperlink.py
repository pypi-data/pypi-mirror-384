import AsposePDFPython

class Hyperlink:
    '''Represents abstract hyperlink.'''
    def __init__(self, handle: AsposePDFPython.hyperlink_handle):
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)