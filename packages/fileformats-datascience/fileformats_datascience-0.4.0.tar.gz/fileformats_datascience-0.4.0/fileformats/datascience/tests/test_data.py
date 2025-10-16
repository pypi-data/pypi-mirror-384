from fileformats.datascience import Hdf5, MatFile, RData


def test_hdf5(tmp_path):
    import h5py

    tmp_fspath = tmp_path / "a-file.h5"

    with h5py.File(tmp_fspath, 'w') as f:
        f['dataset'] = range(10)

    Hdf5(tmp_fspath)


def test_mat_file(tmp_path):
    import scipy.io

    tmp_fspath = tmp_path / "a-file.mat"

    scipy.io.savemat(tmp_fspath, {"some": [1, 2, 3], "data": [[99, 100], [101, 102]]})

    MatFile(tmp_fspath)


def test_rdata_file(tmp_path):
    from rpy2 import robjects
    from rpy2.robjects import r

    tmp_fspath = tmp_path / "a-file.rData"

    # Create some dummy data in Python
    data_list = [1, 2, 3, 4, 5]
    data_matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    # Convert Python objects to R objects
    r_data_list = robjects.vectors.FloatVector(data_list)
    r_data_matrix = r.matrix(robjects.vectors.FloatVector(sum(data_matrix, [])), nrow=len(data_matrix))

    # Create an R environment to store the objects
    r_env = robjects.Environment()

    # Assign the R objects to the R environment with names "data_list" and "data_matrix"
    r_env["data_list"] = r_data_list
    r_env["data_matrix"] = r_data_matrix

    robjects.r(f'save.image(file="{tmp_fspath}")')

    RData(tmp_fspath)
