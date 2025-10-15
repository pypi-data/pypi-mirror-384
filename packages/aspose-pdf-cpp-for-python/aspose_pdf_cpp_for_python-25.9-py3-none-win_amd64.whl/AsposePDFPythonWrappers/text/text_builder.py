import AsposePDFPython
import AsposePDFPythonWrappers.page
import AsposePDFPythonWrappers.text.text_fragment


class TextBuilder:
    '''Appends text object to Pdf page.'''

    def __init__(self, page: AsposePDFPythonWrappers.page.Page):
        '''Initializes a new instance of :class:`TextBuilder` class for the Pdf page.

        The TextBuilder allows to append text objects to Pdf pages.

        :param page: Page object.'''
        self.handle = AsposePDFPython.text_text_builder_create_from_page(page.handle)

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    def append_text(self, text_fragment: AsposePDFPythonWrappers.text.text_fragment.TextFragment) -> None:
        '''Appends text fragment to Pdf page

        :param text_fragment: Text fragment object.'''
        AsposePDFPython.text_text_builder_append_text(self.handle, text_fragment.handle)