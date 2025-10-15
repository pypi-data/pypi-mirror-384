import AsposePDFPython

class WarningInfo:
    '''Immutable object for encapsulating warning information.'''

    def __init__(self, type: AsposePDFPython.WarningType, message: str):
        '''Constructs instance for gathering information.

        :param type: the warning type to set
        :param message: the warning message to set'''
        self.handle = AsposePDFPython.warning_info_create(type, message)

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @property
    def warning_message(self) -> str:
        '''Returns string representation of warning message.
        :returns: the warning message'''
        return AsposePDFPython.warning_info_get_warning_message(self.handle)

    @property
    def warning_type_property(self) -> AsposePDFPython.WarningType:
        '''Returns warning type.
        :returns: the warning type'''
        return AsposePDFPython.warning_info_get_warning_type_property(self.handle)