import AsposePDFPython

class License:
    '''Provides methods to license the component.'''

    def __init__(self):
        self.handle = AsposePDFPython.license_create()

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    def set_license(self, license_name: str) -> None:
        '''Licenses the component.

        :param license_name: License file name.
                             Use an empty string to switch to evaluation mode.'''
        AsposePDFPython.license_set(self.handle, license_name)