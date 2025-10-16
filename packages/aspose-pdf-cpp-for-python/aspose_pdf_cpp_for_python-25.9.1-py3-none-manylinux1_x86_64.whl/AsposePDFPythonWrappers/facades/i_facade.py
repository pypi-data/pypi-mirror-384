import AsposePDFPythonWrappers.sys.io.stream
import AsposePDFPythonWrappers.document

from typing import overload
from abc import ABC, abstractmethod


class IFacade:
    '''General facade interface that defines common facades methods.'''

    @abstractmethod
    @overload
    def bind_pdf(self, src_file: str) -> None:
        '''Binds PDF document for editing.
        :param src_file: The path of input PDF document.'''
        ...

    @abstractmethod
    @overload
    def bind_pdf(self, src_stream: AsposePDFPythonWrappers.sys.io.stream.Stream) -> None:
        '''Binds PDF document for editing.
        :param src_stream: The stream of input PDF document.'''
        ...

    @abstractmethod
    @overload
    def bind_pdf(self, src_doc: AsposePDFPythonWrappers.document.Document) -> None:
        '''Binds PDF document for editing.
        :param src_doc: Input PDF document.'''
        ...

    @abstractmethod
    def close(self) -> None:
        '''Releases any resources associates with the current facade.'''
        ...