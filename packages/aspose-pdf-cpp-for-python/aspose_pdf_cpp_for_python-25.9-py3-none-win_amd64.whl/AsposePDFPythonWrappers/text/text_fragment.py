import AsposePDFPython
import AsposePDFPythonWrappers.rectangle
import AsposePDFPythonWrappers.page
import AsposePDFPythonWrappers.base_paragraph
import AsposePDFPythonWrappers.note
import AsposePDFPythonWrappers.text.tab_stops
import AsposePDFPythonWrappers.text.text_replace_options
import AsposePDFPythonWrappers.text.text_fragment_state
import AsposePDFPythonWrappers.text.text_segment_collection
import AsposePDFPythonWrappers.text.position

from typing import overload


class TextFragment(AsposePDFPythonWrappers.base_paragraph.BaseParagraph):
    '''Represents fragment of Pdf text.

    In a few words, :class:`TextFragment` object contains list of :class:`TextSegment` objects.

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
    Meanwhile :class:`TextSegment` objects are accessible and users are able to operate with :class:`TextSegment` objects independently.

    Note that changing TextFragment properties may change inner :attr:`TextFragment.segments` collection because TextFragment is an aggregate object
    and it may rearrange internal segments or merge them into single segment.
    If your requirement is to leave the :attr:`TextFragment.segments` collection unchanged, please change inner segments individually.'''

    @overload
    def __init__(self):
        '''Initializes new instance of the :class:`TextFragment` object.'''
        ...

    @overload
    def __init__(self, tab_stops: AsposePDFPythonWrappers.text.tab_stops.TabStops):
        '''Initializes new instance of the :class:`TextFragment` object with predefined :class:`TabStops` positions.

        :param tab_stops: Tabulation positions'''
        ...

    @overload
    def __init__(self, text: str):
        '''Creates :class:`TextFragment` object with single :class:`TextSegment` object inside.
        Specifies text string inside the segment.

        :param text: Text fragment's text.'''
        ...

    @overload
    def __init__(self, text: str, tab_stops: AsposePDFPythonWrappers.text.tab_stops.TabStops):
        '''Creates :class:`TextFragment` object with single :class:`TextSegment` object inside and predefined :class:`TabStops` positions.

        :param text: Text fragment's text.
        :param tab_stops: Tabulation positions'''
        ...

    def __init__(self, arg0: str | AsposePDFPythonWrappers.text.tab_stops.TabStops | None = None, arg1: AsposePDFPythonWrappers.text.tab_stops.TabStops | None = None):
        if arg0 is None and arg1 is None:
            super().__init__(AsposePDFPython.text_text_fragment_create())
        elif isinstance(arg0, AsposePDFPythonWrappers.text.tab_stops.TabStops) and arg1 is None:
            super().__init__(AsposePDFPython.text_text_fragment_create_from_tab_stops())
        elif isinstance(arg0, str) and arg1 is None:
            super().__init__(AsposePDFPython.text_text_fragment_create_from_text(arg0))
        elif isinstance(arg0, str) and isinstance(arg1, AsposePDFPythonWrappers.text.tab_stops.TabStops):
            super().__init__(AsposePDFPython.text_text_fragment_create_from_text_and__tab_stops(self.handle, arg0, arg1))
        else:
            raise TypeError("Invalid arguments.")

    def __del__(self):
        super().__del__()

    @property
    def replace_options(self) -> AsposePDFPythonWrappers.text.text_replace_options.TextReplaceOptions:
        '''Gets text replace options. The options define behavior when fragment text is replaced to more short/long.'''
        return AsposePDFPythonWrappers.text.text_replace_options.TextReplaceOptions(AsposePDFPython.text_text_fragment_get_replace_options(self.handle))

    @property
    def text(self) -> str:
        '''Gets or sets System.String text object that the :class:`TextFragment` object represents.'''
        return AsposePDFPython.text_text_fragment_get_text(self.handle)

    @text.setter
    def text(self, value: str):
        AsposePDFPython.text_text_fragment_set_text(self.handle, value)

    @property
    def text_state(self) -> AsposePDFPythonWrappers.text.text_fragment_state.TextFragmentState:
        '''Gets or sets text state for the text that :class:`TextFragment` object represents.

        Provides a way to change following properties of the text:
        Font
        FontSize
        FontStyle
        ForegroundColor
        BackgroundColor'''
        return AsposePDFPythonWrappers.text.text_fragment_state.TextFragmentState(AsposePDFPython.text_text_fragment_get_text_state(self.handle))

    @property
    def segments(self) -> AsposePDFPythonWrappers.text.text_segment_collection.TextSegmentCollection:
        '''Gets text segments for current :class:`TextFragment`.

        In a few words, :class:`TextSegment` objects are children of :class:`TextFragment` object.
        Advanced users may access segments directly to perform more complex text edit scenarios.
        For details, please look at :class:`TextFragment` object description.'''
        return AsposePDFPythonWrappers.text.text_segment_collection.TextSegmentCollection(AsposePDFPython.text_text_fragment_get_segments(self.handle))

    @segments.setter
    def segments(self, value: AsposePDFPythonWrappers.text.text_segment_collection.TextSegmentCollection):
        AsposePDFPython.text_text_fragment_set_segments(self.handle, value.handle)

    @property
    def position(self) -> AsposePDFPythonWrappers.text.position.Position:
        '''Gets or sets text position for text, represented with :class:`TextFragment` object.'''
        return AsposePDFPythonWrappers.text.position.Position(AsposePDFPython.text_text_fragment_get_position(self.handle))

    @position.setter
    def position(self, value: AsposePDFPythonWrappers.text.position.Position):
        AsposePDFPython.text_text_fragment_set_position(self.handle, value.handle)

    @property
    def baseline_position(self) -> AsposePDFPythonWrappers.text.position.Position:
        '''Gets text position for text, represented with :class:`TextFragment` object.
        The YIndent of the Position structure represents baseline coordinate of the text fragment.'''
        return AsposePDFPythonWrappers.text.position.Position(AsposePDFPython.text_text_fragment_get_baseline_position(self.handle))

    @baseline_position.setter
    def baseline_position(self, value: AsposePDFPythonWrappers.text.position.Position):
        AsposePDFPython.text_text_fragment_set_baseline_position(self.handle, value.handle)

    @property
    def rectangle(self) -> AsposePDFPythonWrappers.rectangle.Rectangle:
        '''Gets rectangle of the TextFragment'''
        return AsposePDFPythonWrappers.rectangle.Rectangle(AsposePDFPython.text_text_fragment_get_rectangle(self.handle))

    @property
    def page(self) -> AsposePDFPythonWrappers.page.Page:
        '''Gets page that contains the TextFragment

        The value can be null in case the TextFragment object doesn't belong to any page.'''
        return AsposePDFPythonWrappers.page.Page(AsposePDFPython.text_text_fragment_get_page(self.handle))

    @property
    def wrap_lines_count(self) -> int:
        '''Gets or sets wrap lines count for this paragraph(for pdf generation only)'''
        return AsposePDFPython.text_text_fragment_get_wrap_lines_count(self.handle)

    @wrap_lines_count.setter
    def wrap_lines_count(self, value: int):
        AsposePDFPython.text_text_fragment_set_wrap_lines_count(self.handle, value)

    @property
    def end_note(self) -> AsposePDFPythonWrappers.note.Note:
        '''Gets or sets the paragraph end note.(for pdf generation only)'''
        return AsposePDFPythonWrappers.note.Note(AsposePDFPython.text_text_fragment_get_end_note(self.handle))

    @end_note.setter
    def end_note(self, value: AsposePDFPythonWrappers.note.Note):
        AsposePDFPython.text_text_fragment_set_end_note(self.handle, value.handle)

    @property
    def foot_note(self) -> AsposePDFPythonWrappers.note.Note:
        '''Gets or sets the paragraph foot note.(for pdf generation only)'''
        return AsposePDFPythonWrappers.note.Note(AsposePDFPython.text_text_fragment_get_foot_note(self.handle))

    @foot_note.setter
    def foot_note(self, value: AsposePDFPythonWrappers.note.Note):
        AsposePDFPython.text_text_fragment_set_foot_note(self.handle, value.handle)