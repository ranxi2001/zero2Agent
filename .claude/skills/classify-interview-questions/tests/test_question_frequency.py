import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("question_frequency", SCRIPT_DIR / "question_frequency.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class QuestionFrequencyTest(unittest.TestCase):
    def test_named_primary_and_annotations_are_counted(self):
        evidence = MODULE.infer_evidence(
            "腾讯终面 【蚂蚁二面同题：ReAct 原理】【字节二面追问：架构取舍】"
        )
        self.assertEqual(len(evidence), 3)

    def test_generic_collections_do_not_inflate_frequency(self):
        self.assertEqual(MODULE.infer_evidence("30题"), [])
        self.assertEqual(MODULE.infer_evidence("已有正文（补录索引）"), [])
        self.assertEqual(MODULE.infer_evidence("Agent开发八股合集（南京大学）"), [])
        self.assertEqual(MODULE.infer_evidence("Agent Runtime 管线高频题"), [])

    def test_unattributed_followup_does_not_add_occurrence(self):
        evidence = MODULE.infer_evidence("字节一面 【含追问：记忆更新策略】")
        self.assertEqual(evidence, ["字节一面"])

    def test_ai_infra_summary_is_split_into_occurrences(self):
        evidence = MODULE.infer_evidence("阿里/美团/字节等 AI Infra 面经（新增）")
        self.assertEqual(len(evidence), 3)

    def test_question_detail_separators_do_not_inflate_frequency(self):
        evidence = MODULE.infer_evidence(
            "字节一面 【火山引擎一面追问：开发、测试、运维 Skills 如何组织】"
        )
        self.assertEqual(len(evidence), 2)

    def test_multi_source_annotation_counts_each_interview(self):
        evidence = MODULE.infer_evidence("字节一面 【高德/百度二面同题：如何压缩上下文】")
        self.assertEqual(len(evidence), 3)

    def test_markdown_source_links_are_preserved_as_separate_evidence(self):
        evidence = MODULE.infer_evidence(
            "[阿里云 Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/a)"
            "【[百度 AI Infra 二面](https://www.nowcoder.com/feed/main/detail/b)】"
        )
        self.assertEqual(
            evidence,
            [
                "[阿里云 Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/a)",
                "[百度 AI Infra 二面](https://www.nowcoder.com/feed/main/detail/b)",
            ],
        )

    def test_multiple_markdown_links_in_one_source_block_are_split(self):
        evidence = MODULE.infer_evidence(
            "[百度一面](https://www.nowcoder.com/feed/main/detail/a) / "
            "[虾皮一面](https://www.nowcoder.com/feed/main/detail/b) / "
            "[字节一面](https://www.nowcoder.com/feed/main/detail/c)"
        )
        self.assertEqual(
            evidence,
            [
                "[百度一面](https://www.nowcoder.com/feed/main/detail/a)",
                "[虾皮一面](https://www.nowcoder.com/feed/main/detail/b)",
                "[字节一面](https://www.nowcoder.com/feed/main/detail/c)",
            ],
        )
    def test_frequency_must_equal_evidence_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frequency.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "questions": [
                            {
                                "dimension": "01-test",
                                "title": "测试题",
                                "frequency": 2,
                                "firstSeenOrder": 1,
                                "evidence": ["腾讯一面"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Frequency differs"):
                MODULE.load_frequency(path)

    def test_duplicate_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frequency.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "questions": [
                            {
                                "dimension": "01-test",
                                "title": "测试题",
                                "frequency": 2,
                                "firstSeenOrder": 1,
                                "evidence": ["腾讯一面", "腾讯一面"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Duplicate evidence"):
                MODULE.load_frequency(path)

    def test_sync_assigns_new_order_after_existing_maximum(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index_path = root / "question-index.md"
            frequency_path = root / "question-frequency.json"
            index_path.write_text(
                "## 01-test（2题）\n\n1. 已有题 — 腾讯一面\n2. 新题 — 字节一面\n",
                encoding="utf-8",
            )
            frequency_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "questions": [
                            {
                                "dimension": "01-test",
                                "title": "已有题",
                                "frequency": 1,
                                "firstSeenOrder": 3,
                                "evidence": ["腾讯一面"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "sync_question_frequency.py"),
                    "--index",
                    str(index_path),
                    "--out",
                    str(frequency_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(frequency_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["questions"][1]["firstSeenOrder"], 4)

    def test_index_source_must_exist_in_frequency_evidence(self):
        questions = [
            MODULE.IndexQuestion(
                "01-test",
                1,
                "测试题",
                "腾讯一面 【字节二面同题：测试题】",
            )
        ]
        records = {
            ("01-test", "测试题"): {
                "dimension": "01-test",
                "title": "测试题",
                "frequency": 1,
                "firstSeenOrder": 1,
                "evidence": ["腾讯一面"],
            }
        }
        with self.assertRaisesRegex(ValueError, "evidence is stale"):
            MODULE.validate_coverage(questions, records)


if __name__ == "__main__":
    unittest.main()
