"""Explicit human-only disposable-fixture setup; never imported by BIMCode AI.

Select one eligible Pipe before invoking. Creates a NEW dedicated shared-parameter
file at a user-selected path; never overwrites an existing file. No value writes.
"""
from bimcode_ai_pane import write_contracts as contract
from bimcode_write_runtime import resolve_target, verify_binding, resolve_parameter


def inspect_existing(doc, db, guid):
    """Reject conflicts rather than repair, rebind or broaden categories."""
    shared = db.SharedParameterElement.Lookup(doc, guid)
    for item in db.FilteredElementCollector(doc).OfClass(db.ParameterElement):
        if item.Name == contract.M4A_TEST_PARAMETER_NAME:
            if not isinstance(item, db.SharedParameterElement) or not item.GuidValue.Equals(guid):
                raise ValueError("Conflicting parameter name; setup stopped.")
    if shared is not None:
        if shared.Name != contract.M4A_TEST_PARAMETER_NAME:
            raise ValueError("Fixed GUID has an incompatible name; setup stopped.")
        verify_binding(doc, shared, db)
    return shared


def provision(uiapp, path, db, guid, io):
    """Only this human setup utility owns a binding transaction."""
    doc, uidoc, pipe = resolve_target(uiapp, db)
    if inspect_existing(doc, db, guid) is not None:
        resolve_parameter(doc, pipe, db, guid)
        return "ALREADY_PROVISIONED"
    # Exclusive creation protects office master/unknown existing files, even races.
    stream = io.FileStream(path, io.FileMode.CreateNew, io.FileAccess.Write)
    writer = io.StreamWriter(stream)
    try:
        writer.WriteLine("# This is a Revit shared parameter file.")
        writer.WriteLine("*META\tVERSION\tMINVERSION")
        writer.WriteLine("META\t2\t1")
        writer.WriteLine("*GROUP\tID\tNAME")
        writer.WriteLine("*PARAM\tGUID\tNAME\tDATATYPE\tDATACATEGORY\tGROUP\tVISIBLE\tDESCRIPTION\tUSERMODIFIABLE\tHIDEWHENNOVALUE")
    finally:
        writer.Dispose()
    app = uiapp.Application
    original = app.SharedParametersFilename
    try:
        app.SharedParametersFilename = path
        shared_file = app.OpenSharedParameterFile()
        if shared_file is None:
            raise ValueError("Dedicated shared parameter file could not be opened.")
        group = shared_file.Groups.Create("BIMCode M4A disposable fixture")
        options = db.ExternalDefinitionCreationOptions(contract.M4A_TEST_PARAMETER_NAME,
                                                       db.SpecTypeId.String.Text)
        options.GUID = guid
        definition = group.Definitions.Create(options)
        if not definition.GUID.Equals(guid):
            raise ValueError("Definition GUID verification failed.")
        categories = app.Create.NewCategorySet()
        categories.Insert(doc.Settings.Categories.get_Item(db.BuiltInCategory.OST_PipeCurves))
        binding = app.Create.NewInstanceBinding(categories)
        tx = db.Transaction(doc, "BIMCode M4A fixture parameter binding")
        try:
            if tx.Start() != db.TransactionStatus.Started:
                raise ValueError("Binding transaction did not start.")
            options = tx.GetFailureHandlingOptions()
            options.SetForcedModalHandling(True)
            tx.SetFailureHandlingOptions(options)
            if not doc.ParameterBindings.Insert(definition, binding, db.GroupTypeId.Data):
                raise ValueError("Binding insertion rejected; no repair attempted.")
            # Verify while rollback is still possible, then again after commit.
            inspect_existing(doc, db, guid)
            resolve_parameter(doc, pipe, db, guid)
            status = tx.Commit()
            if status != db.TransactionStatus.Committed:
                raise ValueError("Binding transaction not committed: " + str(status))
        finally:
            status = tx.GetStatus()
            if status == db.TransactionStatus.Started:
                if tx.RollBack() != db.TransactionStatus.RolledBack:
                    raise ValueError("Binding rollback not confirmed; inspect fixture manually.")
            if status != db.TransactionStatus.Pending:
                tx.Dispose()
        inspect_existing(doc, db, guid)
        resolve_parameter(doc, pipe, db, guid)
        return "PROVISIONED / selected Pipe GUID, binding, Text storage and writability verified"
    finally:
        app.SharedParametersFilename = original


def main():
    from pyrevit import HOST_APP, forms
    from Autodesk.Revit import DB
    from System import Guid, IO
    uiapp = HOST_APP.uiapp
    try:
        doc, uidoc, pipe = resolve_target(uiapp, DB)
        guid = Guid(contract.M4A_TEST_PARAMETER_GUID)
        if inspect_existing(doc, DB, guid) is not None:
            resolve_parameter(doc, pipe, DB, guid)
            print("ALREADY_PROVISIONED; no transaction or file created.")
            return
        consent = forms.ask_for_string(
            prompt="Disposable project only: {0}\nCreate shared instance Text parameter {1}\nGUID {2}\nPipes only. No values will be set.\nType PROVISION to continue.".format(
                doc.Title, contract.M4A_TEST_PARAMETER_NAME, contract.M4A_TEST_PARAMETER_GUID),
            title="M4A fixture setup")
        if consent != "PROVISION":
            return
        path = forms.save_file(file_ext="txt", default_name="BIMCode_M4A_fixture_shared_parameters.txt",
                               title="Choose a NEW dedicated file; existing files are rejected")
        if path:
            print(provision(uiapp, path, DB, guid, IO))
            print("Save/inspect the disposable fixture manually. Dedicated file: " + path)
    except Exception as error:
        print("SETUP STOPPED: {0}. Binding may have committed if a post-commit read failed. Inspect fixture and dedicated file manually; no automatic retry.".format(error))


if __name__ == "__main__":
    main()
