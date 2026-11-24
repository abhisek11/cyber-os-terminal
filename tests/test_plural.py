"""Unit tests for `plural()`, which keeps counts like `1 thread` and `2 threads` grammatical."""

import unittest

import cyber_tools


class PluralTest(unittest.TestCase):
    def test_one_is_singular(self):
        self.assertEqual(cyber_tools.plural(1, "thread"), "1 thread")
        self.assertEqual(cyber_tools.plural(1, "open port"), "1 open port")

    def test_zero_and_many_are_plural(self):
        self.assertEqual(cyber_tools.plural(0, "thread"), "0 threads")
        self.assertEqual(cyber_tools.plural(2, "thread"), "2 threads")
        self.assertEqual(cyber_tools.plural(37, "active scheduled/daemon job"), "37 active scheduled/daemon jobs")

    def test_a_plural_form_can_be_given(self):
        self.assertEqual(cyber_tools.plural(1, "PROCESS", "PROCESSES"), "1 PROCESS")
        self.assertEqual(cyber_tools.plural(3, "PROCESS", "PROCESSES"), "3 PROCESSES")


if __name__ == "__main__":
    unittest.main()
