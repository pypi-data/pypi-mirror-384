import AsposePDFPython
import AsposePDFPythonWrappers.text.text_state
import AsposePDFPythonWrappers.text.position
import AsposePDFPythonWrappers.rectangle
import AsposePDFPythonWrappers.text.text_edit_options
import AsposePDFPythonWrappers.text.char_info_collection
import AsposePDFPythonWrappers.hyperlink

from typing import overload


class TextSegment:
    '''Represents segment of Pdf text.

    In a few words, :class:`TextSegment` objects are children of :class:`TextFragment` object.

    In details:

    Text of pdf document in :mod:`aspose.pdf` is represented by two basic objects: :class:`TextFragment` and :class:`TextSegment`

    The differences between them is mostly context-dependent.

    Let's consider following scenario. User searches text "hello world" to operate with it, change it's properties, look etc.

    Document doc = new Document(docFile);

    TextFragmentAbsorber absorber = new TextFragmentAbsorber("hello world");

    doc.Pages[1].Accept(absorber);

    Phisycally pdf text's representation is very complex.
    The text "hello world" may consist of several phisycally independent text segments.

    The Aspose.Pdf text model basically establishes that:class:`TextFragment` object
    provides single logic operation set over physical :class:`TextSegment` objects set that represent user's query.

    In text search scenario, :class:`TextFragment` is logical "hello world" text representation,
    and :class:`TextSegment` object collection represents all physical segments that construct "hello world" text object.

    So, :class:`TextFragment` is close to logical text representation.
    And :class:`TextSegment` is close to physical text representation.

    Obviously each :class:`TextSegment` object may have it's own font, coloring, positioning properties.

    :class:`TextFragment` provides simple way to change text with it's properties: set font, set font size, set font color etc.
    Meanwhile :class:`TextSegment` objects are accessible and users are able to operate with :class:`TextSegment` objects independently.'''

    @overload
    def __init__(self):
        '''Creates TextSegment object.'''
        ...

    @overload
    def __init__(self, text: str):
        '''Creates TextSegment object.

        :param text: Text segment's text.'''
        ...

    def __init__(self, arg0: str | None = None):
        if isinstance(arg0, str):
            self.handle = AsposePDFPython.text_text_segment_create_from_text(arg0)
        elif arg0 is None:
            self.handle = AsposePDFPython.text_text_segment_create()
        else:
            raise TypeError("Invalid arguments.")

    @staticmethod
    def my_html_encode(value: str) -> str:
        '''Encodes string as html.

        :param value: String value to encode.
        :returns: Html encoded string.'''
        return AsposePDFPython.text_text_segment_my_html_encode(value)


    @property
    def start_char_index(self) -> int:
        '''Gets starting character index of current segment in the show text operator (Tj, TJ) segment.'''
        return AsposePDFPython.text_text_segment_get_start_char_index(self.handle)

    @property
    def end_char_index(self) -> int:
        '''Gets ending character index of current segment in the show text operator (Tj, TJ) segment.'''
        return AsposePDFPython.text_text_segment_get_end_char_index(self.handle)

    @property
    def text(self) -> str:
        '''Gets or sets System.String text object that the :class:`TextSegment` object represents.'''
        return AsposePDFPython.text_text_segment_get_text(self.handle)

    @text.setter
    def text(self, value: str):
        AsposePDFPython.text_text_segment_set_text(self.handle, value)

    @property
    def text_state(self) -> AsposePDFPythonWrappers.text.text_state.TextState:
        '''Gets or sets text state for the text that :class:`TextSegment` object represents.

        Provides a way to change following properties of the text:
        Font
        FontSize
        FontStyle
        ForegroundColor
        BackgroundColor'''
        return AsposePDFPythonWrappers.text.text_state.TextState(AsposePDFPython.text_text_segment_get_text_state(self.handle))

    @text_state.setter
    def text_state(self, value: AsposePDFPythonWrappers.text.text_state.TextState):
        AsposePDFPython.text_text_segment_set_text_state(self.handle, value.handle)

    @property
    def position(self) -> AsposePDFPythonWrappers.text.position.Position:
        '''Gets text position for text, represented with :class:`TextSegment` object.'''
        return AsposePDFPythonWrappers.text.position.Position(AsposePDFPython.text_text_segment_get_position(self.handle))

    @position.setter
    def position(self, value: AsposePDFPythonWrappers.text.position.Position):
        AsposePDFPython.text_text_segment_set_position(self.handle, value.handle)

    @property
    def rectangle(self) -> AsposePDFPythonWrappers.rectangle.Rectangle:
        '''Gets rectangle of the TextSegment'''
        return AsposePDFPythonWrappers.rectangle.Rectangle(AsposePDFPython.text_text_segment_get_rectandle(self.handle))

    @property
    def baseline_position(self) -> AsposePDFPythonWrappers.text.position.Position:
        '''Gets text position for text, represented with :class:`TextSegment` object.
        The YIndent of the Position structure represents baseline coordinate of the text segment.'''
        return AsposePDFPythonWrappers.text.position.Position(AsposePDFPython.text_text_segment_get_baseline_position(self.handle))

    @baseline_position.setter
    def baseline_position(self, value: AsposePDFPythonWrappers.text.position.Position):
        AsposePDFPython.text_text_segment_set_baseline_position(self.handle, value.handle)

    @property
    def text_edit_options(self) -> AsposePDFPythonWrappers.text.text_edit_options.TextEditOptions:
        '''Gets or sets text edit options. The options define special behavior when requested symbol cannot be written with font.'''
        return AsposePDFPythonWrappers.text.text_edit_options.TextEditOptions(AsposePDFPython.text_text_segment_get_text_edit_options(self.handle))

    @text_edit_options.setter
    def text_edit_options(self, value: AsposePDFPythonWrappers.text.text_edit_options.TextEditOptions):
        AsposePDFPython.text_text_segment_set_text_edit_options(self.handle, value.handle)

    @property
    def characters(self) -> AsposePDFPythonWrappers.text.char_info_collection.CharInfoCollection:
        '''Gets collection of CharInfo objects that represent information on characters in the text segment.'''
        return AsposePDFPythonWrappers.text.char_info_collection.CharInfoCollection(AsposePDFPython.text_text_segment_get_characters(self.handle))

    @property
    def hyperlink(self) -> AsposePDFPythonWrappers.hyperlink.Hyperlink:
        '''Gets or sets the segment hyperlink(for pdf generator).'''
        return AsposePDFPythonWrappers.hyperlink.Hyperlink(AsposePDFPython.text_text_segment_get_hyperlink(self.handle))

    @hyperlink.setter
    def hyperlink(self, value: AsposePDFPythonWrappers.hyperlink.Hyperlink):
        AsposePDFPython.text_text_segment_set_hyperlink(self.handle, value.handle)
