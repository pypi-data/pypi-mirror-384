import AsposePDFPython
import AsposePDFPythonWrappers.sys.io.stream


class FileStream(AsposePDFPythonWrappers.sys.io.stream.Stream):
    '''Represents a file stream supporting synchronous and asynchronous read and write operations.'''

    def __init__(self, path: str, mode: AsposePDFPython.FileMode):
        '''Constructs a new instance of FileStream class and initializes it with the specified parameters.
        :param: str: The path of the file to open.
        :param: mode: Specifies the mode in which to open the file.'''
        super().__init__(AsposePDFPython.sys_io_file_stream_create(path, mode))

    def __del__(self):
        '''Close handle.'''
        super().__del__()
