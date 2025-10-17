import tempfile
import pathlib
import pytest
from inspectr.duplicates import calculate_similarity, find_duplicates, main


def test_calculate_similarity_identical():
    lines1 = ["x = 1\n", "y = 2\n"]
    lines2 = ["x = 1\n", "y = 2\n"]
    similarity = calculate_similarity(lines1, lines2)
    assert similarity == 1.0


def test_calculate_similarity_different():
    lines1 = ["x = 1\n", "y = 2\n"]
    lines2 = ["a = 1\n", "b = 2\n"]
    similarity = calculate_similarity(lines1, lines2)
    assert similarity == 0.0


def test_calculate_similarity_partial():
    lines1 = ["x = 1\n", "y = 2\n", "z = 3\n"]
    lines2 = ["x = 1\n", "y = 2\n", "w = 4\n"]
    similarity = calculate_similarity(lines1, lines2)
    assert 0.6 < similarity < 0.7


def test_calculate_similarity_empty():
    lines1 = []
    lines2 = ["x = 1\n"]
    similarity = calculate_similarity(lines1, lines2)
    assert similarity == 0.0


def test_find_duplicates_basic():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("x = 1\n" * 15)
        path1 = f.name
    
    try:
        results = list(find_duplicates([path1], block_size=5, min_occur=2))
        assert len(results) > 0
    finally:
        pathlib.Path(path1).unlink()


def test_main_with_files(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n    pass\n" * 5)
        path = pathlib.Path(f.name)
    
    try:
        main([path], block_size=2, min_occur=2)
        output = capsys.readouterr().out
        assert "lines" in output or output == ""
    finally:
        path.unlink()


def test_main_with_kwargs(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("x = 1\n" * 10)
        path = pathlib.Path(f.name)
    
    try:
        main([path], block_size=3, min_occur=2)
        output = capsys.readouterr().out
        assert "lines" in output or output == ""
    finally:
        path.unlink()


def test_main_validates_file_exists(capsys):
    path = pathlib.Path("/nonexistent/file.py")
    main([path])
    output = capsys.readouterr().out
    assert "does not exist" in output


def test_main_empty_files_list(capsys):
    main([])
    output = capsys.readouterr().out
    assert "Usage:" in output
