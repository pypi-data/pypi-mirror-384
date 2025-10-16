from fileformats.text import Plain


class Script(Plain):
    iana_mime = None  # type: ignore[assignment]


class RFile(Script):
    """R statistical package script file"""

    ext = ".r"


class IPythonNotebook(Script):
    """Jupyter notebook"""

    ext = ".ipynb"
