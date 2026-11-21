"""The baseline-policy adapter (`auditenv.jury_run.JuryPolicy`) is faithful: a policy behind the jury's protocol
takes the same actions and gets the same grade as the same policy on `AuditEnv` directly."""

import os
import tempfile
import unittest
from unittest import mock

import judge_adapter as ja
from auditenv.env import AuditEnv
from auditenv.jury import SCENARIOS
from auditenv.jury_run import JuryPolicy, main, run
from auditenv.policies.flag_all import FlagAll
from auditenv.policies.random_explorer import RandomExplorer
from auditenv.policies.reconcile import Reconcile
from auditenv.run import run_episode

ja._WARNED = True  # public test seeds: the grader-key warning is tested on its own
os.environ.setdefault("AUDITENV_KEY_FILE", os.path.join(tempfile.mkdtemp(), "grader.key"))  # not ~/.auditenv


class JuryPolicyTest(unittest.TestCase):
    @mock.patch.dict(os.environ, {"AUDITENV_SECRET": "test-only-key"})  # one key for the adapter and AuditEnv
    def test_same_actions_and_grade_as_on_auditenv(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("D06", "D10", "D16", "D19", "D03"):
                path = os.path.join(tmp, name)
                ja.generate_episode(4200, SCENARIOS[name], path)
                for cls in (Reconcile, RandomExplorer, FlagAll):
                    with self.subTest(scenario=name, policy=cls.name):
                        direct = AuditEnv()
                        traj = run_episode(direct, cls(seed=0), 4200, {**SCENARIOS[name], "mode": "eval"})
                        env, policy = ja.make_env(), JuryPolicy(cls(seed=0))
                        obs, _ = env.reset(0, {"mode": "closed", "episode_dir": path, "team_config": {}})
                        actions = []
                        while True:
                            action = policy.act(obs)
                            actions.append({"type": action["name"], **action["args"]})
                            obs, _, terminated, truncated, _ = env.step(action)
                            if terminated or truncated:
                                break
                        self.assertEqual(actions, [t["action"] for t in traj[1:]])
                        keys = ("tp", "fp", "fn", "reward", "inspection_steps")
                        self.assertEqual({k: env.grader_log[-1][k] for k in keys},
                                         {k: direct.grader_log[-1][k] for k in keys})

    def test_jury_flow_table(self):
        rows = run(3000)
        self.assertEqual(rows["oracle"]["mean_return"], 1.0)
        self.assertEqual(rows["reconcile"]["f1"], 1.0)
        self.assertTrue(all(r["episodes"] == 20 for r in rows.values()))


class PolicyImageTest(unittest.TestCase):
    def test_missing_docker_is_a_clean_error(self):
        with mock.patch("shutil.which", return_value=None), mock.patch("sys.stderr") as err:
            self.assertEqual(main(["--policy-image", "genesis-policy"]), 2)
        self.assertIn("docker", "".join(c.args[0] for c in err.write.call_args_list))


if __name__ == "__main__":
    unittest.main()
