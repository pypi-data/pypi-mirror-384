import AsposePDFPython


class TextWriter:
    '''
    A base class for classes that represent writers that writes sequences of characters to different destinations.
    Objects of this class should only be allocated using System::MakeObject() function.
    Never create instance of this type on stack or using operator new, as it will result in runtime errors and/or assertion faults.
    Always wrap this class into System::SmartPtr pointer and use this pointer to pass it to functions as argument.
    '''
