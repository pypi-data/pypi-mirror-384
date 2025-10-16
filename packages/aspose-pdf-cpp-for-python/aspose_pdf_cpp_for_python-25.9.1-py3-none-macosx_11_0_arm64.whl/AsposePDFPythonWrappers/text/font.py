import AsposePDFPython
import AsposePDFPythonWrappers.sys.io.stream
import AsposePDFPythonWrappers.text.ifont_options

class Font:
    '''Represents font object.'''

    def __init__(self, handle: AsposePDFPython.text_font_handle):
        '''Init font from handle.'''
        self.handle = handle

    def get_last_font_embedding_error(self) -> str:
        '''An objective of this method - to return description of error if an attempt
        to embed font was failed. If there are no error cases it returns empty string.

        :returns: Error description'''
        return AsposePDFPython.text_font_get_last_font_embedding_error(self.handle)

    def save(self, stream: AsposePDFPythonWrappers.sys.io.stream.Stream) -> None:
        '''Saves the font into the stream.
        Note that the font is saved to intermediate TTF format intended to be used in a converted copy of the original document only.
        The font file is not intended to be used outside the original document context.

        :param stream: Stream to save the font.'''
        AsposePDFPython.text_font_save(self.handle, stream.handle)

    def measure_string(self, str: str, font_size: float) -> float:
        '''Measures the string.

        :param str: The string.
        :param font_size: Font size.
        :returns: Width of the string represented with this font and the specified size.'''
        return AsposePDFPython.text_font_measure_string(self.handle, str, font_size)

    @property
    def font_name(self) -> str:
        '''Gets font name of the :class:`Font` object.'''
        return AsposePDFPython.text_font_get_font_name(self.handle)

    @property
    def decoded_font_name(self) -> str:
        '''Sometimes PDF fonts(usually Chinese/Japanese/Korean fonts) could have specificical font name.
        This name is value of PDF font property "BaseFont" and sometimes this property
        could be represented in hexademical form. If read this name directly it could be represented
        in non-readable form. To get readable form it's necessary to decode font's name by
        rules specifical for this font.
        This property returns decoded font name, so use it for cases when you meet
        with a non-readable :attr:`Font.font_name`.
        If property :attr:`Font.font_name` has readable form this property will be the same as
        :attr:`Font.font_name`, so you can use this property for any cases when you need to
        get font name in a readable form.'''
        return AsposePDFPython.text_font_get_decoded_font_name(self.handle)

    @property
    def base_font(self) -> str:
        '''Gets BaseFont value of PDF font object. Also known as PostScript name of the font.'''
        return AsposePDFPython.text_font_get_base_font(self.handle)

    @property
    def is_embedded(self) -> bool:
        '''Gets or sets a value that indicates whether the font is embedded.
        Font based on IFont will automatically be subset and embedded'''
        return AsposePDFPython.text_font_get_is_embedded(self.handle)

    @is_embedded.setter
    def is_embedded(self, value: bool):
        AsposePDFPython.text_font_set_is_embedded(self.handle, value)

    @property
    def is_subset(self) -> bool:
        '''Gets or sets a value that indicates whether the font is a subset.
        Font based on IFont will automatically be subset and embedded'''
        return AsposePDFPython.text_font_get_is_subset(self.handle)

    @is_subset.setter
    def is_subset(self, value: bool):
        AsposePDFPython.text_font_set_is_subset(self.handle, value)

    @property
    def is_accessible(self) -> bool:
        '''Gets indicating whether the font is present (installed) in the system.

        Some operations are not available with fonts that could not be found in the system.'''
        return AsposePDFPython.text_font_get_is_accessible(self.handle)

    @property
    def font_options(self) -> AsposePDFPythonWrappers.text.ifont_options.IFontOptions:
        '''Useful properties to tune Font behaviour'''
        return AsposePDFPython.text_font_get_font_options(self.handle)
