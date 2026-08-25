import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("extract_and_recall", SCRIPT_DIR / "extract_and_recall.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ExtractAndRecallTest(unittest.TestCase):
    def test_html_list_extraction(self):
        source = """
        <p>下面是面试问到的问题：</p>
        <ol>
          <li>什么是 Agent？</li>
          <li>如何选择工具？</li>
        </ol>
        <p>面试感想：有点难。</p>
        """
        questions = MODULE.extract_questions(MODULE.html_to_text(source))
        self.assertEqual(questions, ["什么是 Agent？", "如何选择工具？"])

    def test_plain_numbered_questions(self):
        source = """
        三、Agent 原理
        1. 一次 Agent 请求的完整链路是什么？
        2. 如何记录实验失败路线？
        作者：示例
        """
        self.assertEqual(
            MODULE.extract_questions(source),
            ["一次 Agent 请求的完整链路是什么？", "如何记录实验失败路线？"],
        )

    def test_parse_nowcoder_initial_state(self):
        state = {
            "prefetchData": {
                "2": {
                    "ssrCommonData": {
                        "contentData": {
                            "title": "Example",
                            "richText": "<ol><li>为什么需要 Agent？</li></ol>",
                        }
                    }
                }
            }
        }
        page = f"<script>{MODULE.INITIAL_STATE_MARKER}{__import__('json').dumps(state)};(function(){{}})()</script>"
        title, text = MODULE.parse_nowcoder_html(page)
        self.assertEqual(title, "Example")
        self.assertEqual(MODULE.extract_questions(text), ["为什么需要 Agent？"])

    def test_recall_band(self):
        self.assertEqual(MODULE.recall_band(0.8), "high")
        self.assertEqual(MODULE.recall_band(0.6), "review")
        self.assertEqual(MODULE.recall_band(0.2), "low")

    def test_load_json_codex_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "provider": {
                            "baseURL": "https://llm.example.test/v1",
                            "token": "secret-value",
                            "model": "test-model",
                            "wireApi": "responses",
                        }
                    }
                ),
                encoding="utf-8",
            )
            config = MODULE.load_codex_api_config(str(path))
        self.assertEqual(config.base_url, "https://llm.example.test/v1")
        self.assertEqual(config.token, "secret-value")
        self.assertEqual(config.model, "test-model")
        self.assertNotIn("secret-value", json.dumps(config.safe_summary()))

    def test_parse_chat_completion_json(self):
        payload = {"choices": [{"message": {"content": '```json\n{"questions":["Q1"]}\n```'}}]}
        parsed = MODULE.parse_model_json(MODULE.extract_model_text(payload))
        self.assertEqual(parsed["questions"], ["Q1"])

    def test_parse_responses_json(self):
        payload = {"output": [{"content": [{"type": "output_text", "text": '{"questions":["Q2"]}'}]}]}
        parsed = MODULE.parse_model_json(MODULE.extract_model_text(payload))
        self.assertEqual(parsed["questions"], ["Q2"])

    def test_chunk_text(self):
        chunks = MODULE.chunk_text("A" * 20 + "\n\n" + "B" * 20, maximum_chars=25)
        self.assertEqual(chunks, ["A" * 20, "B" * 20])

    def test_firsthand_interview_gate(self):
        result = MODULE.classify_interview_experience(
            "字节 Agent 一面面经",
            "面试时间：8月20日\n1. Agent Loop 如何结束？",
        )
        self.assertTrue(result["isInterviewExperience"])

    def test_offer_post_is_rejected(self):
        result = MODULE.classify_interview_experience(
            "AI Infra offer 帮选",
            "1. 如何选择两个 offer？",
        )
        self.assertFalse(result["isInterviewExperience"])

    def test_question_compilation_is_rejected(self):
        result = MODULE.classify_interview_experience(
            "AI Infra 面试题汇总",
            "1. 什么是 CUDA？\n2. 如何优化推理？",
        )
        self.assertFalse(result["isInterviewExperience"])


if __name__ == "__main__":
    unittest.main()
