def test_import():
    import ncsc
    assert hasattr(ncsc, "__version__")
