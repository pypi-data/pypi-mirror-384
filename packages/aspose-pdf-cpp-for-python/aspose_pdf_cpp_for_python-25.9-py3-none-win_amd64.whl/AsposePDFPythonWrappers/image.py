import AsposePDFPython
import AsposePDFPythonWrappers.base_paragraph


class Image(AsposePDFPythonWrappers.base_paragraph.BaseParagraph):
    '''Represents image.'''

    def __init__(self):
        '''Initialize Image object'''
        super().__init__(AsposePDFPython.image_create())
        
    def __del__(self):
        super().__del__()

    @property
    def fix_width(self) -> float:
        '''Get the image width.'''
        return AsposePDFPython.image_get_fix_width(self.handle)

    @fix_width.setter
    def fix_width(self, value: float):
        '''Set the image width.'''
        AsposePDFPython.image_set_fix_width(self.handle, value)

    @property
    def fix_height(self) -> float:
        '''Get the image height.'''
        return AsposePDFPython.image_get_fix_height(self.handle)

    @fix_height.setter
    def fix_height(self, value: float):
        '''Set the image height.'''
        AsposePDFPython.image_set_fix_height(self.handle, value)

    @property
    def file_type(self) -> AsposePDFPython.ImageFileType:
        '''Get the image file type.'''
        return AsposePDFPython.image_get_file_type(self.handle)

    @file_type.setter
    def file_type(self, value: AsposePDFPython.ImageFileType):
        '''Set the image file type.'''
        AsposePDFPython.image_set_file_type(self.handle, value)

    @property
    def file(self) -> str:
        '''Get the image file.'''
        return AsposePDFPython.image_get_file(self.handle)

    @file.setter
    def file(self, value: str):
        '''Set the image file.'''
        AsposePDFPython.image_set_file(self.handle, value)