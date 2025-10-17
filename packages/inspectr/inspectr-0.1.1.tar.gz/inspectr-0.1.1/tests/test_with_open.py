import tempfile
import pathlib
import pytest
from inspectr.with_open import main


def test_open_with_with_statement(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("with open('file.txt') as f:\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "outside with" not in output
    finally:
        path.unlink()


def test_open_without_with(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("f = open('file.txt')\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "outside with" in output
    finally:
        path.unlink()


def test_no_open_calls(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "outside with" not in output
    finally:
        path.unlink()


def test_validates_file_exists(capsys):
    path = pathlib.Path("/nonexistent/file.py")
    main([path])
    output = capsys.readouterr().out
    assert "does not exist" in output


def test_empty_files_list():
    with pytest.raises(SystemExit):
        main([])


def test_multiple_files(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
        f1.write("f = open('file.txt')\n")
        path1 = pathlib.Path(f1.name)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
        f2.write("with open('file.txt') as f:\n    pass\n")
        path2 = pathlib.Path(f2.name)
    
    try:
        main([path1, path2])
        output = capsys.readouterr().out
        assert str(path1) in output and "outside with" in output
    finally:
        path1.unlink()
        path2.unlink()
