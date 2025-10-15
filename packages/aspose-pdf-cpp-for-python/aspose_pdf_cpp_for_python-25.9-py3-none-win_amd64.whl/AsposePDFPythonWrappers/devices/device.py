import AsposePDFPython


class Device:
    '''Abstract class for all types of devices. Device is used to represent pdf document in some format.
    For example, document page can be represented as image or text.'''

    def __init__(self, handle: AsposePDFPython.devices_device_handle):
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)