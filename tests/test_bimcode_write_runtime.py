"""Offline fake-API safety evidence, not live Revit validation."""
import ast
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "AI.extension/lib"))
import bimcode_write_runtime as runtime
from bimcode_ai_pane import write_contracts as c


class Identity:
    def __init__(self, value):
        self.Value = value

    def Equals(self, other):
        return isinstance(other, Identity) and self.Value == other.Value


class Pipe:
    pass


class Binding:
    pass


def fixture():
    guid = Identity(c.M4A_TEST_PARAMETER_GUID)
    text = Identity("text")
    definition = N(GetDataType=lambda: text)
    binding = Binding()
    binding.Categories = [N(Id=Identity(-2008044))]
    doc = N(IsValidObject=True, IsFamilyDocument=False, IsWorkshared=False,
            IsReadOnly=False, IsModifiable=False, Title="Fixture", GetHashCode=lambda: 123)
    doc.Equals = lambda other: doc is other
    pipe = Pipe()
    pipe.__dict__.update(Document=doc, IsValidObject=True, Category=binding.Categories[0],
                         IsPlaceholder=False, Pinned=False, GroupId=Identity(-1),
                         AssemblyInstanceId=Identity(-1), DesignOption=None, Id=Identity(1),
                         UniqueId="pipe-1", GetTypeId=lambda: Identity(2))
    parameter = N(IsShared=True, GUID=guid, Element=pipe, StorageType="String",
                  Definition=definition, IsReadOnly=False, AsString=lambda: None, HasValue=False)
    pipe.get_Parameter = lambda requested: parameter if requested.Equals(guid) else None
    doc.GetElement = lambda eid: pipe if eid.Value == 1 else N(UniqueId="type-2")
    doc.ParameterBindings = N(get_Item=lambda d: binding)
    shared = N(GuidValue=guid, Name=c.M4A_TEST_PARAMETER_NAME, GetDefinition=lambda: definition)
    db = N(Plumbing=N(Pipe=Pipe), ElementType=type("ElementType", (), {}),
           BuiltInCategory=N(OST_PipeCurves=-2008044), InstanceBinding=Binding,
           SpecTypeId=N(String=N(Text=text)), StorageType=N(String="String"),
           SharedParameterElement=N(Lookup=lambda d, g: shared))
    uidoc = N(Document=doc, Selection=N(GetElementIds=lambda: [Identity(1)]),
              ActiveView=N(IsValidObject=True, Id=Identity(3), UniqueId="view-3"))
    return N(app=N(ActiveUIDocument=uidoc), doc=doc, pipe=pipe, parameter=parameter,
             binding=binding, shared=shared, db=db, guid=guid, uidoc=uidoc)


class Preview(unittest.TestCase):
    def setUp(self):
        self.f = fixture()

    def run_preview(self, value="Test 1"):
        f = self.f
        return runtime._preview(f.app, "request-1", value, 5, f.db, f.guid)

    def reason(self, expected):
        result = self.run_preview()
        self.assertEqual(result["reason_code"], expected)
        self.assertEqual(result["classification"], c.PREVIEW_NOT_READY)
        self.assertFalse(result["transaction_started"])
        self.assertFalse(result["model_modified"])

    def test_good(self):
        result = self.run_preview()
        self.assertEqual(result["classification"], c.PREVIEW_OK)
        self.assertEqual(result["target_element_id"], 1)
        self.assertEqual(result["binding_kind"], "INSTANCE")
        self.assertIsNone(result["current_value"])
        self.assertTrue(result["confirmation_required"])
        self.assertFalse(result["model_modified"])
        self.assertFalse(result["transaction_started"])

    def test_empty(self):
        self.f.uidoc.Selection.GetElementIds = lambda: []
        self.reason("NO_ELEMENTS_SELECTED")

    def test_consecutive_invocations_never_reuse_target(self):
        selection = Mock(return_value=[Identity(1)])
        self.f.uidoc.Selection.GetElementIds = selection
        first = self.run_preview()
        self.assertEqual(first["classification"], c.PREVIEW_OK)
        for ids, reason in (([], "NO_ELEMENTS_SELECTED"),
                            ([Identity(1), Identity(2)], "MULTIPLE_ELEMENTS_SELECTED")):
            selection.return_value = ids
            result = self.run_preview()
            self.assertEqual(result["reason_code"], reason)
            self.assertIsNone(result["target_element_id"])
            self.assertIsNone(result["target_unique_id"])
            self.assertNotEqual(result["selection_fingerprint"], first["selection_fingerprint"])
            self.assertFalse(result["transaction_started"])
            self.assertFalse(result["model_modified"])
        self.assertEqual(selection.call_count, 3)

    def test_explicit_empty_snapshot_not_replaced_by_later_selection(self):
        selection = Mock(return_value=[])
        self.f.uidoc.Selection.GetElementIds = selection
        context = runtime.capture_preview_context(self.f.app)
        selection.return_value = [Identity(1)]
        f = self.f
        result = runtime._preview(f.app, "request", "Test", None, f.db, f.guid, context)
        self.assertEqual(result["reason_code"], "NO_ELEMENTS_SELECTED")
        self.assertEqual(result["selection_snapshot"]["selected_element_ids"], [])
        selection.assert_called_once()

    def test_fingerprint_deterministic_and_context_sensitive(self):
        first = runtime.capture_preview_context(self.f.app)
        self.assertEqual(first["fingerprint"], runtime.capture_preview_context(self.f.app)["fingerprint"])
        self.f.uidoc.ActiveView.UniqueId = "other-view"
        self.assertNotEqual(first["fingerprint"], runtime.capture_preview_context(self.f.app)["fingerprint"])

    def test_multiple(self):
        self.f.uidoc.Selection.GetElementIds = lambda: [Identity(1), Identity(2)]
        self.reason("MULTIPLE_ELEMENTS_SELECTED")

    def test_target_exclusions(self):
        for key, value in (("IsPlaceholder", True), ("Pinned", True), ("GroupId", Identity(4)),
                           ("AssemblyInstanceId", Identity(4)), ("DesignOption", object()),
                           ("Category", N(Id=Identity(9))), ("Document", Identity("linked"))):
            self.f = fixture()
            setattr(self.f.pipe, key, value)
            self.reason("UNSUPPORTED_TARGET")

    def test_wrong_class(self):
        self.f.db.Plumbing.Pipe = type("Other", (), {})
        self.reason("UNSUPPORTED_TARGET")

    def test_documents(self):
        for key in ("IsFamilyDocument", "IsWorkshared", "IsReadOnly", "IsModifiable"):
            self.f = fixture()
            setattr(self.f.doc, key, True)
            self.reason("UNSUPPORTED_DOCUMENT")
        self.f = fixture()
        self.f.app.ActiveUIDocument = None
        self.reason("NO_VALID_DOCUMENT")

    def test_missing(self):
        self.f.pipe.get_Parameter = lambda g: None
        self.reason("PARAMETER_MISSING")

    def test_shared_missing(self):
        self.f.db.SharedParameterElement.Lookup = lambda d, g: None
        self.reason("PARAMETER_MISSING")

    def test_read_only(self):
        self.f.parameter.IsReadOnly = True
        self.reason("TARGET_NOT_WRITABLE")

    def test_storage(self):
        self.f.parameter.StorageType = "Integer"
        self.reason("STORAGE_TYPE_UNSUPPORTED")

    def test_data_type(self):
        self.f.parameter.Definition.GetDataType = lambda: Identity("number")
        self.reason("DATA_TYPE_UNSUPPORTED")

    def test_identity(self):
        self.f.parameter.GUID = Identity("wrong")
        self.reason("PARAMETER_IDENTITY_MISMATCH")

    def test_binding(self):
        self.f.binding.Categories.append(N(Id=Identity(8)))
        self.reason("INVALID_BINDING")
        self.f.doc.ParameterBindings.get_Item = lambda d: object()
        self.reason("INVALID_BINDING")

    def test_empty_and_noop(self):
        self.f.parameter.AsString = lambda: ""
        self.assertEqual(self.run_preview()["current_display"], "(empty)")
        self.f.parameter.AsString = lambda: "Test 1"
        self.reason("NO_CHANGE_REQUIRED")

    def test_unsafe_current(self):
        for value in ("a" * 257, "a\n", "a\u202e"):
            self.f.parameter.AsString = lambda: value
            self.reason("CURRENT_VALUE_UNSAFE")

    def test_read_exception(self):
        def broken():
            raise RuntimeError("unreadable")
        self.f.parameter.AsString = broken
        result = self.run_preview()
        self.assertEqual(result["classification"], c.PREVIEW_FAILED)
        self.assertEqual(result["reason_code"], "READ_FAILED")

    def test_invalid_before_api(self):
        self.f.app = None
        self.assertEqual(self.run_preview(" bad")["reason_code"], "INVALID_VALUE")

    def test_preview_has_no_mutation_or_name_lookup(self):
        for path in (ROOT / "AI.extension/lib/bimcode_write_runtime.py",
                     ROOT / "AI.extension/lib/bimcode_ai_pane/write_contracts.py"):
            tree = ast.parse(path.read_text())
            names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
            self.assertFalse(names & {"Transaction", "Set", "LookupParameter", "SetElementIds",
                                      "Raise", "Create", "WriteAllText"})


class Provisioning(unittest.TestCase):
    def setUp(self):
        path = ROOT / "AI.extension/AI.tab/Dev.panel/M4ASetup.pushbutton/script.py"
        spec = importlib.util.spec_from_file_location("m4a_setup_test", path)
        self.setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.setup)

    def test_existing_definition_conflicts(self):
        f = fixture()
        class Shared:
            pass
        shared = Shared()
        shared.Name = c.M4A_TEST_PARAMETER_NAME
        shared.GuidValue = f.guid
        shared.GetDefinition = f.shared.GetDefinition
        Shared.Lookup = staticmethod(lambda d, g: shared)
        f.db.SharedParameterElement = Shared
        f.db.ParameterElement = object
        items = [shared]
        f.db.FilteredElementCollector = lambda d: N(OfClass=lambda cls: items)
        self.assertIs(self.setup.inspect_existing(f.doc, f.db, f.guid), shared)
        shared.Name = "Wrong name"
        with self.assertRaises(ValueError):
            self.setup.inspect_existing(f.doc, f.db, f.guid)
        shared.Name = c.M4A_TEST_PARAMETER_NAME
        items.append(N(Name=c.M4A_TEST_PARAMETER_NAME))
        with self.assertRaises(ValueError):
            self.setup.inspect_existing(f.doc, f.db, f.guid)

    def test_already_provisioned_has_no_file_or_transaction(self):
        f = fixture()
        self.setup.inspect_existing = lambda d, db, g: f.shared
        # No IO/Transaction API supplied: any attempt would fail.
        self.assertEqual(self.setup.provision(f.app, None, f.db, f.guid, None),
                         "ALREADY_PROVISIONED")

    def test_binding_transaction_and_restore(self):
        for outcome in ("Committed", "RolledBack", "insert_false", "read_failure"):
            f = fixture()
            app = Mock(SharedParametersFilename="office-master.txt")
            f.app.Application = app
            app.OpenSharedParameterFile.return_value.Groups.Create.return_value.Definitions.Create.return_value = N(GUID=f.guid)
            f.db.ExternalDefinitionCreationOptions = Mock(return_value=N())
            f.db.GroupTypeId = N(Data="data")
            f.db.TransactionStatus = N(Started="Started", Committed="Committed",
                                      RolledBack="RolledBack", Pending="Pending")
            f.doc.Settings = Mock()
            f.doc.ParameterBindings = Mock()
            f.doc.ParameterBindings.Insert.return_value = outcome != "insert_false"
            tx = Mock()
            tx.Start.return_value = "Started"
            tx.GetStatus.return_value = "Started"
            def commit():
                tx.GetStatus.return_value = outcome
                return outcome
            tx.Commit.side_effect = commit
            tx.RollBack.return_value = "RolledBack"
            f.db.Transaction = Mock(return_value=tx)
            self.setup.inspect_existing = Mock(return_value=None)
            self.setup.resolve_parameter = Mock()
            if outcome == "read_failure":
                self.setup.resolve_parameter.side_effect = RuntimeError("read failed")
            io = Mock()
            if outcome == "Committed":
                self.assertTrue(self.setup.provision(f.app, "new.txt", f.db, f.guid, io).startswith("PROVISIONED"))
                tx.Commit.assert_called_once()
                tx.RollBack.assert_not_called()
            else:
                with self.assertRaises((ValueError, RuntimeError)):
                    self.setup.provision(f.app, "new.txt", f.db, f.guid, io)
                if outcome in ("insert_false", "read_failure"):
                    tx.RollBack.assert_called_once()
                    tx.Commit.assert_not_called()
            self.assertEqual(app.SharedParametersFilename, "office-master.txt")
            tx.Dispose.assert_called_once()

    def test_readonly_registry_unchanged(self):
        from bimcode_ai_pane.ai_tool_registry import TOOLS
        self.assertEqual(len(TOOLS), 13)
        self.assertNotIn("set_selected_pipe_test_text", [item[0] for item in TOOLS])

    def test_isolated_setup(self):
        path = ROOT / "AI.extension/AI.tab/Dev.panel/M4ASetup.pushbutton/script.py"
        source = path.read_text()
        tree = ast.parse(source)
        self.assertNotIn(".Set(", source)
        self.assertNotIn("ReInsert", source)
        self.assertEqual(source.count("db.Transaction("), 1)
        self.assertIn("io.FileMode.CreateNew", source)
        self.assertIn("app.SharedParametersFilename = original", source)
        self.assertIn("options.GUID = guid", source)
        self.assertIn('if __name__ == "__main__":', source)
        self.assertTrue(tree)
