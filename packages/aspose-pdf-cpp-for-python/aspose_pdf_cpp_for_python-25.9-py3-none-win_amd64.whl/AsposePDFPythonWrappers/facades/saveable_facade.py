import AsposePDFPython
import AsposePDFPythonWrappers.facades.facade
import AsposePDFPythonWrappers.sys.io.stream


class SaveableFacade(AsposePDFPythonWrappers.facades.facade.Facade):
    ''' Base class for all saveable facades. '''

    def save_to_file(self, file_path: str):
        ''' Saves the PDF document to the specified file.

        :param file_path: Path to the file to save to. '''
        AsposePDFPython.facades_saveablefacade_save_to_file(self.handle, file_path)

    def save_to_stream(self, stream: AsposePDFPythonWrappers.sys.io.stream.Stream):
        ''' Saves the PDF document to the specified stream.

        :param stream: Stream to save to. '''
        AsposePDFPython.facades_saveablefacade_save_to_stream(self.handle, stream)