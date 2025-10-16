import AsposePDFPython
import AsposePDFPythonWrappers.warning_info


class IWarningCallback:
    ''' Interface for user's callback mechanism support. '''

    def __init__(self, handle: AsposePDFPython.i_warning_callback_handle):
        self.handle = handle

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    def warning(self, warning: AsposePDFPythonWrappers.warning_info.WarningInfo) -> AsposePDFPython.ReturnAction:
        '''The callback method for some program notifications.

        :param warning: the warning information for some happened warning
        :returns: the result of further program workflow'''
        return AsposePDFPython.pdf_iwarningcallback_warning(self.handle, warning.handle)