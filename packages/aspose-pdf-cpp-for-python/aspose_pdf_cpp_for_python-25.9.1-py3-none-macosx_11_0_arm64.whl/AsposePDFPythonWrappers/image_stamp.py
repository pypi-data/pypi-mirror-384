import AsposePDFPython
import AsposePDFPythonWrappers.stamp


class ImageStamp(AsposePDFPythonWrappers.stamp.Stamp):
    '''Reresents graphic stamp.'''

    def __init__(self, file_name: str):
        '''Creates image stamp by image in the specified file.
        :param file_name: Name of the file which contains image.'''
        super().__init__(AsposePDFPython.image_stamp_create(file_name))

    def __del__(self):
        '''Close handle.'''
        super().__del__()

    @property
    def width(self) -> float:
        '''Gets image width. Setting this property allos to scal image horizontally.'''
        return AsposePDFPython.image_stamp_get_width(self.handle)

    @width.setter
    def width(self, value: float):
        '''Sets image width. Setting this property allos to scal image horizontally.'''
        AsposePDFPython.image_stamp_set_width(self.handle, value)

    @property
    def height(self) -> float:
        '''Gets image height. Setting this image allows to scale image vertically.'''
        return AsposePDFPython.image_stamp_get_height(self.handle)

    @height.setter
    def height(self, value: float):
        '''Sets image height. Setting this image allows to scale image vertically.'''
        AsposePDFPython.image_stamp_set_height(self.handle, value)

    @property
    def quality(self) -> int:
        '''Gets quality of image stamp in percent. Valid values are 0..100%.'''
        return AsposePDFPython.image_stamp_get_quality(self.handle)

    @quality.setter
    def quality(self, value: int):
        '''Sets quality of image stamp in percent. Valid values are 0..100%.'''
        AsposePDFPython.image_stamp_set_quality(self.handle, value)