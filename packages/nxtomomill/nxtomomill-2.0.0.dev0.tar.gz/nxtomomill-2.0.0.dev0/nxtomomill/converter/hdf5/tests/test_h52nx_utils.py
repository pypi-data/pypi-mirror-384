from nxtomomill.converter.hdf5.utils import (
    get_default_output_file,
    PROCESSED_DATA_DIR_NAME,
    RAW_DATA_DIR_NAME,
)


def test_get_default_output_file():
    """
    test the get_default_output_file function
    """
    # 1. simple test
    assert get_default_output_file("/my_tmp/path/file.h5") == "/my_tmp/path/file.nx"
    assert (
        get_default_output_file(f"/my_tmp/{RAW_DATA_DIR_NAME}/file.h5")
        == f"/my_tmp/{PROCESSED_DATA_DIR_NAME}/file.nx"
    )

    assert (
        get_default_output_file(f"/my_tmp/path/{RAW_DATA_DIR_NAME}/toto/file.h5")
        == f"/my_tmp/path/{PROCESSED_DATA_DIR_NAME}/toto/file.nx"
    )
    # note: _RAW_DATA_DIR_NAME part of the path but not a folder
    assert (
        get_default_output_file(f"/my_tmp/path_{RAW_DATA_DIR_NAME}/toto/file.h5")
        == f"/my_tmp/path_{RAW_DATA_DIR_NAME}/toto/file.nx"
    )

    # 2. advance test
    # 2.1 use case: '_RAW_DATA_DIR_NAME' is present twice in the path -> replace the deeper one
    assert (
        get_default_output_file(
            f"/my_tmp/{RAW_DATA_DIR_NAME}/path/{RAW_DATA_DIR_NAME}/toto/file.h5"
        )
        == f"/my_tmp/{RAW_DATA_DIR_NAME}/path/{PROCESSED_DATA_DIR_NAME}/toto/file.nx"
    )

    # 2.2 use case: contains both '_RAW_DATA_DIR_NAME' and '_PROCESSED_DATA_DIR_NAME' in the path
    assert (
        get_default_output_file(
            f"/my_tmp/{RAW_DATA_DIR_NAME}/path/{PROCESSED_DATA_DIR_NAME}/toto/file.h5"
        )
        == f"/my_tmp/{RAW_DATA_DIR_NAME}/path/{PROCESSED_DATA_DIR_NAME}/toto/file.nx"
    )

    assert (
        get_default_output_file(
            f"/my_tmp/{PROCESSED_DATA_DIR_NAME}/path/{RAW_DATA_DIR_NAME}/toto/file.h5"
        )
        == f"/my_tmp/{PROCESSED_DATA_DIR_NAME}/path/{PROCESSED_DATA_DIR_NAME}/toto/file.nx"
    )

    # 2.3 use case: expected output file is the input file. Make sure append '_nxtomo'
    assert (
        get_default_output_file("/my_tmp/path/file.nx") == "/my_tmp/path/file_nxtomo.nx"
    )
