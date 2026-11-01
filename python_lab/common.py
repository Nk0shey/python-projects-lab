"""Small shared helpers for validated values and atomic UTF-8 output."""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import tempfile


def money(value, *, allow_negative=False):
    """Read a finite amount with at most two decimal places, without rounding."""
    try:
        result = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ValueError("Invalid monetary amount") from exc
    if not result.is_finite() or abs(result) > Decimal("999999999999.99"):
        raise ValueError("Monetary amount must be finite and within the supported range")
    if not allow_negative and result < 0:
        raise ValueError("Amount cannot be negative")
    if result != result.quantize(Decimal("0.01")):
        raise ValueError("Use at most two decimal places")
    return result.quantize(Decimal("0.01"))


def text(value, label="Value"):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be empty")
    value = value.strip()
    if any(ord(c) < 32 for c in value):
        raise ValueError(f"{label} cannot contain control characters")
    return value


@contextmanager
def atomic_text(path):
    """Replace output only after successful writing; leave old output on failure."""
    path = Path(path)
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=path.parent, prefix=".tmp-", delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            yield handle
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def distinct_output(output, *inputs):
    target = Path(output).resolve()
    if any(target == Path(source).resolve() for source in inputs):
        raise ValueError("Output must differ from input files")
