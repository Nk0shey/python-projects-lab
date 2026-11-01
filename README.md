# Python Projects Lab

**Four small console applications, developed from university exercises.**

By [Nikita Kozchenko](https://github.com/Nk0shey) · Computer Engineering student, University of Catania

Python 3.10+ · Standard library only · CSV & JSON · Manual algorithms · Automated tests

[Quick start](#quick-start) · [The projects](#the-projects) · [Tests](#tests) · [Design notes](docs/DESIGN.md) · [Development history](docs/CHANGES.md)

---

This collection develops four of my Python practice exercises into runnable, tested applications. It focuses on completing a workflow: read and validate data, apply the rules, produce a result and save it reliably. Italian function names retain the connection to the original exercises; documentation is in English.

## The projects

### 01 · Library manager

A single-copy catalogue with members, loans, returns and a persistent JSON archive.

- Case-insensitive lookup and duplicate detection.
- Up to three simultaneous loans per member.
- Borrowed books and members with outstanding loans cannot be deleted.
- Archive validation checks that availability agrees with every member's loans.
- Successful changes are saved automatically; a failed save rolls back the in-memory change.

[Source](python_lab/library.py) · [Data format and rules](docs/DESIGN.md#library)

### 02 · Account records

A local CSV record manager that completes the assignment's three manual sorting algorithms:

- Shaker sort: opening date, oldest first.
- Insertion sort: balance, highest first.
- Bubble sort: surname and first name.

Dates are validated and normalized; monetary values use `Decimal`. CSV import, adding records and backup export are available through a menu. This is an account-record sorting exercise, with no real banking connection.

[Source](python_lab/bank.py) · [Data format and rules](docs/DESIGN.md#account-records)

### 03 · Exam reports

Join student and exam files, build passing-exam histories and export averages for students with at least three passing records. Invalid rows are skipped, following the supplied assignment; exact duplicate records are counted once.

[Source](python_lab/exams.py) · [Data format and rules](docs/DESIGN.md#exam-reports)

### 04 · Sales analysis

Calculate product revenue and export the most-sold products using a manually maintained top-k list. Ranking is by units sold; tied products use alphabetical name order. Decimal arithmetic preserves values such as `0.10 × 3 = 0.30`.

[Source](python_lab/sales.py) · [Data format and rules](docs/DESIGN.md#sales-analysis)

## Quick start

Clone this repository and run commands from its root. No installation or third-party packages are required.

```sh
git clone https://github.com/Nk0shey/python-projects-lab.git
cd python-projects-lab
python --version
```

On systems where Python 3 is named `python3`, use that instead of `python` below.

**Sales report**

```sh
python -m python_lab.sales examples/products.csv --output topk.csv
```

```text
Products: 5 | Total revenue: EUR 275.00
Tea: 50 sold | EUR 60.00
Water: 50 sold | EUR 40.00
Coffee: 40 sold | EUR 100.00
Report: topk.csv
```

Use `--top 5` to export five products instead of three.

**Exam report**

```sh
python -m python_lab.exams examples/students.csv examples/exams.csv --output averages.txt
```

The report contains:

```text
S001: 29.00
S003: 18.67
```

Use `--minimum 2` to change the minimum passing-record count.

**Library**

Copy the example once, then launch the menu:

```sh
python -c "import shutil; shutil.copyfile('examples/library.json', 'library.json')"
python -m python_lab.library --data library.json
```

The example includes three books and `Demo Reader`. Select **5** to borrow `The Hobbit` for `Demo Reader`, **8** to inspect the member's loans, **6** to return it, and **11** to exit. Run the application again to check persistence. Copying the example again resets the working archive.

To start with an empty library, use a nonexistent archive path instead. Existing malformed archives produce an error and are preserved.

**Account records**

```sh
python -m python_lab.bank --input examples/accounts.csv --output backup.csv
```

Select **1** to load, **2** to display, **3** to add a record, **4–6** to sort, **7** to save and **0** to exit. Changes are saved only when you choose **7**. Failed reloads retain the current records.

Each application supports `--help`. Output paths are relative to the working directory. Report commands reject an output path equal to an input path. Successful exports replace any previous report at the requested output path.

## Tests

```sh
python -m unittest discover -s tests -v
```

The suite currently has **60 test methods**, including:

- Loans, returns at the borrowing limit and cross-record archive consistency.
- CSV/JSON round trips, missing inputs and malformed records.
- Manual sorting and top-k results compared with reference implementations over deterministic generated cases.
- Decimal calculations, report thresholds and exact example outputs.
- Every menu operation and report command, including separate-process persistence checks.
- Interrupted writes, failed saves, reload recovery and import side effects.

Tests use isolated temporary directories. They do not change the example files. Validation was performed on Linux with Python 3.12; the source targets Python 3.10+. Other versions and operating systems have not been verified.

## Structure

- `python_lab/`: four application modules and shared validation/output helpers.
- `examples/`: fictional demonstration data, including intentionally invalid exam rows.
- `tests/`: standard-library unit and command-line integration tests.
- `docs/`: rules, design decisions, corrections and source provenance.

This is a student portfolio collection. It demonstrates small local applications; its passing tests do not establish correctness for every input or suitability for production use. See [design notes](docs/DESIGN.md) for boundaries and explicit choices.
