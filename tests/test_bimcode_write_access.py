"""Offline M4B-0/1 foundation; no Revit, credentials, or provider requests."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "AI.extension/lib"))
from bimcode_ai_pane.write_access import ControlledWritePermission, document_eligibility
from bimcode_ai_pane import controlled_write_registry as registry
from bimcode_ai_pane import write_contracts


def facts():
    return dict(valid_document=True, active_uidocument=True, family_document=False,
                host_document=True, linked_document=False, workshared=False,
                read_only=False, modifiable=False, fixed_parameter_available=True,
                fixed_parameter_binding_valid=True)


class PermissionTests(unittest.TestCase):
    def test_default_and_new_session(self):
        old = ControlledWritePermission()
        self.assertFalse(old.view_model()["enabled"])
        self.assertTrue(old.enable_from_human("doc", facts(), True))
        self.assertFalse(ControlledWritePermission().view_model()["enabled"])

    def test_enable_and_disable(self):
        state = ControlledWritePermission()
        self.assertTrue(state.enable_from_human("doc", facts(), True))
        self.assertEqual(state.view_model()["status"], "CONTROLLED WRITES: ENABLED FOR THIS SESSION")
        self.assertFalse(state.view_model()["provider_exposure_allowed"])
        state.disable()
        self.assertEqual(state.view_model()["status"], "CONTROLLED WRITES: DISABLED")

    def test_human_consent_required_each_time(self):
        state = ControlledWritePermission()
        state.enable_from_human("doc", facts(), True)
        for consent in (False, None, 1, "true"):
            self.assertFalse(state.enable_from_human("doc", facts(), consent))
            self.assertFalse(state.view_model()["enabled"])

    def test_lifecycle_reset_contracts(self):
        for event in ("document_closed", "pane_disposed", "shutdown"):
            state = ControlledWritePermission()
            state.enable_from_human("doc", facts(), True)
            getattr(state, event)()
            self.assertFalse(state.view_model()["enabled"])
            self.assertIsNone(state.view_model()["document_key"])

    def test_document_switch_and_return(self):
        state = ControlledWritePermission()
        state.enable_from_human("doc", facts(), True)
        state.document_changed("doc")
        self.assertTrue(state.view_model()["enabled"])
        state.document_changed("other")
        state.document_changed("doc")
        self.assertFalse(state.view_model()["enabled"])

    def test_environment_does_not_enable(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-test-value", "CONTROLLED_WRITES": "true"}):
            self.assertFalse(ControlledWritePermission().view_model()["enabled"])

    def test_no_persistence(self):
        with patch("builtins.open", side_effect=AssertionError("disk access")):
            state = ControlledWritePermission()
            state.enable_from_human("doc", facts(), True)
            state.shutdown()

    def test_eligibility(self):
        self.assertTrue(document_eligibility(facts())["eligible"])
        reasons = dict(valid_document="NO_VALID_DOCUMENT", active_uidocument="NO_ACTIVE_UIDOCUMENT",
                       family_document="FAMILY_DOCUMENT", host_document="NON_HOST_CONTEXT",
                       linked_document="LINKED_DOCUMENT", workshared="WORKSHARED_DOCUMENT",
                       read_only="READ_ONLY_DOCUMENT", modifiable="DOCUMENT_MODIFIABLE",
                       fixed_parameter_available="FIXED_PARAMETER_MISSING",
                       fixed_parameter_binding_valid="FIXED_PARAMETER_BINDING_INVALID")
        for key, reason in reasons.items():
            item = facts()
            item[key] = not item[key]
            self.assertEqual(document_eligibility(item)["reason_code"], reason)
            self.assertFalse(ControlledWritePermission().enable_from_human("doc", item, True))

    def test_unknown_facts_fail_closed(self):
        for item in (None, {}, [], {"valid_document": 1}):
            self.assertFalse(document_eligibility(item)["eligible"])


class RegistryTests(unittest.TestCase):
    def test_active_surface_and_write_rejection(self):
        sys.path.insert(0, str(ROOT / "BIMCode_Provider"))
        import provider
        import tool_protocol
        from bimcode_ai_pane import provider_bridge
        state = ControlledWritePermission()
        for enabled in (False, True):
            if enabled:
                state.enable_from_human("doc", facts(), True)
            self.assertEqual(len(provider.TOOLS), 13)
            self.assertEqual(tuple(provider.TOOLS), provider.READ_ONLY_TOOL_REGISTRY)
            names = [tool["name"] for tool in provider.TOOLS]
            self.assertEqual(len(set(names)), 13)
            self.assertEqual(set(names), set(tool_protocol.ACTIONS))
            self.assertNotIn("set_selected_pipe_test_text", names)
        call = dict(call_id="call_test", name="set_selected_pipe_test_text", arguments={"value": "A"})
        with self.assertRaises(tool_protocol.ToolError):
            tool_protocol.validate_call(call)
        self.assertNotIn("set_selected_pipe_test_text", provider_bridge.ACTIONS)

    def test_metadata(self):
        self.assertEqual(len(registry.READ_ONLY_TOOL_REGISTRY), 13)
        self.assertEqual(len(registry.CONTROLLED_WRITE_TOOL_REGISTRY), 1)
        entry = registry.metadata()[0]
        self.assertEqual(entry["tool_name"], "set_selected_pipe_test_text")
        self.assertEqual(entry["action_id"], "MEP-PARAM-WR-001-A01")
        self.assertEqual(entry["safety_class"], "CONTROLLED_WRITE")
        self.assertEqual(entry["dispatcher_state"], "NOT_IMPLEMENTED")
        self.assertIs(entry["provider_exposure_allowed"], False)
        self.assertEqual(entry["schema"]["required"], ["value"])
        self.assertFalse(entry["schema"]["additionalProperties"])
        entry["schema"]["required"].append("confirmed")
        self.assertEqual(registry.metadata()[0]["schema"]["required"], ["value"])

    def test_scalar_parity(self):
        for value in ("A", "A" * 64, "M4A_AI_01", "A B-C_0", "", " A", "A ", " ",
                      "A\n", "A\t", "A\x00", "A" * 65, "a/b", "https://x", "x.py",
                      "x()", "cmd.exe", [], None, 1, True):
            self.assertEqual(registry.validate_arguments({"value": value}), write_contracts.validate_value(value))

    def test_forbidden_fields(self):
        for key in ("confirmation", "confirmed", "ElementId", "element_ids", "parameter",
                    "parameter_name", "parameter_guid", "action_id", "document_id", "transaction",
                    "options", "command", "path", "url", "script"):
            self.assertFalse(registry.validate_arguments({"value": "A", key: "X"})["valid"])
        for value in ({}, [], ["A"], {"value": ["A", "B"]}, None):
            self.assertFalse(registry.validate_arguments(value)["valid"])

    def test_provider_code_unchanged_except_partition(self):
        path = "BIMCode_Provider/provider.py"
        baseline = subprocess.check_output(["git", "show", "b2e4c9344983251864f9f948fa8e85c4b03ec070:" + path], cwd=str(ROOT)).decode("utf-8-sig")
        current = ast.parse((ROOT / path).read_text(encoding="utf-8-sig"))
        current.body = [node for node in current.body if not (
            isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
            t.id == "READ_ONLY_TOOL_REGISTRY" for t in node.targets))]
        current.body = [node for node in current.body if not (
            isinstance(node, ast.FunctionDef) and node.name == "send_write_explanation")]
        self.assertEqual(ast.dump(current), ast.dump(ast.parse(baseline)))

    def test_pure_boundary(self):
        for name in ("write_access.py", "controlled_write_registry.py"):
            source = (ROOT / "AI.extension/lib/bimcode_ai_pane" / name).read_text()
            tree = ast.parse(source)
            calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
            forbidden = {"Set", "Transaction", "Raise", "TaskDialog", "open", "exec", "eval"}
            for call in calls:
                self.assertNotIn(getattr(call.func, "attr", getattr(call.func, "id", "")), forbidden)
