import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location(
    "sort_questions_by_frequency", SCRIPT_DIR / "sort_questions_by_frequency.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SortQuestionsByFrequencyTest(unittest.TestCase):
    def test_sorts_stably_inside_existing_groups(self):
        markdown = """# 示例

## 主题 A

### Q：低频题

> 来源：甲公司一面

低频答案。

---

### Q：高频题

> 来源：乙公司一面

高频答案。

---

## 主题 B

### Q：同频题一

> 来源：丙公司一面

答案一。

### Q：同频题二

> 来源：丁公司一面

答案二。

## 这类题的答题模式

结尾。
"""
        questions = [
            MODULE.IndexQuestion("01-example", 1, "低频题", "甲公司一面"),
            MODULE.IndexQuestion("01-example", 2, "高频题", "乙公司一面"),
            MODULE.IndexQuestion("01-example", 3, "同频题一", "丙公司一面"),
            MODULE.IndexQuestion("01-example", 4, "同频题二", "丁公司一面"),
        ]
        frequency = {
            ("01-example", "低频题"): {"frequency": 1, "firstSeenOrder": 1},
            ("01-example", "高频题"): {"frequency": 3, "firstSeenOrder": 2},
            ("01-example", "同频题一"): {"frequency": 2, "firstSeenOrder": 3},
            ("01-example", "同频题二"): {"frequency": 2, "firstSeenOrder": 4},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.md"
            path.write_text(markdown, encoding="utf-8")
            sorted_markdown, permutation = MODULE.sort_article(path, questions, frequency)

        self.assertLess(sorted_markdown.index("Q：高频题"), sorted_markdown.index("Q：低频题"))
        self.assertLess(sorted_markdown.index("Q：低频题"), sorted_markdown.index("## 主题 B"))
        self.assertLess(sorted_markdown.index("Q：同频题一"), sorted_markdown.index("Q：同频题二"))
        self.assertEqual(permutation, [1, 0, 2, 3])


if __name__ == "__main__":
    unittest.main()
