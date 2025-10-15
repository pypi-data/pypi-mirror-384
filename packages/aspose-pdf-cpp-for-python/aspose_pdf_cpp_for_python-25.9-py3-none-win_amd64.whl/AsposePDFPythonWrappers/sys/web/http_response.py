import AsposePDFPython
import AsposePDFPythonWrappers.sys.io.text_writer

class HttpResponse:
    '''
    Dummy class making it possible linking translated code with HttpResponse references, but not executing it.
    Contains no properly implemented members.
    Objects of this class should only be allocated using System::MakeObject() function.
    Never create instance of this type on stack or using operator new, as it will result in runtime errors and/or assertion faults.
    Always wrap this class into System::SmartPtr pointer and use this pointer to pass it to functions as argument.
    '''
    def __init__(self, writer: AsposePDFPythonWrappers.sys.io.text_writer.TextWriter):
        '''Initializes PageCollection with text writer.'''
        self.handle = AsposePDFPython.sys_web_http_response_create(writer.handle)

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)
