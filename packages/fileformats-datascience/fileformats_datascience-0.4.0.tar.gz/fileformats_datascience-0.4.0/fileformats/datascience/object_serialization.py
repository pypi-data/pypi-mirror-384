from fileformats.generic import BinaryFile
from fileformats.core.mixin import WithMagicNumber
from fileformats.application import Gzip


class ObjectSerialisation(BinaryFile): ...


class Pickle(WithMagicNumber, ObjectSerialisation):
    """Python's native byte-encoded serialization format"""

    ext = ".pkl"
    magic_number = "8004"


class Pickle___Gzip(Gzip[Pickle]):  # type: ignore[type-arg]
    """Python pickle file that has been gzipped"""

    ext = "pkl.gz"
    alternate_exts = (".pklz",)
    iana_mime = "application/x-pickle+gzip"
