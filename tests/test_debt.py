from app.debt import simplify_debts


def _net_from_settlements(settlements):
    """Recompute net positions implied by a settlement list, for cross-checking
    against the original net_positions passed into simplify_debts."""
    net = {}
    for debtor, creditor, amount in settlements:
        net[debtor] = net.get(debtor, 0) - amount
        net[creditor] = net.get(creditor, 0) + amount
    return net


def _assert_conserves(net_positions, settlements):
    # Every settlement is a positive amount between two distinct people.
    for debtor, creditor, amount in settlements:
        assert amount > 0
        assert debtor != creditor

    recomputed = _net_from_settlements(settlements)
    for name, amount in net_positions.items():
        if amount == 0:
            assert name not in recomputed
        else:
            assert recomputed.get(name, 0) == amount
    # No stray names invented by the settlement list.
    assert set(recomputed).issubset({n for n, a in net_positions.items() if a != 0})


def test_simple_two_person():
    net = {"A": 100, "B": -100}
    settlements = simplify_debts(net)
    assert settlements == [("B", "A", 100)]
    _assert_conserves(net, settlements)


def test_three_plus_person_overlapping_with_partial_settlements():
    # Net positions as they'd fall out after aggregating several overlapping
    # orders where some order_items were already partially settled via /paid
    # or the settle button - so the remaining amounts don't divide evenly.
    net = {
        "tam": 45000,
        "raihan": 20000,
        "budi": -35000,
        "citra": -30000,
    }
    settlements = simplify_debts(net)

    _assert_conserves(net, settlements)
    # Minimal-ish: at most len(participants) - 1 lines.
    assert len(settlements) <= len(net) - 1
    # tam (largest creditor) should be settled first against budi (largest debtor).
    assert settlements[0] == ("budi", "tam", 35000)


def test_zero_net_position_produces_no_line():
    net = {"A": 50, "B": -50, "C": 0}
    settlements = simplify_debts(net)

    _assert_conserves(net, settlements)
    assert len(settlements) == 1
    for debtor, creditor, _ in settlements:
        assert "C" not in (debtor, creditor)


def test_minimal_lines_for_two_creditors_one_debtor():
    net = {"A": 30, "B": 20, "C": -50}
    settlements = simplify_debts(net)

    _assert_conserves(net, settlements)
    assert len(settlements) == 2
    debtors = {debtor for debtor, _, _ in settlements}
    assert debtors == {"C"}


def test_empty_positions_produce_no_settlements():
    assert simplify_debts({}) == []


def test_all_zero_positions_produce_no_settlements():
    assert simplify_debts({"A": 0, "B": 0}) == []
