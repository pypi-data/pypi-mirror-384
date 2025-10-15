from __future__ import annotations

import AsposePDFPython
import AsposePDFPythonWrappers.page

from typing import Union
from typing import overload


class PageCollection:
    '''Collection of PDF document pages.'''

    def __init__(self, handle: AsposePDFPython.page_collection_handle):
        '''Initializes PageCollection with handle.'''
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @overload
    def add(self) -> AsposePDFPythonWrappers.page.Page:
        '''Adds empty page

        :returns: Added page.'''
        ...

    @overload
    def add(self, pages: PageCollection):
        '''Adds to collection all pages from list.

        :param pages: List which contains all pages which must be added.'''
        ...

    def add(self, arg0: None | PageCollection = None) -> Union[AsposePDFPythonWrappers.page.Page, None]:
        if arg0 is None:
            return AsposePDFPythonWrappers.page.Page(AsposePDFPython.page_collection_add_page(self.handle))
        elif isinstance(arg0, PageCollection):
            AsposePDFPython.page_collection_add_pages(self.handle, arg0.handle)
            return None

    def count(self) -> int:
        '''Adds return page count

        :returns: Added page.'''
        return AsposePDFPython.page_collection_count(self.handle)

    def __getitem__(self, index: int) -> AsposePDFPythonWrappers.page.Page:
        '''Gets page by index.

        :param index: Index of page.
        :returns: Retreived page.'''
        return AsposePDFPythonWrappers.page.Page(AsposePDFPython.page_collection_get_page(self.handle, index))

    def copy_page(self, page: AsposePDFPythonWrappers.page.Page) -> AsposePDFPythonWrappers.page.Page:
        '''Adds page to collection.

        :param page which should be added.
        :returns: Added page.'''
        return AsposePDFPythonWrappers.page.Page(AsposePDFPython.page_collection_copy_page(self.handle, page.handle))
