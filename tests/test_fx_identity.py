import unittest

from auditenv.generator import generate
from auditenv.verify import verify_episode


class FXIdentityTest(unittest.TestCase):
    def test_swapped_rate_labels(self):
        episode = generate(0, {"errors": {}})
        self.assertEqual(verify_episode(episode), [])
        first, second = episode["tables"]["fx"][:2]
        first["fx_id"], second["fx_id"] = second["fx_id"], first["fx_id"]
        self.assertTrue(any("fx_id" in p for p in verify_episode(episode)))

    def test_duplicate_rate_key(self):
        episode = generate(0, {"errors": {}})
        first, second = episode["tables"]["fx"][:2]
        second.update({k: first[k] for k in ("date", "source_currency", "target_currency")})
        self.assertTrue(any("duplicate FX rate" in p for p in verify_episode(episode)))
