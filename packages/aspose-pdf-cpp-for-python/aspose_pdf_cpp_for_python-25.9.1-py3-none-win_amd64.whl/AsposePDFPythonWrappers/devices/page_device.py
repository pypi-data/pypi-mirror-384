import AsposePDFPython
import AsposePDFPythonWrappers.devices.device
import AsposePDFPythonWrappers.page
import AsposePDFPythonWrappers.sys.io.stream

from typing import overload


class PageDevice(AsposePDFPythonWrappers.devices.device.Device):
    '''Abstract class for all devices which is used to process certain page the pdf document.'''


    @overload
    def process(self, page: AsposePDFPythonWrappers.page.Page, output: AsposePDFPythonWrappers.sys.io.stream.Stream):
        '''Perfoms some operation on the given page, e.g. converts page into graphic image.

        :param page: The page to process.
        :param output: This stream contains the results of processing.'''
        ...


    @overload
    def process(self, page: AsposePDFPythonWrappers.page.Page, output_file_name: str):
        '''Perfoms some operation on the given page and saves results into the file.

        :param page: The page to process.
        :param output_file_name: This file contains the results of processing.'''
        ...

    def process(self, page: AsposePDFPythonWrappers.page.Page, arg):
        if isinstance(arg, AsposePDFPythonWrappers.sys.io.stream.Stream):
            AsposePDFPython.devices_page_device_process_with_stream(self.handle, page.handle, arg.handle)
        elif isinstance(arg, str):
            AsposePDFPython.devices_page_device_process_with_file(self.handle, page.handle, arg)
        else:
            raise TypeError("Invalid number of arguments.")
