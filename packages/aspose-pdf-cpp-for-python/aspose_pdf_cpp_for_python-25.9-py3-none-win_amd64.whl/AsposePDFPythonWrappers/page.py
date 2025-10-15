import AsposePDFPython
import AsposePDFPythonWrappers.rectangle
import AsposePDFPythonWrappers.paragraphs
import AsposePDFPythonWrappers.stamp
import AsposePDFPythonWrappers.artifact_collection
import AsposePDFPythonWrappers.layer


class Page:
    '''Class representing page of PDF document.'''

    def __init__(self, handle: AsposePDFPython.page_handle):
        '''Initializes PageCollection with handle.'''
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @property
    def rotate(self) -> AsposePDFPython.Rotation:
        '''Get rotation of the page.

        :returns: Added page.'''
        return AsposePDFPython.page_get_rotate(self.handle)

    @rotate.setter
    def rotate(self, value: AsposePDFPython.Rotation):
        '''Set rotation of the page.

        :param value: Rotate value'''
        AsposePDFPython.page_set_rotate(self, value)

    @property
    def color_type(self) -> AsposePDFPython.ColorType:
        '''Sets color type of the pages based on information getting from operators SetColor, images and forms.'''
        return AsposePDFPython.page_color_type(self.handle)

    @property
    def rect(self) -> AsposePDFPythonWrappers.rectangle.Rectangle:
        '''Get rectangle of the page.
           For get: page crop box is returned if specified, otherwise page media box is returned.
           For set: page media box always set.
           Please note that this property don't consider page rotation. To get page rectangle considering rotation please use ActualRect.'''
        return AsposePDFPythonWrappers.rectangle.Rectangle(AsposePDFPython.page_get_rectangle(self.handle))

    @rect.setter
    def rect(self, value: AsposePDFPythonWrappers.rectangle.Rectangle):
        '''Set rectangle of the page.
           For get: page crop box is returned if specified, otherwise page media box is returned.
           For set: page media box always set.
           Please note that this property don't consider page rotation. To get page rectangle considering rotation please use ActualRect.'''
        AsposePDFPython.page_set_rectangle(self.handle, value.handle)

    @property
    def paragraphs(self) -> AsposePDFPythonWrappers.paragraphs.Paragraphs:
        '''Gets the paragraphs.

        :returns Paragraphs'''
        return AsposePDFPythonWrappers.paragraphs.Paragraphs(AsposePDFPython.page_get_paragraphs(self.handle))

    @paragraphs.setter
    def paragraphs(selfs, value: AsposePDFPythonWrappers.paragraphs.Paragraphs):
        '''Gets the paragraphs.

        :param value: Paragraphs'''
        AsposePDFPython.page_set_paragraphs(selfs.handle, value.handle)

    def add_stamp(self, value: AsposePDFPythonWrappers.stamp.Stamp):
        '''Put stamp into page. Stamp can be page number, image or simple text, e.g. some logo.

        :param stamp: Stamp to add on the page.
                      Each stamp has its coordinates and corresponding properties regarding to the kind of stamp,
                      i.e. image or text value.'''
        AsposePDFPython.page_add_stamp(self.handle, value.handle)

    @property
    def number(self) -> int:
        '''Get number of the page.

        :returns: page number'''
        return AsposePDFPython.page_get_number(self.handle)

    @property
    def layers(self) -> list[AsposePDFPythonWrappers.layer.Layer]:
        '''Gets layers collection.'''
        layer_handles_list = AsposePDFPython.page_get_layers(self.handle)
        result = []
        for layer_handle in layer_handles_list:
            result.append(AsposePDFPythonWrappers.layer.Layer(layer_handle))
        return result

    @property
    def artifacts(self) -> AsposePDFPythonWrappers.artifact_collection.ArtifactCollection:
        '''Gets collection of artifacts on the page.'''
        return AsposePDFPythonWrappers.artifact_collection.ArtifactCollection(
            AsposePDFPython.page_get_artifacts(self.handle))