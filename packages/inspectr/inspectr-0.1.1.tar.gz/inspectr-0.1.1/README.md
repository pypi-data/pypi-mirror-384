# inspectr
A collection of python tools to inspect code quality.

## Installation
```bash
python -m venv .venv/
source .venv/bin/activate
pip install inspectr
```

## Usage
Generally, the syntax goes:
```bash
inspectr <subtool> [options] [files...]
```
where `<subtool>` is one of the following:

- `authenticity`: looks for TODO comments, empty try/except blocks, and stub functions
- `bare_ratio`: checks for the ratio of bare excepts to meaningful exception usage
- `compare_funcs`: compares function/method names across two directory versions
- `complexity`: analyzes algorithmic complexity of Python code
- `count_exceptions`: counts how many of each type of exception there are (including bare except)
- `duplicates`: looks for occurrences of duplicate or similar code (>80% similarity, default: 10+ lines, 3+ occurrences)
- `size_counts`: various linecount-related code complexity checks
- `with_open`: checks for `open` in the absense of `with` and manual calls to `close()`

### Command-Line Options
All tools accept command-line options in the format `--option-name value`. 
Options are passed as keyword arguments to the tool's main function. For example:
```bash
inspectr duplicates --block-size 15 --min-occur 2 file1.py file2.py
```

Recognized options include:
- `duplicates`:
  - `--block-size N`: number of consecutive lines in a block (default: 10)
  - `--min-occur N`: minimum number of occurrences to report (default: 3

**Note**: any unrecognized options will be silently ignored.

### Usage for compare_funcs
The `compare_funcs` tool compares functions across two directory versions:
```bash
inspectr compare_funcs files_list.txt dir1 dir2
```
where `files_list.txt` contains relative paths to compare, one per line.

## Local Testing
First install in development mode with test dependencies, then run the tests:
```bash
git clone https://github.com/ajcm474/inspectr.git
cd inspectr
pip install -e ".[test]"
pytest tests/
```

**Please note:** this project is in the early alpha stage, so don't expect the above subtool names 
to be stable between versions. I might even merge/split them at some point.
