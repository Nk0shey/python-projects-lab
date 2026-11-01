# Rules and design notes

## Library

Each title represents one physical copy. Titles and member names are unique without regard to case; member email addresses must also be unique. Display names preserve the entered spelling. The email check only validates a minimal local-part/domain shape.

A member can borrow up to three books. Borrowing marks a book unavailable and stores its canonical title in the member's history. Returning is allowed at the borrowing limit, but only by its current borrower. A borrowed book cannot be removed, and a member cannot be removed while loans remain.

The JSON archive has exactly three top-level keys: `version` (integer 1), `books` and `members`. Book records use `titolo`, `autore`, `anno`, `disponibile`. Members use `nome`, `email`, `prestiti`. Loading and saving validate all records and loan relationships. Missing archives start empty; malformed archives fail without replacement.

Every successful menu mutation is saved immediately. If writing fails, the mutation is reverted in memory. The archive is replaced atomically after a complete write. This is a single-process local application: concurrent writers are not coordinated, and atomic replacement is not a power-loss durability guarantee. The programme has no authentication or multi-copy inventory model.

## Account records

CSV rows have no header and contain `first_name,last_name,opening_date,balance`. Quoted fields are supported. Dates accept `YYYY-MM-DD` and `DD/MM/YYYY`, then normalize to ISO format before sorting. Negative balances are permitted. Amounts must be finite, within ±999999999999.99 and expressible with two decimal places; additional nonzero decimal places are rejected rather than silently rounded.

Import is strict: one invalid record rejects the load. Reloading assigns the new list only after validation succeeds. Names are descriptive fields, so multiple accounts with the same name are allowed; no account IDs or transfers are implemented.

The assignment's algorithms are preserved: shaker sort by date, insertion sort by descending balance and bubble sort by case-insensitive surname/first name. Sorts mutate and return the input list, preserving the order of equal keys. Sorting functions expect records created or loaded through this module, with canonical dates and Decimal balances.

The menu starts empty and requires option 1 to import the selected CSV. Adding validates a complete record before modifying state. Option 7 exports a backup; exiting does not implicitly save. Backups preserve all four fields with canonical dates and two-decimal amounts.

## Exam reports

Input is the assignment's simple semicolon-separated text format, without headers or multiline/quoted fields:

- Students: `first_name;surname;student_id`.
- Exams: `student_id;exam_name;integer_grade`.

Whitespace around fields is stripped. Empty fields, malformed rows, control characters and invalid grades are ignored. The only accepted grades are integer 0 or integers 18–30. Decimal forms such as `18.0` are rejected. Grade 0 means a failed attempt and is excluded from passing histories.

For duplicate student IDs, the first valid student row wins. Exact duplicate exam tuples are counted once. Records with the same exam name but a different passing grade remain distinct records, consistent with the input's attempt-based representation; no rule for replacing repeated attempts was supplied. Unknown student IDs do not acquire a student record and are excluded from student reports.

Histories are replaced on recomputation, so repeated calls do not duplicate entries. The default threshold is at least three passing records, not three attempts including failures. `--minimum` is a positive integer. Averages use Decimal and round half up to two decimal places. Output is `student_id: average`, in student-file order. Empty datasets produce an empty report.

## Sales analysis

Input is headerless CSV: `product_name,unit_price,units_sold,remaining_stock`. CSV quoting is supported. Blank records are skipped. Empty names, duplicate case-insensitive product names, malformed fields, negative quantities and invalid monetary values reject the input. The unit-price rules match the account-record monetary rules, except negative prices are disallowed.

Revenue is `price × units_sold`. Remaining stock is validated separately; it is not a cap on units already sold. Sales rows describe distinct products, not repeat sale transactions. Supporting repeated product rows would require an explicit aggregation rule.

Top-k ranking is descending units sold, then case-insensitive product name and finally its original spelling. The algorithm maintains a bounded list using manual insertion, rather than sorting the full dataset. It takes O(nk) comparisons and O(k) extra space. For the original top-three task, k is 3. Exports contain `product_name,revenue`, without a header. Empty input produces total 0.00 and an empty report.

## Shared output behavior

Files are UTF-8. Writers create a temporary file in the destination directory and replace the destination only after writing and closing succeeds. Failed writes remove temporary files and preserve the old destination. The destination parent directory must already exist.

Batch report commands return exit status 1 with a short diagnostic for expected input/output errors; successful runs return 0. Interactive menus report recoverable errors and continue. EOF exits menus cleanly; incomplete add operations do not change state. Importing a module does not prompt, print or write data.

The apps use only Python's standard library. Dictionaries and lists retain the approachable style of the exercises. Shared code is limited to validation and output helpers; each application's business rules remain in its own module.
