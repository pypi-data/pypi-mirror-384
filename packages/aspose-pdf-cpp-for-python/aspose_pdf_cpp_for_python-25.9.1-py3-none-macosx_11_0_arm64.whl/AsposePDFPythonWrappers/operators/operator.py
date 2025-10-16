import AsposePDFPython

class Operator:
    '''Abstract class representing operator.'''
    def __init__(self, handle: AsposePDFPython.operators_operator_handle):
        self.handle = handle

    @property
    def index(self) -> int:
        '''Operator index in page operators list.'''
        return AsposePDFPython.operator_get_index(self.handle)

    def to_string(self) -> str:
        '''Return operator string'''
        return AsposePDFPython.operator_to_string(self.handle)