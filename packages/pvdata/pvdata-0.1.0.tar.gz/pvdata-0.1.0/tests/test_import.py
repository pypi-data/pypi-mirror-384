"""
Test basic package import and version
"""


def test_import_pvdata():
    """Test that pvdata can be imported"""
    import pvdata

    assert pvdata is not None


def test_version():
    """Test that version is accessible"""
    import pvdata

    assert hasattr(pvdata, "__version__")
    assert isinstance(pvdata.__version__, str)
    assert pvdata.__version__ == "0.1.0"


def test_version_info():
    """Test version info tuple"""
    from pvdata.__version__ import __version_info__

    assert isinstance(__version_info__, tuple)
    assert len(__version_info__) == 3
    assert __version_info__ == (0, 1, 0)
