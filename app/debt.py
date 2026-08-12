"""Debt simplification: turn a set of net positions into a minimal-ish
set of pairwise settlements.

Pure function, no I/O - this is the one piece of real logic in the
service, so it gets real unit tests (see tests/test_debt.py).
"""


def simplify_debts(net_positions: dict[str, int]) -> list[tuple[str, str, int]]:
    """Given `{name: net_amount}` (positive = owed to them, negative = they owe,
    zero = settled up), return a list of `(debtor, creditor, amount)` settlements
    that resolves every position to zero.

    Greedy strategy: repeatedly match the current largest creditor against the
    current largest debtor, settle the smaller of the two magnitudes, and
    recompute. This keeps the number of settlement lines small (at most
    len(positions) - 1) without needing to solve the NP-hard minimum-transactions
    problem exactly.
    """
    positions = {name: amount for name, amount in net_positions.items() if amount != 0}

    settlements: list[tuple[str, str, int]] = []

    while positions:
        creditor_name, credit_amt = max(positions.items(), key=lambda kv: kv[1])
        debtor_name, debt_amt = min(positions.items(), key=lambda kv: kv[1])

        if credit_amt <= 0 or debt_amt >= 0:
            # Everything left is (numerically) zero - nothing more to settle.
            break

        amount = min(credit_amt, -debt_amt)
        settlements.append((debtor_name, creditor_name, amount))

        positions[creditor_name] -= amount
        positions[debtor_name] += amount

        if positions[creditor_name] == 0:
            del positions[creditor_name]
        if positions[debtor_name] == 0:
            del positions[debtor_name]

    return settlements
