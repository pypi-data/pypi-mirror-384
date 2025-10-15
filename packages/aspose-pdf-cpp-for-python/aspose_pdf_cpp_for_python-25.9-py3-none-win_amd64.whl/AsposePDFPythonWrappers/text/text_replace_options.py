import AsposePDFPython
import AsposePDFPythonWrappers.text.text_options

from typing import overload

class TextReplaceOptions(AsposePDFPythonWrappers.text.text_options.TextOptions):
    '''Represents text replace options'''

    @overload
    def __init__(self, handle: AsposePDFPython.text_text_options_handle):
        '''Initialize from handle.'''
        self.handle = handle

    @overload
    def __init__(self, scope: AsposePDFPython.Scope):
        '''Initializes new instance of the :class:`TextReplaceOptions` object for the specified scope.

        :param scope: Scope object.'''
        ...

    @overload
    def __init__(self, adjustment: AsposePDFPython.ReplaceAdjustment):
        '''Initializes new instance of the :class:`TextReplaceOptions` object for the specified after replace action.

        :param adjustment: ReplaceAdjustment object.'''
        ...

    def __init__(self, arg0: AsposePDFPython.text_text_options_handle | AsposePDFPython.Scope | AsposePDFPython.ReplaceAdjustment):
        if arg0 is AsposePDFPython.text_text_options_handle:
            super().__init__(arg0)
        elif arg0 is AsposePDFPython.Scope:
            super().__init__(AsposePDFPython.text_text_replace_options_create_from_scope(arg0))
        elif arg0 is AsposePDFPython.ReplaceAdjustment:
            super().__init__(AsposePDFPython.text_text_replace_options_create_from_adjustment(args[0]))
        else:
            raise TypeError("Invalid arguments.")

    def __del__(self):
        super().__del__()

    @property
    def replace_scope(self) -> AsposePDFPython.Scope:
        '''Gets or sets a scope where replace text operation is applied'''
        return AsposePDFPython.text_text_replace_options_get_replace_scope(self.handle)

    @replace_scope.setter
    def replace_scope(self, value: AsposePDFPython.Scope):
        AsposePDFPython.text_text_replace_options_set_replace_scope(self.handle, value)

    @property
    def replace_adjustment_action(self) -> AsposePDFPython.ReplaceAdjustment:
        '''Gets or sets an action that will be done after replace of text fragment to more short.'''
        return AsposePDFPython.text_text_replace_options_get_replace_adjustment_action(self.handle)

    @replace_adjustment_action.setter
    def replace_adjustment_action(self, value: AsposePDFPython.ReplaceAdjustment):
        AsposePDFPython.text_text_replace_options_set_replace_adjustment_action(self.handle, value)

    @property
    def adjustment_new_line_spacing(self) -> float:
        '''Gets or sets value of line spacing that used if replace adjustment is forced to create new line of text.
        The value expected is multiplier of font size of the replaced text. Default is 1.2.'''
        return AsposePDFPython.text_text_replace_options_get_adjustment_new_line_spacing(self.handle)

    @adjustment_new_line_spacing.setter
    def adjustment_new_line_spacing(self, value: float):
        AsposePDFPython.text_text_replace_options_set_adjustment_new_line_spacing(self.handle, value)