import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_recall_queues.py"
SPEC = importlib.util.spec_from_file_location("build_recall_queues", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def match(relation, confidence):
    return {"llmRelation": relation, "llmConfidence": confidence, "title": relation}


class BuildRecallQueuesTest(unittest.TestCase):
    def test_high_confidence_same_is_duplicate_evidence(self):
        decision, _, _ = MODULE.classify_question(
            {"matches": [match("same", 0.9), match("different", 0.99)]}, 0.85, 0.8, 0.85
        )
        self.assertEqual(decision, "duplicate_evidence")

    def test_overlap_wins_over_different(self):
        decision, _, _ = MODULE.classify_question(
            {"matches": [match("overlap", 0.9), match("different", 0.99)]}, 0.85, 0.8, 0.85
        )
        self.assertEqual(decision, "enhancement")

    def test_only_different_becomes_novel(self):
        decision, _, _ = MODULE.classify_question(
            {"matches": [match("different", 0.95)]}, 0.85, 0.8, 0.85
        )
        self.assertEqual(decision, "novel")

    def test_low_confidence_overlap_requires_review(self):
        decision, _, _ = MODULE.classify_question(
            {"matches": [match("overlap", 0.7), match("different", 0.99)]}, 0.85, 0.8, 0.85
        )
        self.assertEqual(decision, "review")

    def test_personal_question_is_out_of_scope(self):
        self.assertEqual(MODULE.scope_decision("你的职业规划是什么？")[0], "out_of_scope")
        self.assertIsNone(MODULE.scope_decision("Agent Runtime 如何传播取消信号？"))

    def test_incomplete_question_requires_review(self):
        self.assertEqual(MODULE.scope_decision("这些框架有什么区别？")[0], "review")



if __name__ == "__main__":
    unittest.main()
