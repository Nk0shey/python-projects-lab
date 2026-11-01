from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from python_lab import bank as app


def record(first="Anna", last="Rossi", opening="2020-01-01", balance="1.00"):
    return app.crea_correntista(first, last, opening, balance)


class BankTests(unittest.TestCase):
    def test_dates_normalized(self):
        self.assertEqual(record(opening="31/12/2020")["data apertura"], "2020-12-31")

    def test_invalid_dates(self):
        for opening in ("2023-02-29", "bad", "31/04/2020"):
            with self.subTest(opening=opening), self.assertRaises(ValueError):
                record(opening=opening)

    def test_money_is_exact_and_negative_balance_supported(self):
        self.assertEqual(record(balance="-1.20")["saldo"], Decimal("-1.20"))

    def test_invalid_account(self):
        for overrides in ({"first": " "}, {"last": ""}, {"balance": "nan"}, {"balance": "1.234"}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                record(**overrides)

    def test_three_sorts_against_oracle(self):
        randomizer = random.Random(42)
        for size in range(30):
            records = [record(str(i), randomizer.choice(["Rossi", "Bianchi", "verdi"]),
                              f"2020-01-{randomizer.randrange(1, 29):02d}", str(randomizer.randrange(-10, 10))) for i in range(size)]
            for sorter, key in ((app.ordina_per_data_apertura, lambda c: c["data apertura"]),
                                (app.ordina_per_saldo_decrescente, lambda c: -c["saldo"]),
                                (app.ordina_per_cognome_nome, lambda c: (c["cognome"].casefold(), c["nome"].casefold()))):
                with self.subTest(size=size, sorter=sorter.__name__):
                    actual = deepcopy(records)
                    self.assertIs(sorter(actual), actual)
                    self.assertEqual(actual, sorted(records, key=key))

    def test_csv_round_trip_with_quoted_name(self):
        accounts = [record(first='Anna, Maria', last='D’Amico', balance="0.10"), record(balance="-2.00")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "accounts.csv"
            self.assertEqual(app.salva_backup(accounts, path), 2)
            self.assertEqual(app.leggi_da_file(path), accounts)

    def test_empty_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.csv"; path.touch()
            self.assertEqual(app.leggi_da_file(path), [])

    def test_bad_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            for row in ("Anna,Rossi,2020-01-01\n", "Anna,Rossi,2020-01-01,Infinity\n", "Anna,Rossi,2020-02-30,4\n"):
                with self.subTest(row=row):
                    path.write_text(row)
                    with self.assertRaisesRegex(ValueError, "Record 1"):
                        app.leggi_da_file(path)

    def test_incomplete_add_does_not_mutate(self):
        accounts = []
        with patch("builtins.input", side_effect=["Anna", "Rossi", "2020-01-01", EOFError]):
            with self.assertRaises(EOFError):
                app.aggiungi_correntista(accounts)
        self.assertEqual(accounts, [])

    def test_invalid_add_does_not_mutate(self):
        accounts = []
        with patch("builtins.input", side_effect=["Anna", "Rossi", "2020-01-01", "nan"]):
            with self.assertRaises(ValueError):
                app.aggiungi_correntista(accounts)
        self.assertEqual(accounts, [])
