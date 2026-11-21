"""Generator configs for the jury's Block 2 scenarios D01-D20 (genesis-exe.com/fintech-checks.html), documented in
README "Jury adapter". The jury picks its own hidden seeds; these are only the documented settings per scenario.
Pass one to `judge_adapter.generate_episode(seed, config, output_dir)`."""

NONE = {"I1": 0, "I2": 0}  # with "errors" given, exactly the listed errors and no random interacting pair

SCENARIOS = {
    # D01-D05 clean companies: truth is empty. Every clean episode keeps the distractors (split payments,
    # refunds, unidentified receipts, repeated amounts, foreign currencies, records on the period's edges).
    **{f"D{n:02d}": {"errors": {}, "interacting": NONE} for n in range(1, 6)},
    **{f"D{n:02d}": {"errors": {"duplicate_invoice": 1}, "interacting": NONE} for n in range(6, 9)},
    "D09": {"errors": {"payment_allocation": 1}, "interacting": NONE, "allocation": "missing"},
    "D10": {"errors": {"payment_allocation": 1}, "interacting": NONE, "allocation": "partial"},
    "D11": {"errors": {"payment_allocation": 1}, "interacting": NONE},  # variant drawn: 60 % partial
    **{f"D{n:02d}": {"errors": {"fx_error": 1}, "interacting": NONE} for n in range(12, 14)},
    **{f"D{n:02d}": {"errors": {"period_cutoff": 1}, "interacting": NONE} for n in range(14, 16)},
    **{f"D{n:02d}": {"errors": {}, "interacting": {"I1": 1, "I2": 0}} for n in range(16, 19)},
    **{f"D{n:02d}": {"errors": {}, "interacting": {"I1": 0, "I2": 1}} for n in range(19, 21)},
}
