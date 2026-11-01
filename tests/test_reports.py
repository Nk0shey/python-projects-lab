from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import random
import tempfile
import unittest
from python_lab import exams, sales
from python_lab.common import atomic_text, distinct_output, money


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def write(self, name, content):
        path = self.directory / name
        path.write_text(content, encoding="utf-8")
        return path


class CommonTests(FileTests):
    def test_atomic_output_preserves_previous_file_on_error(self):
        path = self.write("output", "old")
        with self.assertRaises(RuntimeError):
            with atomic_text(path) as destination:
                destination.write("new")
                raise RuntimeError("Interrupted")
        self.assertEqual(path.read_text(), "old")
        self.assertEqual(list(self.directory.glob(".tmp-*")), [])

    def test_output_must_differ(self):
        path = self.write("input", "original")
        with self.assertRaises(ValueError):
            distinct_output(path, path)

    def test_money_validation(self):
        for value in ("nan", "inf", "1.001", "-2", "bad", "1000000000000"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                money(value)
        self.assertEqual(money("0.10") * 3, Decimal("0.30"))


class SalesTests(FileTests):
    def test_revenue_and_stock(self):
        path = self.write("sales.csv", "Coffee,0.10,3,0\nTea,2.50,2,100\n")
        rows, total = sales.incasso(path)
        self.assertEqual(total, Decimal("5.30"))
        self.assertEqual(rows[0], ("Coffee", 3, Decimal("0.30")))

    def test_top_three_order_ties_and_unchanged_input(self):
        rows = [("Z", 2, Decimal("2")), ("A", 5, Decimal("5")),
                ("C", 3, Decimal("3")), ("B", 5, Decimal("5"))]
        before = deepcopy(rows)
        actual = sales.migliori_prodotti(rows)
        self.assertEqual([item[0] for item in actual], ["A", "B", "C"])
        self.assertEqual(rows, before)

    def test_top_k_against_oracle(self):
        generator = random.Random(2026)
        for size in range(30):
            rows = [(f"P{i}", generator.randrange(20), Decimal(i)) for i in range(size)]
            for k in (1, 3, 10):
                with self.subTest(size=size, k=k):
                    self.assertEqual(sales.migliori_prodotti(rows, k),
                                     sorted(rows, key=lambda r: (-r[1], r[0].casefold(), r[0]))[:k])

    def test_empty_and_short_data(self):
        self.assertEqual(sales.migliori_prodotti([]), [])
        path = self.write("empty", "")
        self.assertEqual(sales.incasso(path), ([], Decimal("0.00")))

    def test_invalid_k(self):
        for k in (0, -1, True, 1.5):
            with self.subTest(k=k), self.assertRaises(ValueError):
                sales.migliori_prodotti([], k)

    def test_bad_sales_records(self):
        for row in ("Bad,1,2\n", "Bad,-1,2,3\n", "Bad,1,-2,3\n", "Bad,1,2,-3\n", "Bad,nan,2,3\n", "Bad,1,2.5,3\n", " ,1,2,3\n", "A,1,1,1\na,2,2,2\n"):
            with self.subTest(row=row), self.assertRaises(ValueError):
                sales.incasso(self.write("bad", row))

    def test_top_export_two_columns(self):
        path = self.directory / "top.csv"
        sales.top3([("Tea", 2, Decimal("0.30"))], path)
        self.assertEqual(path.read_text(), "Tea,0.30\n")


class ExamTests(FileTests):
    def load(self, students, exam_rows):
        return exams.leggi(self.write("students", students), self.write("exams", exam_rows))

    def test_skip_malformed_and_noninteger_grades(self):
        students, rows = self.load(" Anna ; Rossi ; S1 \nmalformed\n;Empty;S2\n", "S1;Math;30\nS1;Failed;0\nS1;Low;17\nS1;Fractional;18.5\nS1;NotInteger;18.0\n;X;20\nS1;Huge;31\nS1;Nan;nan\n")
        self.assertEqual(len(students), 1)
        self.assertEqual(rows, [("S1", "Math", 30), ("S1", "Failed", 0)])

    def test_duplicates_are_not_counted_twice(self):
        students, rows = self.load("Anna;Rossi;S1\nAnna;Rossi;S1\n", "S1;Math;30\nS1;Math;30\n")
        self.assertEqual(len(students), 1)
        self.assertEqual(len(rows), 1)

    def test_histories_are_replaced_and_failed_unknown_exams_excluded(self):
        students, rows = self.load("Anna;Rossi;S1\nBruno;Verdi;S2\n", "S1;Math;30\nS1;Failed;0\nUNKNOWN;Math;30\n")
        exams.aggiungi_storico_esami(students, rows)
        exams.aggiungi_storico_esami(students, rows)
        self.assertEqual(students[0]["storico_esami"], [("Math", 30)])
        self.assertEqual(students[1]["storico_esami"], [])

    def test_threshold_and_mean_export(self):
        students, rows = self.load("Anna;Rossi;S1\nBruno;Verdi;S2\n", "S1;A;30\nS1;B;29\nS1;C;28\nS2;A;18\nS2;B;20\n")
        exams.aggiungi_storico_esami(students, rows)
        output = self.directory / "report"
        self.assertEqual(exams.salva_medie(students, output), 1)
        self.assertEqual(output.read_text(), "S1: 29.00\n")
        self.assertEqual(len(exams.medie_studenti(students, 2)), 2)

    def test_rounding_and_empty_report(self):
        students = [{"matricola": "X", "storico_esami": [("A", 18), ("B", 19), ("C", 19)]}]
        self.assertEqual(exams.medie_studenti(students), [("X", Decimal("18.67"))])
        output = self.directory / "report"
        self.assertEqual(exams.salva_medie([], output), 0)
        self.assertEqual(output.read_text(), "")

    def test_invalid_minimum(self):
        for count in (0, -1, True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                exams.medie_studenti([], count)
