from ._version import __version__
from pathlib import Path
import typing as ty
from fileformats.core import extra_implementation
from fileformats.datascience import TextMatrix

__all__ = ["__version__"]


@extra_implementation(TextMatrix.generate_sample_data)
def text_matrix_generate_sample_data(
    matrix: TextMatrix, dest_dir: Path
) -> ty.List[Path]:
    fspath = dest_dir / "text-matrix.mat"
    fspath.write_text("0 1 2 3 4 5\n10 11 12 13 14 15\n20 21 22 23 24 25\n")
    return [fspath]
