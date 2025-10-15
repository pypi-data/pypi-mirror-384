import AsposePDFPython
import AsposePDFPythonWrappers.hyperlink
import AsposePDFPythonWrappers.base_paragraph

from typing import overload


class LocalHyperlink(AsposePDFPythonWrappers.hyperlink.Hyperlink):
    '''Represents local hyperlink object.'''

    @overload
    def __init__(self):
        '''Initializes a new instance of the :class:`LocalHyperlink` class.'''
        ...

    @overload
    def __init__(self, target: AsposePDFPythonWrappers.base_paragraph.BaseParagraph):
        '''Initializes a new instance of the :class:`LocalHyperlink` class.

        :param target: Target paragraph.'''
        ...

    def __init__(self, arg0: None | AsposePDFPythonWrappers.base_paragraph.BaseParagraph):
        if isinstance(arg0, AsposePDFPythonWrappers.base_paragraph.BaseParagraph):
            super().__init__(AsposePDFPython.local_hyperlink_create_from_target(arg0.handle))
        elif arg0 is None:
            super().__init__(AsposePDFPython.local_hyperlink_create())

    def __del__(self):
        super().__del__()

    @property
    def target(self) -> AsposePDFPythonWrappers.base_paragraph.BaseParagraph:
        '''Gets or sets the target paragraph.'''
        return AsposePDFPythonWrappers.base_paragraph.BaseParagraph(AsposePDFPython.local_hyperlink_get_terget(self.handle))

    @target.setter
    def target(self, value: AsposePDFPythonWrappers.base_paragraph.BaseParagraph):
        AsposePDFPython.local_hyperlink_set_terget(self.handle, value.handle);

    @property
    def target_page_number(self) -> int:
        '''Gets or sets the target page number.'''
        return AsposePDFPython.local_hyperlink_get_target_page_number(self.handle)

    @target_page_number.setter
    def target_page_number(self, value: int):
        AsposePDFPython.local_hyperlink_set_target_page_number(self.handle, value)