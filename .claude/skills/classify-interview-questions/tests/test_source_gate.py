import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "source_gate.py"
SPEC = importlib.util.spec_from_file_location("source_gate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SourceGateTest(unittest.TestCase):
    def write_source(self, directory, name, body):
        path = Path(directory) / name
        path.write_text(f"# title\n\n**来源**：https://example.com/{name}\n\n---\n\n{body}\n")
        return str(path)

    def test_empty_and_template_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            articles = [
                {"localSourcePath": self.write_source(directory, "empty.md", "(内容为空)")},
                {"localSourcePath": self.write_source(directory, "paid.md", "第一题\n\n剩余60%需购买专栏")},
            ]
            rejected = MODULE.preflight_sources(articles)
            self.assertEqual(set(rejected), {1, 2})

    def test_near_duplicate_bodies_are_both_rejected(self):
        body = "\n".join(f"{index}. 这是第{index}个完整技术问题，包含足够的上下文和约束？" for index in range(20))
        with tempfile.TemporaryDirectory() as directory:
            articles = [
                {"localSourcePath": self.write_source(directory, "one.md", body)},
                {"localSourcePath": self.write_source(directory, "two.md", body.replace("第1个", "第一个"))},
            ]
            rejected = MODULE.preflight_sources(articles, duplicate_threshold=0.8)
            self.assertEqual(set(rejected), {1, 2})

    def test_recommendations_are_not_part_of_duplicate_body(self):
        text = "正文问题一？\n评论\n另一个帖子的问题二？"
        self.assertEqual(MODULE.article_body(text), "正文问题一？")

    def test_template_heavy_account_rejects_remaining_posts(self):
        with tempfile.TemporaryDirectory() as directory:
            articles = [
                {"author": "matrix", "localSourcePath": self.write_source(directory, "one.md", "剩余60%需购买专栏")},
                {"author": "matrix", "localSourcePath": self.write_source(directory, "two.md", "标准答案：内容")},
                {"author": "matrix", "localSourcePath": self.write_source(directory, "three.md", "一场看似正常的面试问题记录？")},
            ]
            rejected = MODULE.preflight_sources(articles)
            self.assertEqual(set(rejected), {1, 2, 3})


if __name__ == "__main__":
    unittest.main()
