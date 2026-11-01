# From exercises to applications

## Scope

Four selected works were developed from the supplied training archives. Tiny standalone drills, unrelated exercises, duplicate archives and unfinished gym credentials/pickle code are not part of this repository.

## Library

Repaired the original wrong dictionary key during borrowing, swapped arguments, incorrect member-registration call, early returns in searches/deletion, incorrect availability filtering and newline formatting. Returns no longer fail when a member has three loans. Deleting records now respects outstanding loans. Added duplicate checks, input validation and JSON persistence with cross-record validation and failed-save rollback.

## Account records

Completed the empty sorting functions with the requested algorithms, implemented CSV backup and connected every menu option. Added CSV field validation, real date parsing, Decimal balances and non-destructive reload behavior. The original file format lacked a date specification; accepted date forms are documented in DESIGN.md.

## Exam reports

Completed the empty `salva_medie` function and connected the complete workflow. Grade parsing now follows the supplied integer-grade requirement, requires a nonempty student ID and rejects malformed input rows. Passing histories are rebuilt without accumulation. Added explicit duplicate handling, decimal average rounding, a configurable passing-record threshold and report path protection.

## Sales analysis

Retained per-product revenue and the bounded-selection approach while making top-k output consistently ordered. Added deterministic ties, validation of stock and quantities, quoted CSV support, exact decimal arithmetic and configurable report paths. Invalid inputs do not replace a previous report.

## Repository preparation

Separated reusable functions from command-line entry points, added synthetic examples and standard-library regression/integration tests, and documented formats, limits and development provenance. This is a completed extension of the selected exercises; it does not reconstruct an exact earlier unsaved version.
