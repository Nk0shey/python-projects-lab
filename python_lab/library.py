"""Single-copy library: members, loans, returns and a local JSON archive."""
import argparse
from copy import deepcopy
import json
import sys
from .common import atomic_text, text

MAX_LOANS = 3


def cerca_libro(biblioteca, titolo):
    return next((book for book in biblioteca if book["titolo"].casefold() == titolo.strip().casefold()), None)


def cerca_utente(utenti, nome):
    return next((user for user in utenti if user["nome"].casefold() == nome.strip().casefold()), None)


def aggiungi_libro(biblioteca, titolo, autore, anno):
    titolo, autore = text(titolo, "Title"), text(autore, "Author")
    if isinstance(anno, bool):
        raise ValueError("Year must be an integer")
    if not isinstance(anno, (str, int)):
        raise ValueError("Year must be an integer")
    year = int(anno)
    if cerca_libro(biblioteca, titolo):
        return False
    biblioteca.append({"titolo": titolo, "autore": autore, "anno": year, "disponibile": True})
    return True


def aggiungi_utente(utenti, nome, email):
    nome, email = text(nome, "Name"), text(email, "Email")
    if email.count("@") != 1 or not all(email.split("@")) or any(c.isspace() for c in email):
        raise ValueError("Enter an email address with a local part and domain")
    if cerca_utente(utenti, nome) or any(u["email"].casefold() == email.casefold() for u in utenti):
        return False
    utenti.append({"nome": nome, "email": email, "prestiti": []})
    return True


def mostra_libri(biblioteca):
    return "\n".join(f"{b['titolo']} — {b['autore']} ({b['anno']}) "
                     f"[{'Disponibile' if b['disponibile'] else 'In prestito'}]" for b in biblioteca) or "Nessun libro."


def mostra_utenti(utenti):
    return "\n".join(f"{u['nome']} <{u['email']}> — prestiti: {len(u['prestiti'])}" for u in utenti) or "Nessun utente."


def libri_disponibili(biblioteca):
    return [book for book in biblioteca if book["disponibile"]]


def prestiti_utente(utenti, nome):
    user = cerca_utente(utenti, nome)
    return None if user is None else list(user["prestiti"])


def effettua_prestito(biblioteca, utenti, titolo, nome_utente):
    book, user = cerca_libro(biblioteca, titolo), cerca_utente(utenti, nome_utente)
    if book is None or user is None or not book["disponibile"] or len(user["prestiti"]) >= MAX_LOANS:
        return False
    user["prestiti"].append(book["titolo"])
    book["disponibile"] = False
    return True


def restituisci_libro(biblioteca, utenti, titolo, nome_utente):
    book, user = cerca_libro(biblioteca, titolo), cerca_utente(utenti, nome_utente)
    if book is None or user is None or book["titolo"] not in user["prestiti"]:
        return False
    user["prestiti"].remove(book["titolo"])
    book["disponibile"] = True
    return True


def elimina_libro(biblioteca, titolo):
    book = cerca_libro(biblioteca, titolo)
    if book is None or not book["disponibile"]:
        return False
    biblioteca.remove(book)
    return True


def elimina_utente(utenti, nome):
    user = cerca_utente(utenti, nome)
    if user is None or user["prestiti"]:
        return False
    utenti.remove(user)
    return True


def riepilogo(biblioteca, utenti):
    return (f"Libri totali: {len(biblioteca)}\nUtenti totali: {len(utenti)}\n"
            f"Libri attualmente in prestito: {sum(not book['disponibile'] for book in biblioteca)}")


def valida_archivio(data):
    """Validate shape and cross-record loan invariants before using saved data."""
    if not isinstance(data, dict) or set(data) != {"version", "books", "members"} or type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Unsupported library archive")
    if not isinstance(data["books"], list) or not isinstance(data["members"], list):
        raise ValueError("Books and members must be lists")
    books, members, borrowed = [], [], set()
    for record in data["books"]:
        if not isinstance(record, dict) or set(record) != {"titolo", "autore", "anno", "disponibile"}:
            raise ValueError("Invalid book record")
        if type(record["anno"]) is not int or type(record["disponibile"]) is not bool:
            raise ValueError("Invalid year or availability")
        if not aggiungi_libro(books, record["titolo"], record["autore"], record["anno"]):
            raise ValueError("Duplicate book title")
        books[-1]["disponibile"] = record["disponibile"]
    for record in data["members"]:
        if not isinstance(record, dict) or set(record) != {"nome", "email", "prestiti"}:
            raise ValueError("Invalid member record")
        if not aggiungi_utente(members, record["nome"], record["email"]):
            raise ValueError("Duplicate member name or email")
        loans = record["prestiti"]
        if not isinstance(loans, list) or len(loans) > MAX_LOANS:
            raise ValueError("Invalid loan list")
        for title in loans:
            title = text(title, "Loan title")
            book = cerca_libro(books, title)
            if book is None or book["disponibile"] or book["titolo"] in borrowed:
                raise ValueError("Inconsistent or duplicate loan")
            borrowed.add(book["titolo"])
            members[-1]["prestiti"].append(book["titolo"])
    if any((book["titolo"] in borrowed) == book["disponibile"] for book in books):
        raise ValueError("Book availability does not match loans")
    return books, members


def carica_archivio(path):
    try:
        with open(path, encoding="utf-8") as source:
            return valida_archivio(json.load(source))
    except FileNotFoundError:
        return [], []


def salva_archivio(biblioteca, utenti, path):
    books, members = valida_archivio({"version": 1, "books": biblioteca, "members": utenti})
    with atomic_text(path) as output:
        json.dump({"version": 1, "books": books, "members": members}, output, ensure_ascii=False, indent=2)
        output.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="library.json", help="JSON archive, created on first successful change")
    args = parser.parse_args(argv)
    try:
        books, users = carica_archivio(args.data)
    except (ValueError, OSError) as exc:
        print(f"Archive error: {exc}", file=sys.stderr)
        return 1
    while True:
        print("\n1 Aggiungi libro | 2 Libri | 3 Aggiungi utente | 4 Utenti | 5 Prestito | 6 Reso")
        print("7 Disponibili | 8 Prestiti utente | 9 Elimina | 10 Riepilogo | 11 Esci")
        before = deepcopy((books, users))
        try:
            choice = input("Scelta: ").strip()
            changed = False
            if choice in ("0", "11"):
                return 0
            if choice == "1":
                title, author, year = input("Titolo: "), input("Autore: "), input("Anno: ")
                changed = aggiungi_libro(books, title, author, year)
            elif choice == "2":
                print(mostra_libri(books))
            elif choice == "3":
                name, email = input("Nome: "), input("Email: ")
                changed = aggiungi_utente(users, name, email)
            elif choice == "4":
                print(mostra_utenti(users))
            elif choice in ("5", "6"):
                title, name = input("Titolo: "), input("Nome utente: ")
                operation = effettua_prestito if choice == "5" else restituisci_libro
                changed = operation(books, users, title, name)
            elif choice == "7":
                print(mostra_libri(libri_disponibili(books)))
            elif choice == "8":
                print(prestiti_utente(users, input("Nome: ")))
            elif choice == "9":
                kind, name = input("libro/utente: ").strip().casefold(), input("Titolo/nome: ")
                if kind == "libro":
                    changed = elimina_libro(books, name)
                elif kind == "utente":
                    changed = elimina_utente(users, name)
                else:
                    print("Tipo non valido.")
            elif choice == "10":
                print(riepilogo(books, users))
            else:
                print("Scelta non valida.")
            if changed:
                salva_archivio(books, users, args.data)
                print("Operazione completata e salvata.")
            elif choice in ("1", "3", "5", "6", "9"):
                print("Operazione non eseguita: controllare duplicati, disponibilita e prestiti.")
        except EOFError:
            return 0
        except (ValueError, OSError) as exc:
            books, users = before
            print(f"Errore: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
