import pip_importer


def test_pip_import_exists():
    assert pip_importer.pip_import  # type: ignore


def test_pip_import_can_import_package():
    m = pip_importer.pip_import("sys")
    import sys

    assert m == sys


def test_pip_import_can_import_package_2():
    m = pip_importer.pip_import("termcolor")
    import termcolor  # type: ignore

    assert m == termcolor
