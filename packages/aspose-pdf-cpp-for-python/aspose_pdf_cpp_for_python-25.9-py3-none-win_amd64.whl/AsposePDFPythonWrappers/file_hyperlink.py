import AsposePDFPython
import AsposePDFPythonWrappers.hyperlink

from typing import overload

class FileHyperlink(AsposePDFPythonWrappers.hyperlink.Hyperlink):
    '''Represents file hyperlink object.'''

    @overload
    def __init__(self):
        '''Initializes a new instance of the :class:`FileHyperlink` class.'''
        ...

    @overload
    def __init__(self, path: str):
        '''Initializes a new instance of the :class:`FileHyperlink` class.

        :param path: Path to file.'''
        ...

    def __init__(self, arg0 : None | str = None):
        if isinstance(arg0, str):
            super().__init__(AsposePDFPython.file_hyperlink_create_from_path(arg0))
        elif arg0 is None:
            super().__init__(AsposePDFPython.file_hyperlink_create())
        
    def __del__(self):
        super().__del__()

    @property
    def path(self) -> str:
        '''Gets or sets the path to file.'''
        return AsposePDFPython.file_hyperlink_get_path(self.handle)

    @path.setter
    def path(self, value: str):
        AsposePDFPython.file_hyperlink_set_path(self.handle, value)
