import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "recall_similar_questions.py"
SPEC = importlib.util.spec_from_file_location("recall_similar_questions", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RecallSimilarQuestionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        index_path = Path(__file__).resolve().parents[1] / "question-index.md"
        cls.documents = MODULE.parse_index(index_path)

    def test_utf8_stdin_decoding(self):
        text = "一次 Agent 请求的完整执行链路是什么？\n"
        self.assertEqual(MODULE.decode_input(text.encode("utf-8")), text)

    def test_utf16_stdin_decoding(self):
        text = "如何评测两个 Skill？\n"
        self.assertEqual(MODULE.decode_input(text.encode("utf-16")), text)

    def test_default_indexes_include_backend_questions(self):
        paths = MODULE.default_index_paths()
        self.assertEqual(paths[0].suffix, ".json")
        documents = MODULE.parse_indexes(paths)
        titles = {document.title for document in documents}
        self.assertIn("Cookie、Session 和 JWT 有什么区别？JWT 的结构和验签流程是什么？", titles)
        self.assertGreater(len(documents), len(self.documents))

    def test_machine_agent_index_has_592_questions(self):
        json_index = Path(__file__).resolve().parents[1] / "question-index.json"
        documents = MODULE.parse_index(json_index)
        self.assertEqual(len(documents), 592)

    def test_exact_question_is_top_match(self):
        query = "一次 Agent 请求的完整执行链路是什么？"
        matches = MODULE.recall(query, self.documents, 5)
        self.assertEqual(matches[0]["dimension"], "16-agent-infra")
        self.assertEqual(matches[0]["title"], query)

    def test_tool_result_query_recalls_tool_management(self):
        query = "Function Call 的 Tool Result 怎么重新进入模型上下文？"
        matches = MODULE.recall(query, self.documents, 5)
        dimensions = {match["dimension"] for match in matches[:3]}
        self.assertIn("02-tool-management", dimensions)

    def test_tool_decision_semantic_alias(self):
        query = "大模型如何判断是否需要调用工具？"
        matches = MODULE.recall(query, self.documents, 5)
        titles = {match["title"] for match in matches[:3]}
        self.assertIn("Agent 的 thinking 阶段怎么决定是调用工具还是直接回复？", titles)

    def test_loop_exit_semantic_alias(self):
        query = "Agent Loop 在什么条件下继续执行，又在什么条件下结束？"
        matches = MODULE.recall(query, self.documents, 5)
        titles = {match["title"] for match in matches[:3]}
        self.assertIn("Agent 如何判断已经收集了足够的信息，最终给出输出结论？", titles)

    def test_auto_research_semantic_alias(self):
        query = "如何用 Agent 做 Auto Research？"
        matches = MODULE.recall(query, self.documents, 5)
        titles = {match["title"] for match in matches[:3]}
        self.assertIn("Deep Research 在代码层面是怎么实现的？和普通 RAG 有什么区别？", titles)

    def test_skill_eval_semantic_alias(self):
        query = "如何通过评价脚本或模型评审对比两个 Skill 的输出？"
        matches = MODULE.recall(query, self.documents, 5)
        dimensions = {match["dimension"] for match in matches[:3]}
        self.assertTrue(dimensions <= {"05-eval-and-vision", "08-prompt-engineering"})
        self.assertGreater(matches[0]["score"], 0.5)

    def test_source_annotations_participate_in_recall(self):
        query = "如何用 Coding Agent 完成项目开发？"
        matches = MODULE.recall(query, self.documents, 5)
        titles = {match["title"] for match in matches[:3]}
        self.assertIn("用过哪些 Code Agent？优缺点？", titles)

    def test_react_semantic_alias(self):
        query = "ReAct 是什么？Reasoning 和 Action 如何形成循环？"
        matches = MODULE.recall(query, self.documents, 5)
        titles = [match["title"] for match in matches[:3]]
        self.assertGreaterEqual(sum("ReAct" in title for title in titles), 2)
        self.assertGreater(matches[0]["score"], 0.5)

    def test_full_chain_paraphrase(self):
        query = "一次 Agent 请求从用户输入到最终回答的完整链路是什么？"
        matches = MODULE.recall(query, self.documents, 5)
        titles = {match["title"] for match in matches[:3]}
        self.assertIn("一次 Agent 请求的完整执行链路是什么？", titles)

    def test_backend_jwt_semantic_alias(self):
        documents = MODULE.parse_indexes(MODULE.default_index_paths())
        query = "服务端如何验证 JWT 的真实性和完整性？"
        matches = MODULE.recall(query, documents, 5)
        self.assertEqual(
            matches[0]["title"],
            "Cookie、Session 和 JWT 有什么区别？JWT 的结构和验签流程是什么？",
        )

    def test_os_memory_management_semantic_alias(self):
        documents = MODULE.parse_indexes(MODULE.default_index_paths())
        query = "操作系统是怎么进行内存管理的？为什么虚拟内存和物理内存要分开？"
        matches = MODULE.recall(query, documents, 5)
        self.assertEqual(
            matches[0]["title"],
            "操作系统如何管理内存？为什么要把虚拟内存与物理内存分开？",
        )


if __name__ == "__main__":
    unittest.main()
