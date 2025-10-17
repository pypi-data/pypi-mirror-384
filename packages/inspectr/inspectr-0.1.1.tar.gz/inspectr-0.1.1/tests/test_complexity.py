import tempfile
import pathlib
import pytest
from inspectr.complexity import Complexity, Analyzer, main


def test_complexity_constant():
    c = Complexity.constant()
    assert c.expression == "O(1)"
    assert not c.is_approximate


def test_complexity_linear():
    c = Complexity.linear()
    assert c.expression == "O(n)"
    assert not c.is_approximate


def test_complexity_linear_coefficient():
    c = Complexity.linear(3)
    assert c.expression == "O(3n)"
    assert not c.is_approximate


def test_complexity_combine_sequential():
    c1 = Complexity.linear()
    c2 = Complexity.linear()
    result = c1.combine_sequential(c2)
    assert "2n" in result.expression


def test_complexity_combine_sequential_with_constant():
    c1 = Complexity.linear()
    c2 = Complexity.constant()
    result = c1.combine_sequential(c2)
    assert result.expression == "O(n + 1)"


def test_complexity_combine_sequential_constants():
    c1 = Complexity.constant()
    c2 = Complexity.constant()
    result = c1.combine_sequential(c2)
    assert result.expression == "O(2)"


def test_complexity_combine_sequential_multiple():
    c1 = Complexity.linear(2)
    c2 = Complexity.linear(3)
    result = c1.combine_sequential(c2)
    assert result.expression == "O(5n)"


def test_complexity_combine_nested():
    c1 = Complexity.linear()
    c2 = Complexity.linear()
    result = c1.combine_nested(c2)
    assert result.expression == "O(n²)"


def test_complexity_combine_nested_with_constant():
    c1 = Complexity.linear()
    c2 = Complexity.constant()
    result = c1.combine_nested(c2)
    assert result.expression == "O(n)"


def test_complexity_combine_triple_nested():
    c1 = Complexity.linear()
    c2 = Complexity.linear()
    c3 = Complexity.linear()
    result = c1.combine_nested(c2).combine_nested(c3)
    assert result.expression == "O(n³)"


def test_complexity_max():
    c1 = Complexity("O(n)", False)
    c2 = Complexity("O(n²)", False)
    result = c1.max(c2)
    assert result.expression == "O(n²)"


def test_analyzer_simple_function():
    code = "def foo():\n    pass\n"
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert results[0].name == "foo"
    assert results[0].complexity.expression == "O(1)"


def test_analyzer_multiple_statements():
    code = """def foo():
    x = 1
    y = 2
    z = 3
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert results[0].complexity.expression == "O(3)"


def test_analyzer_for_loop():
    code = """def foo():
    for i in range(10):
        pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    # Should be O(n + 1) for the loop and the function itself
    assert "n" in results[0].complexity.expression


def test_analyzer_nested_loops():
    code = """def foo():
    for i in range(10):
        for j in range(20):
            pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert "n²" in results[0].complexity.expression


def test_analyzer_triple_nested_loops():
    code = """def foo():
    for i in range(10):
        for j in range(20):
            for k in range(30):
                pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert "n³" in results[0].complexity.expression


def test_analyzer_sequential_loops():
    code = """def foo():
    for i in range(10):
        pass
    for j in range(20):
        pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    # Should have 2n or similar (two sequential loops)
    assert "2n" in results[0].complexity.expression


def test_analyzer_mixed_loops():
    code = """def foo():
    x = 1
    for i in range(10):
        pass
    for j in range(20):
        for k in range(30):
            pass
    y = 2
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    # Should have n² + n + constants
    assert "n²" in results[0].complexity.expression
    assert "n" in results[0].complexity.expression


def test_analyzer_list_comprehension():
    code = """def foo():
    result = [i for i in range(10)]
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert "n" in results[0].complexity.expression
    assert len(results[0].anti_patterns) > 0


def test_analyzer_nested_list_comprehension():
    code = """def foo():
    result = [[i*j for i in range(10)] for j in range(20)]
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert "n²" in results[0].complexity.expression


def test_analyzer_builtin_sorted():
    code = """def foo():
    result = sorted([1, 2, 3])
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert "n*log(n)" in results[0].complexity.expression or "log" in results[0].complexity.expression


def test_analyzer_builtin_sum():
    code = """def foo():
    result = sum([1, 2, 3])
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert "n" in results[0].complexity.expression


def test_analyzer_membership_list():
    code = """def foo(items):
    if 5 in [1, 2, 3, 4, 5]:
        pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    # Should detect anti-pattern for list membership
    assert any(ap.pattern_type == "list_membership" for ap in results[0].anti_patterns)


def test_analyzer_membership_set():
    code = """def foo(items):
    if 5 in {1, 2, 3, 4, 5}:
        pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    # Should be constant for set membership
    assert results[0].complexity.expression == "O(2)"


def test_analyzer_if_statement():
    code = """def foo(x):
    if x > 5:
        for i in range(10):
            pass
    else:
        pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    # Should take the max of the branches (the loop)
    assert "n" in results[0].complexity.expression


def test_analyzer_while_loop():
    code = """def foo():
    i = 0
    while i < 10:
        i += 1
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    assert "n" in results[0].complexity.expression
    assert results[0].complexity.is_approximate


def test_analyzer_multiple_functions():
    code = """def foo():
    pass

def bar():
    for i in range(10):
        pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 2
    assert results[0].name == "foo"
    assert results[1].name == "bar"


def test_analyzer_class_methods():
    code = """class MyClass:
    def method1(self):
        pass
    
    def method2(self):
        for i in range(10):
            pass
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 2
    assert results[0].name == "MyClass.method1"
    assert results[1].name == "MyClass.method2"


def test_main_with_file(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Complexity Analysis" in output
        assert "foo" in output
    finally:
        path.unlink()


def test_main_nonexistent_file(capsys):
    path = pathlib.Path("/nonexistent/file.py")
    main([path])
    output = capsys.readouterr().out
    assert "does not exist" in output


def test_analyzer_syntax_error():
    code = "def broken(\n"
    analyzer = Analyzer()
    with pytest.raises(ValueError):
        analyzer.analyze_file(code)


def test_complexity_simplify():
    c = Complexity("O(n + n)", False)
    simplified = c.simplify()
    assert simplified.expression == "O(2n)"


def test_complexity_simplify_nested():
    c = Complexity("O(n*n)", False)
    simplified = c.simplify()
    assert "n²" in simplified.expression


def test_complexity_preserve_terms():
    """Test that lower-order terms are preserved"""
    code = """def foo():
    x = 1
    for i in range(10):
        y = 2
"""
    analyzer = Analyzer()
    results = analyzer.analyze_file(code)
    assert len(results) == 1
    # Should preserve both n and constant terms
    expr = results[0].complexity.expression
    assert "n" in expr
    # Check that we have both n and constant terms
    assert "+" in expr or ("n" in expr and any(char.isdigit() for char in expr))
