import tempfile
import pathlib
import pytest
from io import StringIO
import sys
from inspectr.authenticity import main


def test_detects_todo_comments(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("# TODO: fix this\n")
        f.write("def foo(): pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "TODO comments: 1" in output
    finally:
        path.unlink()


def test_detects_stub_with_pass(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def stub():\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Stub functions/methods: 1" in output
        assert "stub" in output
    finally:
        path.unlink()


def test_detects_stub_with_docstring_only(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def stub():\n    """Docstring"""\n')
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Stub functions/methods: 1" in output
    finally:
        path.unlink()


def test_detects_stub_with_return_none(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def stub():\n    return\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Stub functions/methods: 1" in output
    finally:
        path.unlink()


def test_not_stub_with_real_code(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def real():\n    return 42\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Stub functions/methods: 0" in output
    finally:
        path.unlink()


def test_validates_file_exists(capsys):
    path = pathlib.Path("/nonexistent/file.py")
    main([path])
    output = capsys.readouterr().out
    assert "does not exist" in output


def test_handles_syntax_errors(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def broken(\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Analysis results:" in output
    finally:
        path.unlink()


def test_empty_file(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "TODO comments: 0" in output
    finally:
        path.unlink()
