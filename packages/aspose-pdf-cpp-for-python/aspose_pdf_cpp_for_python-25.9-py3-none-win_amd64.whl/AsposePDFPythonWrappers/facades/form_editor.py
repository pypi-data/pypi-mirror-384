import AsposePDFPython
import AsposePDFPythonWrappers.facades.saveable_facade
import AsposePDFPythonWrappers.facades.form_field_facade
import AsposePDFPythonWrappers.document
import AsposePDFPythonWrappers.sys.io.stream
import AsposePDFPythonWrappers.sys.web.http_response

from typing import overload


class FormEditor(AsposePDFPythonWrappers.facades.saveable_facade.SaveableFacade):
    ''' Class for editing forms (ading/deleting field etc) '''

    @overload
    def __init__(self):
        ''' Initializes new :class:`FormEditor` object. '''
        ...

    @overload
    def __int__(self, document: AsposePDFPythonWrappers.document.Document):
        ''' Initializes new :class:`FormEditor` object from Document object. '''
        ...

    def __init__(self, *args):
        if len(args) == 0:
            super().__init__(AsposePDFPython.facades_formeditor_create())
        elif len(args) == 1:
            if isinstance(args[0], AsposePDFPythonWrappers.document.Document):
                super().__init__(AsposePDFPython.facades_formeditor_create_from_document(args[0].handle))
        else:
            raise TypeError("Invalid number of arguments.")

    def __del__(self):
        super().__del__()

    @property
    def src_file_name(self) -> str:
        '''Gets or sets name of source file.'''
        return AsposePDFPython.facades_formeditor_get_src_file_name(self.handle)

    @src_file_name.setter
    def src_file_name(self, value: str):
        '''Sets name of source file.'''
        AsposePDFPython.facades_formeditor_set_src_file_name(self.handle, value)

    @property
    def dest_file_name(self) -> str:
        '''Gets or sets destination file name.'''
        return AsposePDFPython.facades_formeditor_get_dest_file_name(self.handle, self.handle)

    @dest_file_name.setter
    def dest_file_name(self, value: str):
        '''Sets destination file name.'''
        AsposePDFPython.facades_formeditor_set_dest_file_name(self.handle, value)

    @property
    def src_stream(self) -> AsposePDFPythonWrappers.sys.io.stream.Stream:
        '''Gets or sets source stream.'''
        return AsposePDFPythonWrappers.sys.io.stream.Stream(AsposePDFPython.facades_formeditor_get_src_stream(self.handle))

    @src_stream.setter
    def src_stream(self, value: AsposePDFPythonWrappers.sys.io.stream.Stream):
        '''Sets source stream.'''
        AsposePDFPython.facades_formeditor_set_src_stream(self.handle, value.handle)

    @property
    def dest_stream(self) -> AsposePDFPythonWrappers.sys.io.stream.Stream:
        '''Gets or sets destination stream.'''
        return AsposePDFPythonWrappers.sys.io.stream.Stream(AsposePDFPython.facades_formeditor_get_dest_stream(self.handle))

    @dest_stream.setter
    def dest_stream(self, value: AsposePDFPythonWrappers.sys.io.stream.Stream):
        '''Sets destination stream.'''
        AsposePDFPython.facades_formeditor_set_dest_stream(self.handle, value.handle)

    @property
    def convert_to(self):
        ''' Set ONLY property '''
        raise AttributeError("This property is write-only.")  # Prevent readin

    @convert_to.setter
    def convert_to(self, value: AsposePDFPython.PdfFormat):
        ''' Sets PDF file format. Result file will be saved in specified file format.
        If this property is not specified then file will be save in default PDF format without conversion.'''
        AsposePDFPython.facades_formeditor_set_convert_to(self.handle, value)

    @property
    def items(self) -> list[str]:
        '''Sets items which will be added t onewly created list box or combo box.'''
        return AsposePDFPython.facades_formeditor_get_items(self.handle)

    @items.setter
    def items(self, value: list[str]):
        '''Sets items which will be added t onewly created list box or combo box.'''
        AsposePDFPython.facades_formeditor_set_items(self.handle, value)

    @property
    def export_items(self) -> list[list[str]]:
        '''Sets options for combo box with export values.'''
        return AsposePDFPython.facades_formeditor_get_export_items(self.handle)

    @export_items.setter
    def export_items(self, value: list[list[str]]):
        '''Sets options for combo box with export values.'''
        AsposePDFPython.facades_formeditor_set_export_items(self.handle, value)

    @property
    def facade(self) -> AsposePDFPythonWrappers.facades.form_field_facade.FormFieldFacade:
        '''Sets visual attributes of the field.'''
        return AsposePDFPythonWrappers.facades.form_field_facade.FormFieldFacade(
            AsposePDFPython.facades_formeditor_get_facade(self.handle))

    @facade.setter
    def facade(self, value: AsposePDFPythonWrappers.facades.form_field_facade.FormFieldFacade):
        '''Sets visual attributes of the field.'''
        AsposePDFPython.facades_formeditor_set_facade(self.handle, value.handle)

    @property
    def radio_gap(self) -> float:
        '''Get the member to record the gap between two neighboring radio buttons in pixels,default is 50.'''
        return AsposePDFPython.facades_formeditor_get_radio_gap(self.handle)

    @radio_gap.setter
    def radio_gap(self, value: float):
        '''Set the member to record the gap between two neighboring radio buttons in pixels,default is 50.'''
        AsposePDFPython.facades_formeditor_set_radio_gap(self.handle, value)

    @property
    def radio_horiz(self) -> bool:
        '''Get the flag to indicate whether the radios are arranged horizontally or vertically, default value is true.'''
        return AsposePDFPython.facades_formeditor_get_radio_horiz(self.handle)

    @radio_horiz.setter
    def radio_horiz(self, value: bool):
        '''Set the flag to indicate whether the radios are arranged horizontally or vertically, default value is true.'''
        AsposePDFPython.facades_formeditor_set_radio_horiz(self.handle, value)

    @property
    def radio_button_item_size(self) -> float:
        '''Gets or sets size of radio button item size (when new radio button field is added).
        formEditor = new Aspose.Pdf.Facades.FormEditor("PdfForm.pdf", "FormEditor_AddField_RadioButton.pdf");
        formEditor.RadioGap = 4;
        formEditor.RadioHoriz = false;
        formEditor.RadioButtonItemSize = 20;
        formEditor.Items = new string[] { "First", "Second", "Third" };
        formEditor.AddField(FieldType.Radio, "AddedRadioButtonField", "Second", 1, 10, 30, 110, 130);
        formEditor.Save();'''
        return AsposePDFPython.facades_formeditor_get_radio_button_item_size(self.handle)

    @radio_button_item_size.setter
    def radio_button_item_size(self, value: float):
        '''Sets or sets size of radio button item size (when new radio button field is added).'''
        AsposePDFPython.facades_formeditor_set_radio_button_item_size(self.handle, value)

    @property
    def submit_flag(self) -> AsposePDFPython.SubmitFormFlag:
        '''Get the submit button's submission flags'''
        return AsposePDFPython.facades_formeditor_get_content_disposition(self.handle)

    @submit_flag.setter
    def submit_flag(self, value: AsposePDFPython.SubmitFormFlag):
        '''Set the submit button's submission flags'''
        AsposePDFPython.facades_formeditor_set_content_disposition(self.handle, value)

    @property
    def content_disposition(self) -> AsposePDFPython.ContentDisposition:
        '''Gets how content will be stored when result of operation is stored into HttpResponse object. Possible value: inline / attachment.'''
        return AsposePDFPython.facades_formeditor_get_content_disposition(self.handle)

    @content_disposition.setter
    def content_disposition(self, value: AsposePDFPython.ContentDisposition):
        '''Sets how content will be stored when result of operation is stored into HttpResponse object. Possible value: inline / attachment.'''
        AsposePDFPython.facades_formeditor_set_content_disposition(self.handle, value)

    @property
    def response(self) -> AsposePDFPythonWrappers.sys.web.http_response.HttpResponse:
        '''Gets Response object where result of operation will be stored.'''
        return AsposePDFPython.facades_formeditor_get_response(self.handle)

    @response.setter
    def response(self, value: AsposePDFPythonWrappers.sys.web.http_response.HttpResponse):
        '''Sets Response object where result of operation will be stored.'''
        AsposePDFPython.facades_formeditor_set_response(self.handle, value)



