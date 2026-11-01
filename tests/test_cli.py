from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from python_lab import bank, library

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}

    def run_app(self, module, *args, input="", expected=0):
        result = subprocess.run([sys.executable, "-m", "python_lab." + module, *map(str, args)],
                                input=input, text=True, encoding="utf-8", capture_output=True,
                                timeout=5, cwd=self.work, env=self.env)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_sales_example_exact_report(self):
        result = self.run_app("sales", ROOT / "examples/products.csv", "--output", "top.csv")
        self.assertIn("EUR 275.00", result.stdout)
        self.assertEqual((self.work / "top.csv").read_text(), "Tea,60.00\nWater,40.00\nCoffee,100.00\n")

    def test_exam_example_exact_report(self):
        result = self.run_app("exams", ROOT / "examples/students.csv", ROOT / "examples/exams.csv", "--output", "averages.txt")
        self.assertIn("Exported averages: 2", result.stdout)
        self.assertEqual((self.work / "averages.txt").read_text(), "S001: 29.00\nS003: 18.67\n")

    def test_batch_missing_files_fail_without_traceback(self):
        self.run_app("sales", "absent", expected=1)
        self.run_app("exams", "absent", "absent", expected=1)

    def test_output_cannot_overwrite_input(self):
        path = self.work / "source.csv"
        path.write_text("Tea,1,2,3\n")
        self.run_app("sales", path, "--output", path, expected=1)
        self.assertEqual(path.read_text(), "Tea,1,2,3\n")
        self.run_app("exams", path, path, "--output", path, expected=1)
        self.assertEqual(path.read_text(), "Tea,1,2,3\n")

    def test_failed_batch_preserves_previous_report(self):
        source, output = self.work / "bad", self.work / "report"
        source.write_text("Bad,nan,1,1\n")
        output.write_text("previous")
        self.run_app("sales", source, "--output", output, expected=1)
        self.assertEqual(output.read_text(), "previous")

    def test_invalid_thresholds_fail(self):
        self.run_app("sales", ROOT / "examples/products.csv", "--top", "0", expected=1)
        self.run_app("exams", ROOT / "examples/students.csv", ROOT / "examples/exams.csv", "--minimum", "0", expected=1)

    def test_bank_all_menu_operations(self):
        output = self.work / "backup.csv"
        self.run_app("bank", "--input", ROOT / "examples/accounts.csv", "--output", output,
                     input="1\n2\n3\nDemo\nZebra\n2024-01-01\n12.30\n4\n5\n6\n7\n0\n")
        accounts = bank.leggi_da_file(output)
        self.assertEqual(len(accounts), 4)
        self.assertEqual([c["cognome"] for c in accounts], ["Bianchi", "Rossi", "Verdi", "Zebra"])

    def test_bank_invalid_add_and_recovery(self):
        output = self.work / "backup.csv"
        result = self.run_app("bank", "--input", ROOT / "examples/accounts.csv", "--output", output,
                             input="1\n3\nBad\nRecord\nnot-a-date\n4\n7\n0\n")
        self.assertIn("Errore:", result.stderr)
        self.assertEqual(len(bank.leggi_da_file(output)), 3)

    def test_library_round_trip_across_processes(self):
        archive = self.work / "library.json"
        shutil.copy(ROOT / "examples/library.json", archive)
        self.run_app("library", "--data", archive,
                     input="1\nNew Book\nAuthor\n2020\n2\n3\nAnna\nanna@example.test\n4\n5\nNew Book\nAnna\n7\n8\nAnna\n10\n11\n")
        books, users = library.carica_archivio(archive)
        self.assertEqual(library.prestiti_utente(users, "Anna"), ["New Book"])
        self.assertFalse(library.cerca_libro(books, "New Book")["disponibile"])
        self.run_app("library", "--data", archive,
                     input="6\nnew book\nanna\n9\nlibro\nNew Book\n9\nutente\nAnna\n11\n")
        books, users = library.carica_archivio(archive)
        self.assertIsNone(library.cerca_libro(books, "New Book"))
        self.assertIsNone(library.cerca_utente(users, "Anna"))

    def test_library_corrupt_archive_does_not_get_replaced(self):
        archive = self.work / "bad.json"; archive.write_text("broken")
        self.run_app("library", "--data", archive, input="1\n", expected=1)
        self.assertEqual(archive.read_text(), "broken")

    def test_menus_handle_eof_and_invalid_choice(self):
        for module in ("bank", "library"):
            self.run_app(module)
            self.run_app(module, input="invalid\n")
            self.run_app(module, input="3\n")

    def test_imports_have_no_console_or_file_side_effects(self):
        result = subprocess.run([sys.executable, "-c", "from python_lab import library, bank, exams, sales"],
                                capture_output=True, text=True, timeout=5, cwd=self.work, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(list(self.work.iterdir()), [])

    def test_library_save_failure_rolls_back_in_memory(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["1", "Book", "Author", "2000", "2", "11"]), \
             patch("python_lab.library.carica_archivio", return_value=([], [])), \
             patch("python_lab.library.salva_archivio", side_effect=OSError("disk full")), \
             redirect_stdout(output), redirect_stderr(io.StringIO()):
            self.assertEqual(library.main([]), 0)
        self.assertIn("Nessun libro.", output.getvalue())

    def test_failed_bank_reload_preserves_records(self):
        records = [bank.crea_correntista("Anna", "Rossi", "2020-01-01", "2")]
        output = io.StringIO()
        with patch("builtins.input", side_effect=["1", "1", "2", "0"]), \
             patch("python_lab.bank.leggi_da_file", side_effect=[records, ValueError("bad file")]), \
             redirect_stdout(output), redirect_stderr(io.StringIO()):
            bank.main([])
        self.assertIn("EUR 2.00", output.getvalue())
