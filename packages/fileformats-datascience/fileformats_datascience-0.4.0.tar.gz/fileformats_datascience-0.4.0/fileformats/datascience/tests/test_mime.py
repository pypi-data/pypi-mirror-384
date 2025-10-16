from fileformats.core import from_mime
from fileformats.datascience import Pickle___Gzip


def test_native_container_roundtrip() -> None:

    mime = Pickle___Gzip.mime_like
    assert Pickle___Gzip is from_mime(mime)
