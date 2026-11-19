"""Independent sweep of ledger account usage across generated books (T2).

Verifies ledger account policy adherence directly on generator output:
(a) every ledger account is a key in ep['policy']['ledger']['accounts']
(b) rows with invoice_id set and payment_id None use only 1200/4000 and carry the invoice's entity_id
(c) rows with payment_id set use only 1000/1200/2900/7900
(d) rows with no invoice_id and no payment_id are debits to 6100/6200/6300/6400 or credits to 1000, with entity_id None
"""

from __future__ import annotations

import copy
import unittest

from auditenv.fuzz import HEAVY
from auditenv.generator import generate

EXPENSE_DEBIT_ACCOUNTS = frozenset({"6100", "6200", "6300", "6400"})
INVOICE_ACCOUNTS = frozenset({"1200", "4000"})
PAYMENT_ACCOUNTS = frozenset({"1000", "1200", "2900", "7900"})


def check_ledger_accounts(ep: dict) -> tuple[list[str], dict[str, int]]:
    """Check ledger account rules (a)-(d) and return any problems plus row counts."""
    problems: list[str] = []
    counts: dict[str, int] = {
        "total": 0,
        "check_a": 0,
        "check_b": 0,
        "check_c": 0,
        "check_d": 0,
        "check_d_debit": 0,
        "check_d_credit": 0,
    }

    policy_accounts = set(ep.get("policy", {}).get("ledger", {}).get("accounts", {}).keys())
    invoices = {inv["invoice_id"]: inv for inv in ep.get("tables", {}).get("invoices", [])}

    for row in ep.get("tables", {}).get("ledger", []):
        counts["total"] += 1
        row_id = row.get("row_id")
        acc = str(row.get("account"))
        iid = row.get("invoice_id")
        pid = row.get("payment_id")
        ent = row.get("entity_id")
        debit = row.get("debit_minor", 0)
        credit = row.get("credit_minor", 0)

        # (a) every ledger account is a key of policy.ledger.accounts
        if acc in policy_accounts:
            counts["check_a"] += 1
        else:
            problems.append(f"Row {row_id}: account {acc!r} not in policy accounts {sorted(policy_accounts)}")

        # (b) rows with invoice_id set and payment_id None
        if iid is not None and pid is None:
            counts["check_b"] += 1
            if acc not in INVOICE_ACCOUNTS:
                problems.append(
                    f"Row {row_id}: invoice booking row has account {acc!r}, expected one of {sorted(INVOICE_ACCOUNTS)}"
                )
            if iid not in invoices:
                problems.append(f"Row {row_id}: invoice_id {iid!r} not found in invoices table")
            else:
                expected_entity = invoices[iid].get("entity_id")
                if ent != expected_entity:
                    problems.append(
                        f"Row {row_id}: entity_id {ent!r} does not match invoice {iid!r} entity_id {expected_entity!r}"
                    )

        # (c) rows with payment_id set
        elif pid is not None:
            counts["check_c"] += 1
            if acc not in PAYMENT_ACCOUNTS:
                problems.append(
                    f"Row {row_id}: payment row (payment_id {pid!r}) has account {acc!r}, "
                    f"expected one of {sorted(PAYMENT_ACCOUNTS)}"
                )

        # (d) rows with no invoice_id and no payment_id
        else:
            counts["check_d"] += 1
            if ent is not None:
                problems.append(f"Row {row_id}: expense row has entity_id {ent!r}, expected None")

            is_debit = acc in EXPENSE_DEBIT_ACCOUNTS and debit > 0 and credit == 0
            is_credit = acc == "1000" and credit > 0 and debit == 0

            if is_debit:
                counts["check_d_debit"] += 1
            elif is_credit:
                counts["check_d_credit"] += 1
            else:
                problems.append(
                    f"Row {row_id}: expense row has invalid account/amounts (account={acc!r}, debit={debit}, credit={credit})"
                )

    return problems, counts


class LedgerAccountsTest(unittest.TestCase):
    def test_ledger_accounts_heavy_default(self):
        """100 heavy default seeds satisfy rules (a)-(d) with zero defects."""
        aggregated_counts = {
            "total": 0,
            "check_a": 0,
            "check_b": 0,
            "check_c": 0,
            "check_d": 0,
            "check_d_debit": 0,
            "check_d_credit": 0,
        }
        for seed in range(100):
            ep = generate(seed, HEAVY)
            problems, counts = check_ledger_accounts(ep)
            self.assertEqual(problems, [], f"Seed {seed} had ledger account problems: {problems}")
            for k, v in counts.items():
                aggregated_counts[k] += v

        self.assertEqual(aggregated_counts["total"], 34764)
        self.assertEqual(aggregated_counts["check_a"], 34764)
        self.assertEqual(aggregated_counts["check_b"], 8874)
        self.assertEqual(aggregated_counts["check_c"], 6998)
        self.assertEqual(aggregated_counts["check_d"], 18892)
        self.assertEqual(aggregated_counts["check_d_debit"], 9446)
        self.assertEqual(aggregated_counts["check_d_credit"], 9446)

    def test_ledger_accounts_heavy_hard(self):
        """100 heavy hard seeds satisfy rules (a)-(d) with zero defects."""
        aggregated_counts = {
            "total": 0,
            "check_a": 0,
            "check_b": 0,
            "check_c": 0,
            "check_d": 0,
            "check_d_debit": 0,
            "check_d_credit": 0,
        }
        cfg = {**HEAVY, "difficulty": "hard"}
        for seed in range(100):
            ep = generate(seed, cfg)
            problems, counts = check_ledger_accounts(ep)
            self.assertEqual(problems, [], f"Seed {seed} (hard) had ledger account problems: {problems}")
            for k, v in counts.items():
                aggregated_counts[k] += v

        self.assertEqual(aggregated_counts["total"], 117326)
        self.assertEqual(aggregated_counts["check_a"], 117326)
        self.assertEqual(aggregated_counts["check_b"], 9890)
        self.assertEqual(aggregated_counts["check_c"], 7108)
        self.assertEqual(aggregated_counts["check_d"], 100328)
        self.assertEqual(aggregated_counts["check_d_debit"], 50164)
        self.assertEqual(aggregated_counts["check_d_credit"], 50164)

    def test_clean_seed_0_expense_row_account_9999_detected(self):
        """Tampering an expense row to account '9999' on clean seed 0 is reported by the checker."""
        ep = generate(0, {"errors": {}})
        problems_before, _ = check_ledger_accounts(ep)
        self.assertEqual(problems_before, [])

        tampered = copy.deepcopy(ep)
        expense_row = next(
            r
            for r in tampered["tables"]["ledger"]
            if r.get("invoice_id") is None and r.get("payment_id") is None and r.get("account") in EXPENSE_DEBIT_ACCOUNTS
        )
        row_id = expense_row["row_id"]
        expense_row["account"] = "9999"

        problems_after, _ = check_ledger_accounts(tampered)
        self.assertGreater(len(problems_after), 0)
        self.assertTrue(
            any(row_id in p and "9999" in p for p in problems_after),
            f"Expected tamper on row {row_id} with account 9999 to be reported, got: {problems_after}",
        )

    def test_tampered_invoice_entity_detected(self):
        """Invoice booking row carrying wrong entity_id is reported."""
        ep = generate(0, {"errors": {}})
        tampered = copy.deepcopy(ep)
        row = next(
            r
            for r in tampered["tables"]["ledger"]
            if r.get("invoice_id") is not None and r.get("payment_id") is None
        )
        row["entity_id"] = "ENTITY_TAMPERED"
        problems, _ = check_ledger_accounts(tampered)
        self.assertTrue(any("ENTITY_TAMPERED" in p for p in problems))

    def test_tampered_payment_account_detected(self):
        """Payment row with unauthorized account is reported."""
        ep = generate(0, {"errors": {}})
        tampered = copy.deepcopy(ep)
        row = next(
            r
            for r in tampered["tables"]["ledger"]
            if r.get("payment_id") is not None
        )
        row["account"] = "4000"  # Revenue on payment
        problems, _ = check_ledger_accounts(tampered)
        self.assertTrue(any(row["row_id"] in p and "4000" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
