"""Read product sales, calculate revenue, and export the most-sold products."""
import argparse
import csv
from decimal import Decimal
import sys
from .common import atomic_text, distinct_output, money, text


def incasso(nome_file):
    products = []
    seen = set()
    with open(nome_file, encoding="utf-8", newline="") as source:
        for row_number, row in enumerate(csv.reader(source, strict=True), 1):
            if not row or all(not cell.strip() for cell in row):
                continue
            try:
                if len(row) != 4:
                    raise ValueError("Expected name, price, units sold, remaining stock")
                name = text(row[0], "Product name")
                price = money(row[1])
                sold, stock = int(row[2]), int(row[3])
                if sold < 0 or stock < 0:
                    raise ValueError("Quantities cannot be negative")
                if name.casefold() in seen:
                    raise ValueError("Duplicate product name")
                seen.add(name.casefold())
                products.append((name, sold, sold * price))
            except ValueError as exc:
                raise ValueError(f"Record {row_number}: {exc}") from exc
    return products, incassi_totali(products)


def incassi_totali(l_incasso):
    return sum((revenue for _, _, revenue in l_incasso), Decimal("0.00"))


def migliori_prodotti(l_incasso, k=3):
    """Keep a bounded, manually ordered top-k list; never mutate input."""
    if type(k) is not int or k < 1:
        raise ValueError("Top count must be a positive integer")
    best = []
    for item in l_incasso:
        key = (-item[1], item[0].casefold(), item[0])
        index = 0
        while index < len(best):
            other = best[index]
            if key < (-other[1], other[0].casefold(), other[0]):
                break
            index += 1
        if index < k:
            best.insert(index, item)
            if len(best) > k:
                best.pop()
    return best


def top3(l_incasso, nome_file_w):
    best = migliori_prodotti(l_incasso)
    salva_top(best, nome_file_w)
    return best


def salva_top(products, output):
    with atomic_text(output) as destination:
        writer = csv.writer(destination)
        for name, _, revenue in products:
            writer.writerow((name, f"{revenue:.2f}"))
    return len(products)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="CSV without a header")
    parser.add_argument("--output", default="topk.csv")
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        distinct_output(args.output, args.input)
        products, total = incasso(args.input)
        best = migliori_prodotti(products, args.top)
        salva_top(best, args.output)
    except (ValueError, OSError, csv.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Products: {len(products)} | Total revenue: EUR {total:.2f}")
    for name, sold, revenue in best:
        print(f"{name}: {sold} sold | EUR {revenue:.2f}")
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
