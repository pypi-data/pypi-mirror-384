import AsposePDFPython
import ctypes


class Stream:
    '''A base class for a variety of stream implementations.'''

    def __init__(self, handle):
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    def close(self):
        '''Closes the stream.'''
        AsposePDFPython.sys_io_stream_close(self.handle)

    def read_byte(self):
        '''Reads a single byte from the stream and returns a 32-bit integer value
        equivalent to the value of the read byte.'''
        return AsposePDFPython.sys_io_stream_read_byte(self.handle)

    def write_byte(self, value: ctypes.c_ubyte):
        '''Writes the specified unsigned 8-bit integer value to the stream.'''
        AsposePDFPython.sys_io_stream_write_byte(self.handle, value)