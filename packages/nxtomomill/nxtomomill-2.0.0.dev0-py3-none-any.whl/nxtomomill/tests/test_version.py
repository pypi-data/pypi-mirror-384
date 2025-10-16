# coding: utf-8


def test_version():
    from nxtomomill import version

    assert isinstance(version.version, str)
