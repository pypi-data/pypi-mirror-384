# pyproteum

*A mutation testing toolkit for Python. Implemented as a Python module.*


*It is based on Proteum (Program Testing Using Mutants) , the first widely used mutation tool, developed for C.*

*https://link.springer.com/book/10.1007/978-1-4757-5939-6*


> **Status:** early preview — core mutation operators are available; more coming soon.

> **V0.1.2** 

> - Bug fixing: operator ccsr

> **V0.1.3** 

> - Monthly review

>- Bug fixing  
 
> - Color in the stdout

> - Improved speed for mutant generation and execution

> - Fix source files in different directories like: `--S tests/test_foo.py`

> **V0.1.4** 

>- Bug fixing (mutants were generated with different numbers due to unordered sets) 


---

## Features

- Parse Python source code and generate mutants using configurable operators
- Run your test suite against each mutant (kill/survive reporting)
- Simple CLI 

## Requirements

- Python >= 3.10  
- Dependencies: `timeout-decorator`, `peewee`  
  *(Note: `pickle` is part of the Python standard library and does not need to be installed.)*

## Installation

### From PyPI
```bash
pip install pyproteum
```


# pyproteum — Command Line Guide

`pyproteum` uses the concept of a **test session**.  
To use the tool, follow these steps:

1. **Create a test session** specifying which source files will be tested (mutated).
2. **Add test cases** from `unittest` test files.
3. **Generate mutants** from the selected source files.
4. **Execute the generated mutants** against the test cases.

This cycle can be repeated multiple times — you can remove existing test cases, add new ones, and generate additional mutants as needed.



## Mutation operators (currently implemented)

| Name | Description |
|------|-------------|
| cccr | Constant by Constant Replacement |
| ccsr | Constant by Scalar Replacement |
| crcr | Required Constant Replacement |
| oaaa | Replace arithmetic assignment operator by other arithmetic assignment operator |
| oaan | Replace arithmetic operator by other arithmetic operator |
| oeap | Replace augmented assignment by plain assignment |
| oodl | Operator deletion |
| orrn | Replace relational operator (<, >, <=, >=, ==, !=) by other relational operator |
| sbrc | Replace each break statement by a continue statement |
| scrb | Replace each continue statement by a break statement |
| ssdl | Replace each statement by a pass statement |

> **Notes**  
>  `crcr` replaces literals with a small, meaningful set of alternative constants (e.g., `-1`, `0`, `1`, for integers).


## Configuration tips

- Start with a small set of operators (e.g., `orrn,crcr`) to get quick feedback.
- Scope your target to the most critical modules first to keep the run time manageable.


## Command-line tools

`pyproteum` provides 5 main subcommands:

### 1. `testnew` — Create a new test session

```bash
python -m pyproteum testnew --D /home/user/proteum --S foo.py foo_session
```

- Creates a test session in the specified directory (`--D`) for the file `foo.py`, naming the session `foo_session`.

- **`--D`**: base directory where the session will be created. All file names are relative to this directory.  
  Example: the source file in this case would be `/home/user/proteum/foo.py`.
- **`--S`**: specifies the source file(s) to be mutated; can be repeated multiple times.  
  If not provided, defaults to `<session_name>.py`.

- **`--test`** or **`--research`**: exactly one must be used.
  >`--test`: each mutant is executed until the first test case kills it.  
  >`--research`: each mutant is executed against *all* test cases in the session.  
  > If omitted, `--test` is assumed.

---

### 2. `tcase` — Manage test case files in a session

Add a `unittest` test file:
```bash
python -m pyproteum tcase --add --D /home/user/proteum --S test_foo.py foo_session
```

Remove a test file:
```bash
python -m pyproteum tcase --del --D /home/user/proteum --S test_foo.py foo_session
```

List all test files and test cases in a session:
```bash
python -m pyproteum tcase --list --D /home/user/proteum foo_session
```

---

### 3. `mutagen` — Generate mutants

Generate mutants for all operators:
```bash
python -m pyproteum mutagen --create --D /home/user/proteum foo_session
```

Generate only `ssdl` mutants, with 50% random sampling:
```bash
python -m pyproteum mutagen --create --D /home/user/proteum --ssdl 50 foo_session
```

Notes:

- You can specify multiple operators in the same command.
- You can use `--all` to sample all operators.
- You can specify a seed for sampling, Using the same seed generates the same mutants. Use: `--seed <integer number>.` 
- Partial operator names are allowed. For example, `--c` selects all constant-related operators (those starting with `c`).
- Operators are scanned in the order they appear in the command line. `--all 100 --ssdl 0` generate 100% for all operators, except for ssdl.


---

### 4. `exemuta` — Execute mutants

Run generated mutants against the current test set:
```bash
python -m pyproteum exemuta --exec --D /home/user/proteum foo_session
```
Set mutants as equivalents:
```bash
python -m pyproteum exemuta --equiv --D /home/user/proteum --x "1 4 44" foo_session
```
- If ``--x`` is not provided, all live mutants are set as equivalent.

Generate a CSV table of results:
```bash
python -m pyproteum exemuta --csv --D /home/user/proteum --O foo.csv foo_session
```

- Each row corresponds to a mutant; each column corresponds to a test case.
- **`--O`** sets the CSV output filename. If omitted, defaults to `<session_name>.csv`.

---

### 5. `mutaview` — View mutants

Show original vs. mutated code in the terminal:
```bash
python -m pyproteum mutaview --view --D /home/user/proteum --x 1 foo_session
```
- `--x` specifies the mutant number to display. It can be a list of numbers like --x "1 2 3 4 5".

Generate a `.py` file with the mutant's code:
```bash
python -m pyproteum mutaview --build --D /home/user/proteum --x 1 foo_session
```

- The output file will be named `foo_session_mutant0001.py` in this example.


List all mutants and their current status
```bash
python -m pyproteum mutaview --list --D /home/user/proteum foo_session
``` 

Show mutants in a GUI interface. Allows to compare with original code and set mutant as equivalent.
```bash
python -m pyproteum mutaview --gui --D /home/user/proteum foo_session
``` 

---

## Color output

If you want to use color in pyproteum stdout, do:

``export PYPROTEUMCOLOR=``

Error messages and mutated code will appear in different colors.

---

## Workflow summary

1. `testnew` → create a session  
2. `tcase` → add/remove/list test files  
3. `mutagen` → generate mutants  
4. `exemuta` → execute mutants & get results  
5. `mutaview` → inspect mutants


## Contributing

Contributions are welcome! Please open an issue describing the change you’d like to make or the bug you found. If you’re adding a new operator, include:

1. Operator name, short key, and rationale
2. AST node types affected and transformation rules
3. Unit tests that both generate the mutant and exercise its effects

## License

MIT 

## Citation

If this toolkit helps your research or teaching, consider citing the project as:

```
Delamaro, M. (2025). pyproteum: a mutation testing toolkit for Python. Version 0.1.
```

---

Questions, ideas, or bugs? Open an issue or ping us .
