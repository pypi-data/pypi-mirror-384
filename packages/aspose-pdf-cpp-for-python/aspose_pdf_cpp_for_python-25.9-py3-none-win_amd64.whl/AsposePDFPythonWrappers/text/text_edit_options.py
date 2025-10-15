import AsposePDFPython
import AsposePDFPythonWrappers.text.text_options

from typing import overload


class TextEditOptions(AsposePDFPythonWrappers.text.text_options.TextOptions):
    '''Descubes options of text edit operations.'''

    @overload
    def __init__(self, no_character_behavior: AsposePDFPython.NoCharacterAction):
        '''Initializes new instance of the :class:`TextEditOptions` object for the specified no-character behavior mode.

        :param no_character_behavior: No-character behavior mode object.'''
        ...

    @overload
    def __init__(self, font_replace_behavior: AsposePDFPython.FontReplace):
        '''Initializes new instance of the :class:`TextEditOptions` object for the specified font replacement behavior mode.

        :param font_replace_behavior: Font replace behavior object.'''
        ...

    @overload
    def __init__(self, allow_language_transformation: bool):
        '''Initializes new instance of the :class:`TextEditOptions` object for the specified language transformation permission.

        :param allow_language_transformation: Allows language transformation if set to true.'''
        ...

    @overload
    def __init__(self, language_transformation_behavior: AsposePDFPython.LanguageTransformation):
        '''Initializes new instance of the :class:`TextEditOptions` object for the specified language transformation behavior mode.

        :param language_transformation_behavior: language transformation behavior object.'''
        ...

    def __init__(self, arg0: AsposePDFPython.NoCharacterAction
                             | AsposePDFPython.FontReplace
                             | bool
                             | AsposePDFPython.LanguageTransformation):
        if isinstance(arg0, AsposePDFPython.NoCharacterAction):
            super().__init__(AsposePDFPython.text_text_edit_options_create_from_no_character_action(arg0))
        elif isinstance(arg0, AsposePDFPython.FontReplace):
            super().__init__(AsposePDFPython.text_text_edit_options_create_from_font_replace(arg0))
        elif isinstance(arg0, bool):
            super().__init__(AsposePDFPython.text_text_edit_options_create_from_allow_languge_transformation(arg0))
        elif isinstance(arg0, AsposePDFPython.LanguageTransformation):
            super().__init__(AsposePDFPython.text_text_edit_options_create_from_languge_transformation(arg0))
        else:
            raise TypeError("Invalid arguments.")

    def __del__(self):
        super().__del__()

    @property
    def replacement_font(self) -> AsposePDFPythonWrappers.text.font.Font:
        '''Gets or sets font used for replacing if user font does not contain required character'''
        return AsposePDFPythonWrappers.text.font.Font(AsposePDFPython.text_text_edit_options_get_replacement_font(self.handle))

    @replacement_font.setter
    def replacement_font(self, value: AsposePDFPythonWrappers.text.font.Font):
        AsposePDFPython.text_text_edit_options_set_replacement_font(self.handle, value.handle)

    @property
    def no_character_behavior(self) -> AsposePDFPython.NoCharacterAction:
        '''Gets or sets mode that defines behavior in case fonts don't contain requested characters.'''
        AsposePDFPython.text_text_edit_options_get_no_character_behavior(self.handle)

    @no_character_behavior.setter
    def no_character_behavior(self, value: AsposePDFPython.NoCharacterAction):
        AsposePDFPython.text_text_edit_options_set_no_character_behavior(self.handle, value)

    @property
    def font_replace_behavior(self) -> AsposePDFPython.FontReplace:
        '''Gets mode that defines behavior for fonts replacement scenarios.'''
        return AsposePDFPython.text_text_edit_options_get_font_replace_behavior(self.handle)

    @font_replace_behavior.setter
    def font_replace_behavior(self, value: AsposePDFPython.FontReplace):
        AsposePDFPython.text_text_edit_options_set_font_replace_behavior(self.handle, value)

    @property
    def allow_language_transformation(self) -> bool:
        '''Gets or sets value that permits usage of language transformation during adding or editing of text.
        true - language transformation will be applied if necessary (default value).
        false - language transformation will NOT be applied.'''
        return AsposePDFPython.text_text_edit_options_get_allow_language_transformation(self.handle)

    @allow_language_transformation.setter
    def allow_language_transformation(self, value: bool):
        AsposePDFPython.text_text_edit_options_set_allow_language_transformation(self.handle, value)

    @property
    def language_transformation_behavior(self) -> AsposePDFPython.LanguageTransformation:
        '''Gets mode that defines behavior for language transformation scenarios.'''
        return AsposePDFPython.text_text_edit_options_get_language_transformation_behavior(self.handle)

    @language_transformation_behavior.setter
    def language_transformation_behavior(self, value: AsposePDFPython.LanguageTransformation):
        AsposePDFPython.text_text_edit_options_set_language_transformation_behavior(self.handle, value)

    @property
    def clipping_paths_processing(self) -> AsposePDFPython.ClippingPathsProcessingMode:
        '''Gets mode for processing clipping path of the edited text.'''
        return AsposePDFPython.text_text_edit_options_get_clipping_paths_processing(self.handle)

    @clipping_paths_processing.setter
    def clipping_paths_processing(self, value: AsposePDFPython.ClippingPathsProcessingMode):
        AsposePDFPython.text_text_edit_options_set_clipping_paths_processing(self.handle, value)

    @property
    def to_attempt_get_underline_from_source(self) -> bool:
        '''Gets or sets value that permits searching for text underlining on the page of source document.
        (Obsolete) Please use TextSearchOptions.SearchForTextRelatedGraphics instead this.'''
        return AsposePDFPython.text_text_edit_options_get_to_attempt_get_underline_from_source(self.handle)

    @to_attempt_get_underline_from_source.setter
    def to_attempt_get_underline_from_source(self, value: bool):
        AsposePDFPython.text_text_edit_options_set_to_attempt_get_underline_from_source(self.handle, value)
