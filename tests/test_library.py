from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from python_lab import library as app


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.books, self.users = [], []
        for i in range(4):
            app.aggiungi_libro(self.books, f"Book {i}", "Author", 2000 + i)
        app.aggiungi_utente(self.users, "Anna", "anna@example.test")
        app.aggiungi_utente(self.users, "Bruno", "bruno@example.test")

    def test_duplicate_book(self):
        self.assertFalse(app.aggiungi_libro(self.books, " book 0 ", "Other", 2020))
        self.assertEqual(len(self.books), 4)

    def test_empty_book_is_rejected(self):
        with self.assertRaises(ValueError):
            app.aggiungi_libro(self.books, " ", "Author", 2000)

    def test_year_validation(self):
        for value in ("bad", True, 2.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                app.aggiungi_libro(self.books, "New", "Author", value)

    def test_duplicate_member_or_email(self):
        self.assertFalse(app.aggiungi_utente(self.users, "ANNA", "other@example.test"))
        self.assertFalse(app.aggiungi_utente(self.users, "Other", "ANNA@example.test"))

    def test_invalid_email(self):
        for value in ("", "abc", "a@", "a b@example.test"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                app.aggiungi_utente(self.users, "New", value)

    def test_lookup_finds_later_member(self):
        self.assertEqual(app.cerca_utente(self.users, "BRUNO")["nome"], "Bruno")

    def test_missing_records_do_not_change_state(self):
        before = deepcopy((self.books, self.users))
        self.assertFalse(app.effettua_prestito(self.books, self.users, "Missing", "Anna"))
        self.assertFalse(app.effettua_prestito(self.books, self.users, "Book 0", "Missing"))
        self.assertEqual(before, (self.books, self.users))

    def test_borrow_and_return_case_insensitive(self):
        self.assertTrue(app.effettua_prestito(self.books, self.users, "BOOK 0", "anna"))
        self.assertFalse(self.books[0]["disponibile"])
        self.assertTrue(app.restituisci_libro(self.books, self.users, "book 0", "ANNA"))
        self.assertTrue(self.books[0]["disponibile"])
        self.assertEqual(self.users[0]["prestiti"], [])

    def test_second_borrow_is_rejected(self):
        app.effettua_prestito(self.books, self.users, "Book 0", "Anna")
        self.assertFalse(app.effettua_prestito(self.books, self.users, "Book 0", "Bruno"))

    def test_limit_and_return_when_at_limit(self):
        for i in range(3):
            self.assertTrue(app.effettua_prestito(self.books, self.users, f"Book {i}", "Anna"))
        self.assertFalse(app.effettua_prestito(self.books, self.users, "Book 3", "Anna"))
        self.assertTrue(app.restituisci_libro(self.books, self.users, "Book 1", "Anna"))
        self.assertTrue(app.effettua_prestito(self.books, self.users, "Book 3", "Anna"))

    def test_wrong_member_cannot_return_book(self):
        app.effettua_prestito(self.books, self.users, "Book 0", "Anna")
        self.assertFalse(app.restituisci_libro(self.books, self.users, "Book 0", "Bruno"))
        self.assertFalse(self.books[0]["disponibile"])

    def test_cannot_delete_borrowed_book_or_borrower(self):
        app.effettua_prestito(self.books, self.users, "Book 2", "Anna")
        self.assertFalse(app.elimina_libro(self.books, "Book 2"))
        self.assertFalse(app.elimina_utente(self.users, "Anna"))
        self.assertTrue(app.elimina_libro(self.books, "Book 3"))
        self.assertTrue(app.elimina_utente(self.users, "Bruno"))

    def test_available_books_only(self):
        app.effettua_prestito(self.books, self.users, "Book 0", "Anna")
        self.assertEqual(len(app.libri_disponibili(self.books)), 3)
        self.assertEqual(app.libri_disponibili([]), [])

    def test_returned_history_is_a_copy(self):
        app.effettua_prestito(self.books, self.users, "Book 0", "Anna")
        app.prestiti_utente(self.users, "Anna").clear()
        self.assertEqual(len(self.users[0]["prestiti"]), 1)
        self.assertIsNone(app.prestiti_utente(self.users, "Missing"))

    def test_display_and_summary(self):
        self.assertIn("\n", app.mostra_libri(self.books))
        self.assertIn("\n", app.mostra_utenti(self.users))
        self.assertIn("Libri totali: 4", app.riepilogo(self.books, self.users))

    def test_archive_round_trip(self):
        app.effettua_prestito(self.books, self.users, "Book 0", "Anna")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            app.salva_archivio(self.books, self.users, path)
            self.assertEqual(app.carica_archivio(path), (self.books, self.users))

    def test_missing_archive_starts_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(app.carica_archivio(Path(directory) / "absent.json"), ([], []))

    def test_corrupt_archive_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                app.carica_archivio(path)
            self.assertEqual(path.read_text(), "broken")

    def test_inconsistent_archives(self):
        base = {"version": 1, "books": self.books, "members": self.users}
        cases = []
        bad = deepcopy(base); bad["books"][0]["disponibile"] = False; cases.append(bad)
        bad = deepcopy(base); bad["members"][0]["prestiti"] = ["Missing"]; cases.append(bad)
        bad = deepcopy(base); bad["books"].append(bad["books"][0]); cases.append(bad)
        cases.extend([[], {}, {"version": True, "books": [], "members": []}])
        for bad in cases:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                app.valida_archivio(bad)

    def test_duplicate_loans_are_rejected(self):
        app.effettua_prestito(self.books, self.users, "Book 0", "Anna")
        self.users[1]["prestiti"].append("Book 0")
        with self.assertRaises(ValueError):
            app.valida_archivio({"version": 1, "books": self.books, "members": self.users})
