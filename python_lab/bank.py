"""Account-record sorting exercise; a local educational ledger, using CSV."""
import argparse
import csv
from datetime import datetime
import sys
from .common import atomic_text, money, text

NOME_INPUT_FILE = "banca.csv"
NOME_OUTPUT_FILE = "backup.csv"


def parse_date(value):
    value = text(value, "Opening date")
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    raise ValueError("Use a valid date: YYYY-MM-DD or DD/MM/YYYY")


def crea_correntista(nome, cognome, data_apertura, saldo):
    return {"nome": text(nome, "First name"), "cognome": text(cognome, "Last name"),
            "data apertura": parse_date(data_apertura).isoformat(),
            "saldo": money(saldo, allow_negative=True)}


def leggi_da_file(nome_file=NOME_INPUT_FILE):
    records = []
    with open(nome_file, encoding="utf-8", newline="") as source:
        for row_number, row in enumerate(csv.reader(source, strict=True), 1):
            if not row or all(not part.strip() for part in row):
                continue
            try:
                if len(row) != 4:
                    raise ValueError("Expected four CSV fields")
                records.append(crea_correntista(*row))
            except ValueError as exc:
                raise ValueError(f"Record {row_number}: {exc}") from exc
    return records


def stampa_correntisti(correntisti):
    if not correntisti:
        print("Nessun correntista.")
    for record in correntisti:
        print(f"{record['cognome']}, {record['nome']} | {record['data apertura']} | "
              f"EUR {record['saldo']:.2f}")


def aggiungi_correntista(correntisti):
    # Construct the complete record before changing the list.
    nome = input("Nome: ")
    cognome = input("Cognome: ")
    apertura = input("Data apertura (YYYY-MM-DD): ")
    saldo = input("Saldo: ")
    correntisti.append(crea_correntista(nome, cognome, apertura, saldo))


def ordina_per_data_apertura(v):
    """Stable in-place shaker sort, as required by the original assignment."""
    left, right = 0, len(v) - 1
    while left < right:
        changed = False
        for i in range(left, right):
            if v[i]["data apertura"] > v[i + 1]["data apertura"]:
                v[i], v[i + 1] = v[i + 1], v[i]
                changed = True
        right -= 1
        if not changed:
            break
        changed = False
        for i in range(right, left, -1):
            if v[i - 1]["data apertura"] > v[i]["data apertura"]:
                v[i - 1], v[i] = v[i], v[i - 1]
                changed = True
        left += 1
        if not changed:
            break
    return v


def ordina_per_saldo_decrescente(v):
    """Stable in-place insertion sort by descending balance."""
    for i in range(1, len(v)):
        item = v[i]
        j = i - 1
        while j >= 0 and v[j]["saldo"] < item["saldo"]:
            v[j + 1] = v[j]
            j -= 1
        v[j + 1] = item
    return v


def ordina_per_cognome_nome(v):
    """Stable in-place bubble sort by case-insensitive surname and first name."""
    def key(record):
        return record["cognome"].casefold(), record["nome"].casefold()
    for end in range(len(v) - 1, 0, -1):
        changed = False
        for i in range(end):
            if key(v[i]) > key(v[i + 1]):
                v[i], v[i + 1] = v[i + 1], v[i]
                changed = True
        if not changed:
            break
    return v


def salva_backup(v, nome_file=NOME_OUTPUT_FILE):
    # Validate before opening the destination, including callers outside the CLI.
    records = [crea_correntista(c["nome"], c["cognome"], c["data apertura"], c["saldo"]) for c in v]
    with atomic_text(nome_file) as output:
        writer = csv.writer(output)
        for c in records:
            writer.writerow((c["nome"], c["cognome"], c["data apertura"], f"{c['saldo']:.2f}"))
    return len(records)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=NOME_INPUT_FILE)
    parser.add_argument("--output", default=NOME_OUTPUT_FILE)
    args = parser.parse_args(argv)
    correntisti = []
    while True:
        print("\n1 Carica | 2 Mostra | 3 Aggiungi | 4 Data ↑ | 5 Saldo ↓ | 6 Nome ↑ | 7 Salva | 0 Esci")
        try:
            choice = input("Scelta: ").strip()
            if choice == "0":
                return 0
            if choice == "1":
                correntisti = leggi_da_file(args.input)
                print(f"Caricati {len(correntisti)} correntisti.")
            elif choice == "2":
                stampa_correntisti(correntisti)
            elif choice == "3":
                aggiungi_correntista(correntisti)
            elif choice == "4":
                ordina_per_data_apertura(correntisti)
            elif choice == "5":
                ordina_per_saldo_decrescente(correntisti)
            elif choice == "6":
                ordina_per_cognome_nome(correntisti)
            elif choice == "7":
                print(f"Salvati {salva_backup(correntisti, args.output)} correntisti.")
            else:
                print("Scelta non valida.")
        except EOFError:
            return 0
        except (ValueError, OSError, csv.Error) as exc:
            print(f"Errore: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
