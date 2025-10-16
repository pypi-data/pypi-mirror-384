import AsposePDFPython
import AsposePDFPythonWrappers.document
import AsposePDFPythonWrappers.sys.io.stream
import AsposePDFPythonWrappers.facades.i_facade

from typing import overload


class Facade(AsposePDFPythonWrappers.facades.i_facade.IFacade):
    '''Base facade class.'''

    def __init__(self, handle: AsposePDFPython.facades_facade_handle):
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @overload
    def bind_pdf(self, src_file: str) -> None:
        '''Initializes the facade.
        :param src_file: The PDF file.'''
        ...

    @overload
    def bind_pdf(self, stream: AsposePDFPythonWrappers.sys.io.stream.Stream):
        '''Initializes the facade.
        :param stream: The PDF stream.'''
        ...

    @overload
    def bind_pdf(self, document: AsposePDFPythonWrappers.document.Document):
        '''Initializes the facade.
        :param stream: The PDF Document.'''
        ...

    def bind_pdf(self, arg):
        if isinstance(arg, str):
            AsposePDFPython.facades_facade_bind_pdf(self.handle, arg)
        elif isinstance(arg, AsposePDFPython.sys.stream.Stream):
            AsposePDFPython.facades_facade_bind_pdf_from_stream(self.handle, arg.handle)
        elif isinstance(arg, AsposePDFPythonWrappers.document.Document):
            AsposePDFPython.facades_facade_bind_pdf_from_document(self.handle, arg.handle)
        else:
            raise TypeError("Invalid number of arguments.")

    def close(self):
        '''Disposes Aspose.Pdf.Document bound with a facade.'''
        AsposePDFPython.facades_facade_close(self.handle)