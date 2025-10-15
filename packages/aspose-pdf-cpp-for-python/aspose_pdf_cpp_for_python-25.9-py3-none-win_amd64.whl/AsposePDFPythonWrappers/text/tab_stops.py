import AsposePDFPython
import AsposePDFPythonWrappers.text.tab_stop

from typing import overload


class TabStops:
    '''Represents a collection of :class:`TabStop` objects.'''

    def __init__(self):
        self.handle = AsposePDFPython.text_tab_stops_create()

    def __getitem__(self, index: int) -> AsposePDFPythonWrappers.text.tab_stop.TabStop:
        '''Gets or sets a :class:`TabStop` object from the collection according to TabStop index.

        :param index: Zero-based index of element in :class:`TabStops` collection.
        :returns: :class:`TabStop` object.'''
        return AsposePDFPythonWrappers.text.tab_stop.TabStop(AsposePDFPython.text_tab_stops_idx_get(self.handle, index))

    def __setitem__(self, index: int, value: AsposePDFPythonWrappers.text.tab_stop.TabStop):
        AsposePDFPython.text_tab_stops_idx_set(self.handle, index, value.handle)

    @overload
    def add(self) -> AsposePDFPythonWrappers.text.tab_stop.TabStop:
        '''Initializes a new instance of the :class:`TabStop` class and add it to the
        TabStops collection.

        :returns: The new :class:`TabStop` object.'''
        ...

    @overload
    def add(self, position: float) -> AsposePDFPythonWrappers.text.tab_stop.TabStop:
        '''Initializes a new instance of the :class:`TabStop` class with specified position and
        add it to the TabStops collection.

        :param position: The position of the tab stop.
        :returns: The new :class:`TabStop` object.'''
        ...

    @overload
    def add(self, tab_stop: AsposePDFPythonWrappers.text.tab_stop.TabStop) -> None:
        '''Add instance of the :class:`TabStop` class to the TabStops collection.

        :param tab_stop: The :class:`TabStop` object.'''
        ...

    @overload
    def add(self, position: float, leader_type: AsposePDFPython.TabLeaderType) -> AsposePDFPythonWrappers.text.tab_stop.TabStop:
        '''Initializes a new instance of the :class:`TabStop` class with specified position and leader
        type and add it to the TabStops collection.

        :param position: The position of the tab stop.
        :param leader_type: The leader type of the tab stop.
        :returns: The new :class:`TabStop` object.'''
        ...

    def add(self, arg0: float | AsposePDFPythonWrappers.text.tab_stop.TabStop | None, arg1: AsposePDFPython.TabLeaderType | None):
        if arg0 is None and arg1 is None:
            return AsposePDFPythonWrappers.text.tab_stop.TabStop(AsposePDFPython.text_tab_stops_add(self.handle))
        elif isinstance(arg0, float) and arg1 is None:
            return AsposePDFPythonWrappers.text.tab_stop.TabStop(AsposePDFPython.text_tab_stops_add_position(self.handle, arg0))
        elif isinstance(arg0, AsposePDFPythonWrappers.text.tab_stop.TabStop) and arg1 is None:
            AsposePDFPython.text_tab_stops_add_tab_stop(self.handle, arg0.handle)
        elif isinstance(arg0, float) and isinstance(arg1, AsposePDFPython.TabLeaderType):
            return AsposePDFPythonWrappers.text.tab_stop.TabStop(AsposePDFPython.text_tab_stops_add_position_with_leader_type(self.handle, arg0, arg1))
        else:
            raise TypeError("Invalid arguments.")

    @property
    def is_read_only(self) -> bool:
        '''Gets value indicating that this :class:`TabStops` instance is already attached to :class:`TextFragment` and became readonly.'''
        return AsposePDFPython.text_tab_stops_is_readonly(self.handle)

    @property
    def count(self) -> int:
        '''Gets count elements in TabStops collection.'''
        return AsposePDFPython.text_tab_stops_count(self.handle)
