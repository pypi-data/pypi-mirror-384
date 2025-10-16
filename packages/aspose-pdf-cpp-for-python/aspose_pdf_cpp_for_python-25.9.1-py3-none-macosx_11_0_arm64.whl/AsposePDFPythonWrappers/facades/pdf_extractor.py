import AsposePDFPython
import AsposePDFPythonWrappers.facades.facade
import AsposePDFPythonWrappers.sys.io.stream

from typing import overload

class PdfExtractor(AsposePDFPythonWrappers.facades.facade.Facade):
    '''Class for extracting images and text from PDF document.'''

    def __init__(self):
        '''Initializes new :class:`PdfExtractor` object.'''
        super().__init__(AsposePDFPython.facades_pdf_extractor_create())

    def __del__(self):
        '''Close handle.'''
        super().__del__()

    def extract_text(self) -> None:
        '''Extracts text from a Pdf document using Unicode encoding.'''
        AsposePDFPython.facades_pdf_extractor_extract_text(self.handle)

    @overload
    def get_text(self, output_file: str) -> None:
        '''Saves text to file. see also::meth:`PdfExtractor.extract_text`

        :param output_file: The file path and name to save the text.'''
        ...

    @overload
    def get_text(self, output_stream: AsposePDFPythonWrappers.sys.io.stream.Stream) -> None:
        '''Saves text to stream. see also::meth:`PdfExtractor.extract_text`

        :param output_stream: The stream to save the text.'''
        ...

    def get_text(self, arg):
        if isinstance(arg, str):
            AsposePDFPython.facades_pdf_extractor_get_text_to_file(self.handle, arg)
        elif isinstance(arg, AsposePDFPythonWrappers.sys.io.stream.Stream):
            AsposePDFPython.facades_pdf_extractor_get_text_to_stream(self.handle, arg.handle)
        else:
            raise TypeError("Invalid number of arguments.")