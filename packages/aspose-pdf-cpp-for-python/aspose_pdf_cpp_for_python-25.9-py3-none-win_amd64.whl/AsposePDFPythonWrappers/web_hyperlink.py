import AsposePDFPython
import AsposePDFPythonWrappers.hyperlink

from typing import overload

class WebHyperlink(AsposePDFPythonWrappers.hyperlink.Hyperlink):
    '''Represents web hyperlink object.'''

    @overload
    def __init__(self):
        '''Initializes a new instance of the :class:`WebHyperlink` class.'''
        ...

    @overload
    def __init__(self, url: str):
        '''Initializes a new instance of the :class:`WebHyperlink` class.

        :param url: web url for hyperlink.'''
        ...

    def __init__(self, arg0: None | str = None):
        if isinstance(arg0, str):
            super().__init__(AsposePDFPython.web_hyperlink_create_from_url(arg0))
        elif arg0 is None:
            super().__init__(AsposePDFPython.web_hyperlink_create())

    def __del__(self):
        super().__del__()

    @property
    def url(self) -> str:
        '''Gets or sets the web url.'''
        return AsposePDFPython.web_hyperlink_get_url(self.handle)

    @url.setter
    def url(self, value: str):
        AsposePDFPython.web_hyperlink_set_url(self.handle, value)