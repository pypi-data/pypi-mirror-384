import pickle as pkl
from fileformats.datascience import Pickle


def test_pickle(tmp_path):

    fspath = tmp_path / "a-file.pkl"
    with open(fspath, "wb") as f:
        pkl.dump(["some", "test", "data", 100], f)

    Pickle(fspath)
