"""Harness-only offline tests; existing preview resolver remains authoritative."""
import ast
import html
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "AI.extension/lib"))
PATH = ROOT / "AI.extension/AI.tab/Dev.panel/M4APreview.pushbutton/script.py"


class Harness(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("preview_harness_test", PATH)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.output = Mock()
        self.host = object()
        self.context = {"test_snapshot": True}
        self.forms = Mock()
        self.forms.ask_for_string.return_value = "M4A_Test_01"
        self.pyrevit = N(HOST_APP=N(uiapp=self.host), forms=self.forms,
                         script=N(get_output=lambda: self.output))
        self.session = N(document_identity="fixture", tools=N(pending=None), ai=N(turn=None))
        modules = patch.dict(sys.modules, {"pyrevit.coreutils": N(
            envvars=N(get_pyrevit_env_var=lambda key: self.session))})
        modules.start()
        self.addCleanup(modules.stop)

    def invoke(self, result):
        with patch.dict(sys.modules, {"pyrevit": self.pyrevit}), \
                patch.object(self.module, "capture_preview_context", return_value=self.context), \
                patch.object(self.module, "build_preview", return_value=result) as builder:
            actual = self.module.main()
        return actual, builder

    def test_cancel_has_no_preview_or_output(self):
        self.forms.ask_for_string.return_value = None
        actual, builder = self.invoke({})
        self.assertIsNone(actual)
        builder.assert_not_called()
        self.output.print_html.assert_not_called()

    def test_exact_call_path(self):
        import bimcode_write_runtime
        self.assertIs(self.module.build_preview, bimcode_write_runtime.build_preview)
        result = dict(classification="MEP_PARAMETER_WRITE_PREVIEW_OK", reason_code="COMPLETE")
        actual, builder = self.invoke(result)
        self.assertIs(actual, result)
        builder.assert_called_once()
        args, kwargs = builder.call_args
        self.assertIs(args[0], self.host)
        self.assertEqual(len(args[1]), 32)
        self.assertEqual(args[2], "M4A_Test_01")
        self.assertEqual(kwargs, dict(selection_generation=None, context=self.context))

    def test_capture_precedes_dialog(self):
        calls = []
        with patch.dict(sys.modules, {"pyrevit": self.pyrevit}), \
                patch.object(self.module, "capture_preview_context",
                             side_effect=lambda app: calls.append("capture") or self.context), \
                patch.object(self.module, "build_preview", return_value={}):
            self.forms.ask_for_string.side_effect = lambda **kw: calls.append("dialog") or "Test"
            self.module.main()
        self.assertEqual(calls, ["capture", "dialog"])

    def test_invalid_values_are_not_normalized_or_dropped(self):
        for value in ("", " bad", "bad ", "bad\n", "bad\t", "X" * 65):
            self.forms.ask_for_string.return_value = value
            actual, builder = self.invoke(dict(reason_code="INVALID_VALUE"))
            self.assertEqual(builder.call_args[0][2], value)

    def test_result_roundtrip_and_html_safety(self):
        result = dict(current_value=None, proposed_value="M4A_Test_01",
                      document_identity={"title": "<script>&test</script>"},
                      warnings=[], confirmation_required=True,
                      transaction_started=False, model_modified=False)
        self.invoke(result)
        rendered = self.output.print_html.call_args[0][0]
        self.assertNotIn("<script>", rendered)
        self.assertEqual(json.loads(html.unescape(rendered[5:-6])), result)

    def test_failure_reasons_displayed_without_correction(self):
        for reason in ("NO_ELEMENTS_SELECTED", "MULTIPLE_ELEMENTS_SELECTED", "UNSUPPORTED_TARGET",
                       "PARAMETER_MISSING", "TARGET_NOT_WRITABLE", "STORAGE_TYPE_UNSUPPORTED",
                       "INVALID_VALUE", "NO_CHANGE_REQUIRED", "READ_FAILED"):
            result = dict(reason_code=reason)
            actual, builder = self.invoke(result)
            self.assertEqual(actual, result)
            self.assertIn(reason, self.output.print_html.call_args[0][0])
            builder.assert_called_once()

    def test_no_write_provider_selection_or_generated_code(self):
        tree = ast.parse(PATH.read_text())
        names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        names.update(node.id for node in ast.walk(tree) if isinstance(node, ast.Name))
        self.assertFalse(names & {"Set", "Transaction", "TransactionGroup", "ExternalEvent",
                                  "TaskDialog", "SetElementIds", "PickObject", "eval", "exec",
                                  "provision", "provider", "register"})

    def test_registry_and_catalog(self):
        from bimcode_ai_pane.ai_tool_registry import TOOLS
        self.assertEqual(len(TOOLS), 13)
        self.assertFalse(any("set_selected_pipe_test_text" == row[0] for row in TOOLS))
        self.assertEqual(len(json.loads((ROOT / "AI.extension/lib/prompt_catalog.json")
                                        .read_text(encoding="utf-8-sig"))), 237)
