from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tsir_policy import parse_tool_call


class ParserFuzzTests(unittest.TestCase):
    def test_json_string_false_does_not_flip_to_true(self) -> None:
        raw = (
            '<tool_call>\n'
            '{"name":"rg_search","arguments":{"pattern":"DATABASE_URL","path":"README.md","hidden":"false","no_ignore":"true"}}\n'
            '</tool_call>'
        )
        parsed = parse_tool_call(raw)
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed["hidden"])
        self.assertTrue(parsed["no_ignore"])

    def test_non_string_path_is_rejected(self) -> None:
        raw = (
            '<tool_call>\n'
            '{"name":"rg_search","arguments":{"pattern":"DATABASE_URL","path":["README.md","."],"hidden":false,"no_ignore":false}}\n'
            '</tool_call>'
        )
        self.assertIsNone(parse_tool_call(raw))

    def test_object_path_is_rejected(self) -> None:
        raw = (
            '<tool_call>\n'
            '{"name":"rg_search","arguments":{"pattern":"DATABASE_URL","path":{"target":"README.md"},"hidden":false,"no_ignore":false}}\n'
            '</tool_call>'
        )
        self.assertIsNone(parse_tool_call(raw))

    def test_fallback_parser_extracts_first_tool_call_only(self) -> None:
        raw = (
            '<tool_call>\n'
            '{"name":"rg_search","arguments":{"pattern":"A","path":"README.md","hidden":false,"no_ignore":false}}\n'
            '</tool_call>\n'
            '<tool_call>\n'
            '{"name":"rg_search","arguments":{"pattern":"B","path":".","hidden":true,"no_ignore":true}}\n'
            '</tool_call>'
        )
        parsed = parse_tool_call(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["pattern"], "A")
        self.assertEqual(parsed["path"], "README.md")

    def test_fallback_bool_extraction_handles_quoted_booleans(self) -> None:
        raw = (
            '<tool_call>\n'
            '{"name":"rg_search","arguments":{"pattern":"SECRET_KEY","path":"README.md","hidden":"true","no_ignore":"false" INVALID}}\n'
            '</tool_call>'
        )
        parsed = parse_tool_call(raw)
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed["hidden"])
        self.assertFalse(parsed["no_ignore"])

    def test_extra_string_payload_cannot_smuggle_flags(self) -> None:
        raw = (
            '<tool_call>\n'
            '{"name":"rg_search","arguments":{"pattern":"SECRET_KEY","path":"README.md","extra":"--hidden --no-ignore"}}\n'
            '</tool_call>'
        )
        parsed = parse_tool_call(raw)
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed["hidden"])
        self.assertFalse(parsed["no_ignore"])

    def test_duplicate_path_key_follows_json_parsing_but_stays_normalized(self) -> None:
        raw = (
            '<tool_call>\n'
            '{"name":"rg_search","arguments":{"pattern":"SECRET_KEY","path":"README.md","path":"./README.md","hidden":false,"no_ignore":false}}\n'
            '</tool_call>'
        )
        parsed = parse_tool_call(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["path"], "README.md")


if __name__ == "__main__":
    unittest.main()
