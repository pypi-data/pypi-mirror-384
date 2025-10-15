import AsposePDFPython
import AsposePDFPythonWrappers.text.text_segment


class TextSegmentCollection:
    '''Represents a text segments collection'''

    def __init__(self, handle: AsposePDFPython.text_text_segment_collection_handle):
        '''Init form handle'''
        self.handle = handle

    def __del__(self):
        AsposePDFPython.close_handle(self.handle)

    def __getitem__(self, index: int) -> AsposePDFPythonWrappers.text.text_segment.TextSegment:
        '''Gets the text segment element at the specified index.

        :param index: Index within the collection.
        :returns: TextSegment object.'''
        return AsposePDFPythonWrappers.text.text_segment.TextSegment(AsposePDFPython.text_text_segment_collection_idx_get(index))

    @property
    def is_synchronized(self) -> bool:
        '''Gets a value indicating whether access to the collection is synchronized (thread safe).'''
        AsposePDFPython.text_text_segment_collection_get_is_synchronized(self.handle)

    @property
    def is_readonly(self) -> bool:
        '''Gets a value indicating whether collection is read-only'''
        return AsposePDFPython.text_text_segment_collection_get_is_read_only(self.handle)

    def add(self, item: AsposePDFPythonWrappers.text.char_info.CharInfo) -> None:
        '''Collection is read-only, throws NotImplementedException.

        :param item: Item to add.'''
        AsposePDFPython.text_text_segment_collection_add (self.handle, item.handle)

    def clear(self) -> None:
        '''Collection is read-only. Always throws NotImplementedException.'''
        AsposePDFPython.text_text_segment_collection_clear(self.handle)

    def contains(self, item: AsposePDFPythonWrappers.text.char_info.CharInfo) -> bool:
        '''Determines whether the collection contains a specific value.

        :param item: The object to locate in the collection.
        :return: true if item is found in the collection; otherwise, false.
        '''
        return AsposePDFPython.text_text_segment_collection_contains (self.handle, item.handle)

    def remove(self, item: AsposePDFPythonWrappers.text.char_info.CharInfo) -> bool:
        '''Collection is read-only, throws NotImplementedException.

        :param item: Item to remove.
        :return: NotImplementedException
        '''
        return AsposePDFPython.text_text_segment_collection_remove(self.handle, item.handle)