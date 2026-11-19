import os
import subprocess
import sys
import unittest


class DemoTest(unittest.TestCase):
    def test_findings_and_grader_print_minor_units(self):
        env = os.environ.copy()
        env.pop("AUDITENV_SECRET", None)
        demo = subprocess.run(
            [sys.executable, "-m", "auditenv.demo", "--seed", "2003"],
            env=env, capture_output=True, text=True, check=True,
        )
        for amount in (286, 351331):
            with self.subTest(amount=amount):
                self.assertEqual(demo.stdout.count(f"{amount} USD minor units"), 2)
