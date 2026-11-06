"""Derive fixed test fixtures from the assignment specification, not production code.

Run once when intentionally revising the design; JUnit reads the committed CSVs.
"""
import csv
from decimal import Decimal
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/test/resources/assignment1"


def save(name, columns, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / (name + ".csv")).open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def money(amount, rate):
    return str(Decimal(str(amount)) * Decimal(str(rate)))


def withdrawal():
    # Monetary resolution is one cent. No upper bound is specified for this API:
    # 1,000 and 10,000 are finite sampling-envelope edges, not rejection limits.
    amounts = [-0.01, 0, 0.01, 500, 999.99, 1000, 1000.01]
    balances = [-0.01, 0, 0.01, 999.99, 1000, 1000.01,
                4999.99, 5000, 5000.01, 9999.99, 10000, 10000.01]
    rows = []
    for number, (amount, balance, student, day) in enumerate(
            product(amounts, balances, [True, False], range(9)), 1):
        if amount < 0 or balance < 0 or day not in range(1, 8):
            expected = "REJECT"
        else:
            rate = (0 if day in range(2, 7) else 0.001) if student else (
                0.003 if balance < 1000 else 0.001 if balance < 5000 else 0)
            expected = money(amount, rate)
        rows.append([f"W{number:04}", amount, balance, str(student).lower(), day, expected])
    save("withdrawal", ["id", "amount", "balance", "student", "day", "expected"], rows)


def deposit():
    rows = []
    # Cover each conditional valid amount/balance equivalence class once.
    # Additional equal-threshold representatives make inclusivity explicit.
    for student, amounts, balances in [
            (True, [25, 75], [250, 1000, 6000]),
            (False, [125, 375], [1000, 5000, 15000])]:
        for amount, balance in product(amounts, balances):
            rows.append([amount, balance, student])
    rows += [[50, 500, True], [50, 5000, True], [75, 500, True],
             [250, 2500, False], [250, 10000, False], [375, 2500, False],
             [0, 0, True], [0, 0, False]]
    # Weak robust: each invalid class alone, all other inputs nominal and valid.
    rows += [[-0.01, 1000, True], [75, -0.01, True],
             [-0.01, 5000, False], [375, -0.01, False]]
    results = []
    for number, (amount, balance, student) in enumerate(rows, 1):
        if amount < 0 or balance < 0:
            expected = "REJECT"
        else:
            if student:
                rate = (0.005 if balance > 500 else 0.0025) if amount > 50 else (
                    0.005 if balance > 5000 else 0)
            else:
                rate = (0.008 if balance > 2500 else 0.004) if amount > 250 else (
                    0 if balance > 10000 else 0.001)
            expected = money(amount, rate)
        results.append([f"D{number:02}", amount, balance, str(student).lower(), expected])
    save("deposit", ["id", "amount", "balance", "student", "expected"], results)


def transfer():
    rows = []
    # 2 student classes x 2 amount classes x 2 source classes x 2 destination classes.
    # Low representatives are threshold - 1; high representatives equal threshold.
    # Rates below are fractions, transcribed directly from all 16 specification leaves.
    branches = [
        (True, 199, 2000, 1000, [0.001, 0.0005, 0.0005, 0.00025]),
        (True, 200, 2000, 1000, [0.0005, 0.00025, 0.0025, 0.00125]),
        (False, 99, 4000, 2000, [0.002, 0.001, 0.01, 0.005]),
        (False, 100, 2000, 1000, [0.002, 0.001, 0.005, 0.0025]),
    ]
    for student, amount, source, destination, rates in branches:
        for (from_high, to_high), rate in zip(product([False, True], repeat=2), rates):
            from_balance = source if from_high else source - 1
            to_balance = destination if to_high else destination - 1
            rows.append([f"T{len(rows) + 1:02}", amount, from_balance, to_balance,
                         str(student).lower(), rate, money(amount, rate)])
    save("transfer", ["id", "amount", "from", "to", "student", "rate", "expected"], rows)


def session():
    # PIN numeric BVA includes leading zeros. Length/character cases supplement it.
    pins = ["00000", "00001", "50000", "99998", "99999"]
    pin_cases = [[f"P{i:02}", pin, True] for i, pin in enumerate(pins, 1)]
    invalid = ["-0001", "100000", "1234", "123456", "1", "", "12a45", "12/45", "12:45", "12 45"]
    pin_cases += [[f"P{len(pin_cases) + i:02}", pin, False]
                  for i, pin in enumerate(invalid, 1)]
    # Also vary a character in every position at each character boundary.
    for position, digit in product(range(5), ["/", "0", "1", "8", "9", ":"]):
        pin = list("55555")
        pin[position] = digit
        pin_cases.append([f"P{len(pin_cases) + 1:02}", "".join(pin), digit.isdigit()])
    save("pin", ["id", "pin", "valid"],
         [[case_id, pin, str(valid).lower()] for case_id, pin, valid in pin_cases])
    cases = list(product(pins, [19, 20, 21, 500, 999, 1000, 1001]))
    cases += [("50000", amount) for amount in [-50, -1, 0, 30, 40, 50, 60, 70, 80, 90, 110, 990, 1010, 1020]]
    rows = []
    for number, (pin, amount) in enumerate(cases, 1):
        # Independent bill-combination oracle: nonnegative counts of $50 and $20.
        dispensable = amount > 0 and any(
            (amount - 50 * fifties) % 20 == 0 for fifties in range(max(0, amount // 50) + 1))
        rows.append([f"S{number:02}", pin, amount, str(dispensable and amount <= 1000).lower()])
    save("session", ["id", "pin", "amount", "valid"], rows)


if __name__ == "__main__":
    withdrawal()
    deposit()
    transfer()
    session()
