def test_import_app():
    import app  # noqa: F401


def test_version_is_string():
    import app

    assert isinstance(app.__version__, str)
    assert app.__version__
