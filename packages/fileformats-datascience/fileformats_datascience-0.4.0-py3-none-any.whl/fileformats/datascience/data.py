from fileformats.core.mixin import WithMagicNumber
from fileformats.generic import UnicodeFile, BinaryFile


class Data:
    ...


class TextVector(Data, UnicodeFile):
    """space-delimited text file containing a single vector of values"""

    ...


class TextArray(Data, UnicodeFile):
    """space-delimited text file containing a 2-d array of values"""

    ...


class TextMatrix(Data, UnicodeFile):
    ext = ".mat"


class RData(WithMagicNumber, Data, BinaryFile):
    """Data-file created by the R statistical package"""

    ext = ".rData"
    binary = True
    magic_number = "1f8b0800"


class MatFile(WithMagicNumber, Data, BinaryFile):
    """MATLAB Mat-File (https://au.mathworks.com/help/matlab/import_export/mat-file-versions.html)"""

    ext = ".mat"
    magic_number = "4D41544C"


class DatFile(Data):
    """Generic binary data file"""

    ext = ".dat"


class Hdf5(WithMagicNumber, Data, BinaryFile):
    """Hierarchical Data Format (HDF) Version 5

    An open source file format that supports large, complex, heterogeneous data.
    HDF5 uses a "file directory" like structure that allows you to organize data within
    the file in many different structured ways, as you might do with files on your computer.
    """

    ext = ".h5"
    magic_number = "894844460d0a1a0a"


class VtkDataFile(WithMagicNumber, Data, BinaryFile):

    ext = ".vtk"
    magic_number = b"#vtk DataFile Version"
