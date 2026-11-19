"""Grader-only oracle: submits the truth with one full evidence set and no inspection steps.
It checks the reward ceiling, not agent ability. Never give it to a policy under evaluation."""

from __future__ import annotations


class Oracle:
    name = "oracle"

    def __init__(self, truth: dict):
        self.truth = truth

    def reset(self, first_observation: dict) -> None:
        self.episode_id = first_observation["manifest"]["episode_id"]

    def act(self, observation: dict) -> dict:
        findings = [{"type": i["type"], "affected_ids": list(i["affected_ids"]),
                     "claimed_amount_minor": i["expected_amount_minor"], "currency": i["currency"],
                     "evidence_ids": list(i["evidence_sets"][0]), "explanation": "oracle"}
                    for i in self.truth["issues"]]
        return {"type": "submit", "findings": {"episode_id": self.episode_id, "findings": findings}}
