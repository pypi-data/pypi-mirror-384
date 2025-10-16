import typing as ty
from fileformats.core.exceptions import FormatMismatchError
from fileformats.image import RasterImage
from fileformats.core.mixin import WithMagicVersion


class Vtk(WithMagicVersion, RasterImage):
    """VTK image file format. as described at http://www.princeton.edu/~efeibush/viscourse/vtk.pdf"""

    magic_pattern = rb" #vtkDataFileVersion (\d).(\d)"
    binary = True
    ext = ".vtk"
    mime_types = (
        "application/x-vtk",
        "application/x-vtk-ascii",
        "application/x-vtk-binary",
    )

    def header_info(self) -> ty.Tuple[bytes, str]:
        """Return the header of the VTK file and its format.

        Returns
        -------
        header : bytes
            The header of the VTK file.
        format : str
            The format of the VTK file, either 'ascii' or 'binary'.
        """
        header_end: int = self.contents.find(b"\n")
        header: bytes = self.contents[:header_end]
        format_end: int = self.contents.find(b"\n", header_end + 1)
        contents_format = (
            self.contents[header_end:format_end].strip().decode("utf-8").lower()
        )
        if contents_format not in ("ascii", "binary"):
            raise FormatMismatchError(
                f"Unknown VTK format: {contents_format} (must be 'ascii' or 'binary')"
            )
        # type_end: int = self.contents.find(b'\n', format_end + 1)
        # type_str = self.contents[format_end:type_end].strip().decode("utf-8").lower()
        # match = re.match(r"(?<!\w)DATASET (\w+)", type_str)
        # if not match:
        #     raise FormatMismatchError(
        #         f"VTK file does not contain a DATASET type: {type_str}"
        #     )
        return header, contents_format
