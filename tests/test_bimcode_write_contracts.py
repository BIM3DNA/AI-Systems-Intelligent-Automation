"""Pure M4A contracts: no Revit, provider or credentials."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "AI.extension/lib"))
from bimcode_ai_pane import write_contracts as c


class Contracts(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(c.M4A_TEST_PARAMETER_GUID, "2f3c955d-45ee-4258-bc61-08acd40a2912")
        self.assertEqual(c.M4A_TEST_PARAMETER_NAME, "BIMCode_M4A_TestText")
        self.assertEqual(c.M4A_CATEGORY, "OST_PipeCurves")
        self.assertEqual(c.M4A_MAX_TEXT_LENGTH, 64)

    def test_valid(self):
        for value in ("A", "0", "Pipe 01_A-B", "A" * 64):
            self.assertEqual(c.validate_value(value), dict(valid=True, reason_code="COMPLETE", value=value))

    def test_invalid(self):
        for value in ("", " A", "A ", " ", "A\n", "A\r", "A\t", "A\x00", "A" * 65,
                      "A.B", "A/B", "_A", "-A", "é", None, 1, [], b"A"):
            with self.subTest(value=value):
                self.assertFalse(c.validate_value(value)["valid"])
