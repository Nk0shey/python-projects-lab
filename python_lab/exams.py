"""Join student and exam files, then export averages for eligible students."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import sys
from .common import atomic_text, distinct_output


def leggi(file_studenti, file_esami):
    """Ignore malformed rows as required by the original exercise."""
    students, exams = [], []
    identifiers = set()
    with open(file_studenti, encoding="utf-8", newline="") as source:
        for line in source:
            parts = [value.strip() for value in line.rstrip("\r\n").split(";")]
            if len(parts) != 3 or not all(parts) or any(ord(c) < 32 for part in parts for c in part):
                continue
            first, last, identifier = parts
            if identifier in identifiers:
                continue
            identifiers.add(identifier)
            students.append({"nome": first, "cognome": last, "matricola": identifier})
    # Exact duplicate passing records are counted once; distinct attempts remain distinct.
    seen = set()
    with open(file_esami, encoding="utf-8", newline="") as source:
        for line in source:
            parts = [value.strip() for value in line.rstrip("\r\n").split(";")]
            if len(parts) != 3 or not all(parts) or any(ord(c) < 32 for part in parts for c in part):
                continue
            identifier, name, raw_grade = parts
            try:
                grade = int(raw_grade)
            except ValueError:
                continue
            if grade != 0 and not 18 <= grade <= 30:
                continue
            record = (identifier, name, grade)
            if record not in seen:
                exams.append(record)
                seen.add(record)
    return students, exams


def aggiungi_storico_esami(lista_studenti, lista_esami):
    histories = {}
    for identifier, name, grade in lista_esami:
        if grade >= 18:
            histories.setdefault(identifier, []).append((name, grade))
    for student in lista_studenti:
        student["storico_esami"] = list(histories.get(student["matricola"], []))


def medie_studenti(lista_studenti, minimo_esami=3):
    if type(minimo_esami) is not int or minimo_esami < 1:
        raise ValueError("Minimum exam count must be positive")
    result = []
    for student in lista_studenti:
        history = student.get("storico_esami", [])
        if len(history) >= minimo_esami:
            average = Decimal(sum(grade for _, grade in history)) / len(history)
            result.append((student["matricola"], average.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)))
    return result


def salva_medie(lista_studenti, nome_file_output, minimo_esami=3):
    averages = medie_studenti(lista_studenti, minimo_esami)
    with atomic_text(nome_file_output) as output:
        for identifier, average in averages:
            output.write(f"{identifier}: {average:.2f}\n")
    return len(averages)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("students", help="name;surname;student_id")
    parser.add_argument("exams", help="student_id;exam;integer_grade")
    parser.add_argument("--output", default="averages.txt")
    parser.add_argument("--minimum", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        distinct_output(args.output, args.students, args.exams)
        students, exams = leggi(args.students, args.exams)
        aggiungi_storico_esami(students, exams)
        count = salva_medie(students, args.output, args.minimum)
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Students: {len(students)} | Valid unique exam records: {len(exams)}")
    print(f"Exported averages: {count} | Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
