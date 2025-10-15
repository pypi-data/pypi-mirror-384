import AsposePDFPython
import AsposePDFPythonWrappers.page_collection

from typing import overload


class Document:
    '''Class representing PDF document'''

    @overload
    def __init__(self):
        '''Initializes empty document.'''
        ...

    @overload
    def __init__(self, file_name: str):
        '''Just init Document using filename. The same as :meth:`Document.__init__`.

        :param filename: The name of the pdf document file.'''
        ...

    @overload
    def __init__(self, file_name: str, password: str):
        '''Initializes new instance of the :class:`Document` class for working with encrypted document.

        :param filename: Document file name.
        :param password: User or owner password.'''
        ...

    def __init__(self, arg0: None | str = None, arg1: str | None = None):
        if arg0 is None and arg1 is None:
            self.handle = AsposePDFPython.document_create()
        elif isinstance(arg0, str) and arg1 is None:
            self.handle = AsposePDFPython.document_create_from_file(arg0)
        elif isinstance(arg0, str) and isinstance(arg1, str):
            self.handle = AsposePDFPython.document_create_from_encrypted_file(arg0, arg1)
        else:
            raise TypeError("Invalid arguments.")

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    def set_title(self, title: str):
        '''Set Title for Pdf Document

        :param title: Document's title'''
        AsposePDFPython.document_set_title(self.handle, title)

    def optimize(self):
        '''Linearize document in order to
        - open the first page as quickly as possible;
        - display next page or follow by link to the next page as quickly as possible;
        - display the page incrementally as it arrives when data for a page is delivered over a slow channel (display the most useful data first);
        - permit user interaction, such as following a link, to be performed even before the entire page has been received and displayed.
        Invoking this method doesn't actually saves the document. On the contrary the document only is prepared to have optimized structure,
        call then Save to get optimized document.'''
        AsposePDFPython.document_optimize(self.handle)

    def decrypt(self):
        '''Decrypts the document. Call then Save to obtain decrypted version of the document.'''
        AsposePDFPython.document_decrypt(self.handle)

    @overload
    def encrypt(self, user_password: str, owner_password: str
                , permissions: AsposePDFPython.Permissions, crypto_algorithm: AsposePDFPython.CryptoAlgorithm
                , use_pdf20: bool):
        '''Encrypts the document. Call then Save to get encrypted version of the document.

        :param user_password: User password.
        :param owner_password: Owner password.
        :param permissions: Document permissions, see :attr:`Document.permissions` for details.
        :param crypto_algorithm: Cryptographic algorithm, see :attr:`Document.crypto_algorithm` for details.
        :param use_pdf20: Support for revision 6 (Extension 8).'''
        ...

    @overload
    def encrypt(self, user_password: str, owner_password: str
               , permissions: AsposePDFPython.Permissions, crypto_algorithm: AsposePDFPython.CryptoAlgorithm):
        '''Encrypts the document. Call then Save to get encrypted version of the document.

        :param user_password: User password.
        :param owner_password: Owner password.
        :param permissions: Document permissions, see :attr:`Document.permissions` for details.
        :param crypto_algorithm: Cryptographic algorithm, see :attr:`Document.crypto_algorithm` for details.'''
        ...

    def encrypt(self, arg0 :str, arg1: str, arg2: AsposePDFPython.Permissions, arg3: AsposePDFPython.CryptoAlgorithm, arg4: bool|None = None):
        if arg4 is None:
            AsposePDFPython.document_encrypt_1(self.handle, arg0, arg1, arg2, arg3)
        elif isinstance(arg4, bool):
            AsposePDFPython.document_encrypt(self.handle, arg0, arg1, arg2, arg3, arg4)
        else:
            raise TypeError("Invalid number of arguments.")

    def save_xml(self, save_to: str):
        '''Save document to XML.

        :param save_to: The document model xml file'''
        AsposePDFPython.document_save_xml(self.handle, save_to)

    def export_annotations_to_xfdf(self, file_name: str):
        '''Exports all document annotations to XFDF file

        :param file_name: XFDF file name'''
        AsposePDFPython.document_export_annotations_to_xfdf(self.handle, file_name)

    def save(self, output_file_name: str):
        '''Saves document into the specified file.

        :param output_file_name: Path to file where the document will be stored.'''
        AsposePDFPython.document_save(self.handle, output_file_name)

    @property
    def pages(self) -> AsposePDFPythonWrappers.page_collection.PageCollection:
        '''Gets or sets collection of document pages.
        Note that pages are numbered from 1 in collection.'''
        return AsposePDFPythonWrappers.page_collection.PageCollection(AsposePDFPython.document_get_pages(self.handle))