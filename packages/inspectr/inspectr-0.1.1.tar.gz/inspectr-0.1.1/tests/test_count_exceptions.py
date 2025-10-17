import tempfile
import pathlib
import pytest
from inspectr.count_exceptions import main


def test_bare_except(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("try:\n    pass\nexcept:\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert str(path) in output and ": 1" in output
    finally:
        path.unlink()


def test_typed_except(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("try:\n    pass\nexcept ValueError:\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "ValueError" in output
    finally:
        path.unlink()


def test_multiple_exception_handlers(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("try:\n    pass\nexcept ValueError:\n    pass\nexcept KeyError:\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "ValueError" in output and "KeyError" in output
    finally:
        path.unlink()


def test_tuple_exceptions(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("try:\n    pass\nexcept (ValueError, KeyError):\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "ValueError" in output and "KeyError" in output
    finally:
        path.unlink()


def test_no_exceptions(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n    return 42\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Distinct exception types" in output
    finally:
        path.unlink()


def test_validates_file_exists(capsys):
    path = pathlib.Path("/nonexistent/file.py")
    main([path])
    output = capsys.readouterr().out
    assert "does not exist" in output


def test_handles_syntax_errors(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("try:\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Distinct exception types" in output
    finally:
        path.unlink()
