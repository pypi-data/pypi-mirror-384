import AsposePDFPython


class IFontOptions:
    '''Useful properties to tune Font behaviour'''

    def __init__(self, handle: AsposePDFPython.text_Ifont_options_handle):
        '''Init from handle'''
        self.handle = handle

    @property
    def notify_about_font_embedding_error(self) -> bool:
        '''Sometimes it's not possible to embed desired font into document. There are many reasons, for example
        license restrictions or when desired font was not found on destination computer.
        When this situation comes it's not simply to detect, because desired font is embedded via set
        of property flag Font.IsEmbedded = true; Of course it's possible to read this property immediately after it was set but
        it's not convenient approach. Flag NotifyAboutFontEmbeddingError enforces exception mechanism
        for cases when attempt to embed font became failed. If this flag is set an exception of type
        :class:`aspose.pdf.FontEmbeddingException` will be thrown. By default false.'''
        return AsposePDFPython.text_ifont_option_get_notify_about_font_embedding_error(self.handle)

    @notify_about_font_embedding_error.setter
    def notify_about_font_embedding_error(self, value: bool):
        AsposePDFPython.text_ifont_option_set_notify_about_font_embedding_error(self.handle, value)