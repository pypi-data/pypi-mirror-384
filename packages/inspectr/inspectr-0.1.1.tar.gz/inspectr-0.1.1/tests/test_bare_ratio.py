import tempfile
import pathlib
import pytest
from inspectr.bare_ratio import main


def test_bare_except(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("try:\n    pass\nexcept:\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "1 bare / 0 typed" in output or "ratio = 1.00" in output
    finally:
        path.unlink()


def test_except_with_type(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("try:\n    pass\nexcept ValueError:\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "ValueError" in output
    finally:
        path.unlink()


def test_except_exception(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("try:\n    pass\nexcept Exception:\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "1 bare / 0 typed" in output or "ratio = 1.00" in output
    finally:
        path.unlink()


def test_multiple_exception_types(capsys):
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
        f.write("try:\n    pass\nexcept")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Distinct exception types" in output
    finally:
        path.unlink()
