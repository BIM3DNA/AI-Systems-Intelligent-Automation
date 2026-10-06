"""Human-only confirmation and dedicated write event; no provider entry point."""
import json
from uuid import uuid4
from xml.sax.saxutils import escape

from pyrevit import DB, UI, framework
from bimcode_ai_pane import write_contracts as c
from bimcode_write_execution import Executor, freeze, result_for
from bimcode_write_runtime import capture_preview_context, build_preview
from bimcode_ai_pane.write_access import admission_for, owner_document_key
from bimcode_ai_pane.write_completion import CompletionSink
from bimcode_ai_pane import write_diagnostic as diag


def clock():
    from System.Diagnostics import Stopwatch
    return float(Stopwatch.GetTimestamp()) / Stopwatch.Frequency


def display(output, result, diagnostic=None):
    diag.record(diagnostic, "DEV_OUTPUT_ATTEMPT", result)
    try:
        output.print_html("<pre>" + escape(json.dumps(result, indent=2, sort_keys=True)) + "</pre>")
    except Exception as error:
        diag.exception(diagnostic, "dev_output", error)
        diag.record(diagnostic, "DEV_OUTPUT_RESULT", result, success=False)
        raise
    diag.record(diagnostic, "DEV_OUTPUT_RESULT", result, success=True)


def confirm(preview):
    dialog = UI.TaskDialog("BIMCode M4A Controlled Write")
    dialog.TitleAutoPrefix = False
    dialog.MainInstruction = "This will modify the Revit model in one transaction."
    dialog.MainContent = (
        "Document: {0}\nView: {1}\nTarget: Pipe {2}\nPipe type: {3}\n"
        "Parameter: {4}\nGUID: {5}\nBefore: {6}\nAfter: {7}\nRequest: {8}").format(
            preview["document_identity"]["title"], preview["view_identity"]["unique_id"],
            preview["target_element_id"], json.dumps(preview["pipe_type"], sort_keys=True),
            c.M4A_TEST_PARAMETER_NAME, c.M4A_TEST_PARAMETER_GUID,
            json.dumps(preview["current_value"], ensure_ascii=True),
            json.dumps(preview["proposed_value"], ensure_ascii=True), preview["request_id"])
    dialog.AddCommandLink(UI.TaskDialogCommandLinkId.CommandLink1, "Confirm this one parameter write")
    dialog.CommonButtons = UI.TaskDialogCommonButtons.Cancel
    dialog.DefaultButton = UI.TaskDialogResult.Cancel
    dialog.AllowCancellation = True
    return dialog.Show() == UI.TaskDialogResult.CommandLink1


class WriteHandler(UI.IExternalEventHandler):
    def __init__(self, owner):
        self.owner = owner

    def GetName(self):
        return "BIMCode M4A human-confirmed parameter write"

    def Execute(self, uiapp):
        diag.state(self.owner, "HANDLER_ENTERED")
        try:
            self.owner.execute(uiapp)
        finally:
            diag.state(self.owner, "HANDLER_EXITED")


class WriteCoordinator(object):
    # Also safe for an existing retained controller without a diagnostic session.
    diagnostic = None

    def __init__(self, session):
        self.session = session
        self.pending = None
        self.output = None
        self.epoch = 0
        self.executor = Executor()
        self.handler = WriteHandler(self)
        self.event = UI.ExternalEvent.Create(self.handler)
        self.resolving = False
        self.running = False
        self.delegate = None
        self.admission = admission_for(session)
        self.owner = None
        self.completion_sink = None
        self.delivering = False
        self.diagnostic = None
        try:
            # Use the existing retained subscription list; no parallel lifecycle service.
            self.delegate = framework.EventHandler[DB.Events.DocumentChangedEventArgs](self.on_model_changed)
            session.uiapp.Application.DocumentChanged.__iadd__(self.delegate)
            session._subscriptions.append((session.uiapp.Application, "DocumentChanged", self.delegate))
        except Exception:
            self.event.Dispose()
            raise

    def on_model_changed(self, sender, args):
        # Conservative all-document invalidation, including commit/Undo/Redo/ABA.
        # No API traversal, writes, scheduling, or cancellation of executing work.
        self.epoch += 1

    def epochs(self):
        return (self.session.context_generation, self.session.selection_generation, self.epoch)

    def invoke(self, uiapp, forms, output, completion_callback=None):
        command_trace = diag.host_trace() if completion_callback is None else None
        diag.record(command_trace, "COMMAND_INVOKED")
        if completion_callback is not None and not callable(completion_callback):
            raise ValueError("INVALID_CALLBACK")
        session = self.session
        if self.running or self.pending is not None or self.resolving or self.delivering:
            diag.record(command_trace, "INVOCATION_REJECTED", reason_code="EXECUTION_BUSY")
            display(output, result_for({}, "NOT_READY", "EXECUTION_BUSY"), command_trace)
            return
        if self.executor.retained is not None:
            # A repeated HUMAN command is a status query, not a second write.
            self.output = output
            self.resolving = True
            try:
                diag.state(self, "EXTERNAL_EVENT_RAISE_ATTEMPT")
                raised = self.event.Raise()
                diag.raised(self.diagnostic, raised)
                if raised != UI.ExternalEventRequest.Accepted:
                    self.resolving = False
                    display(output, result_for({}, "NOT_READY", "EXECUTION_BUSY"), self.diagnostic)
                else:
                    diag.state(self, "PUSHBUTTON_RETURN_AFTER_ACCEPTED")
            except Exception as error:
                diag.exception(self.diagnostic, "resolution_raise", error)
                self.resolving = False
                display(output, result_for({}, "INDETERMINATE", "TRANSACTION_STATUS_UNKNOWN"), self.diagnostic)
            return
        if (getattr(session, "write_busy", False) or session.tools.pending is not None or
                session.ai.turn is not None):
            diag.record(command_trace, "INVOCATION_REJECTED", reason_code="EXECUTION_BUSY")
            display(output, result_for({}, "NOT_READY", "EXECUTION_BUSY"), command_trace)
            return
        request_id = uuid4().hex
        self.diagnostic = command_trace
        diag.bind(self.diagnostic, request_id)
        self.owner = self.admission.acquire("HUMAN_DEV_WRITE", request_id, request_id,
            owner_document_key(session), str(id(session)), clock())
        if self.owner is None:
            diag.record(self.diagnostic, "OWNER_REJECTED", reason_code="EXECUTION_BUSY")
            display(output, result_for({}, "NOT_READY", "EXECUTION_BUSY"), self.diagnostic)
            return
        diag.record(self.diagnostic, "OWNER_ACQUIRED")
        self.completion_sink = CompletionSink(self.owner, completion_callback)
        session.write_busy = True
        self.output = output
        preview = {}
        try:
            stamp = clock()
            epochs = self.epochs()
            context = capture_preview_context(uiapp)
            value = forms.ask_for_string(default="M4A_Write_01", title="M4A Write - proposed value",
                                         prompt="One test parameter only. A separate confirmation is required.")
            if value is None:
                self.emit(output, result_for(preview, "CANCELLED", "USER_CANCELLED"))
                return
            preview = build_preview(uiapp, request_id, value, epochs[1], context)
            diag.record(self.diagnostic, "PREVIEW_CREATED", preview)
            display(output, preview, self.diagnostic)
            if preview["classification"] != c.PREVIEW_OK or preview["reason_code"] != "COMPLETE":
                self.complete(preview)
                return
            if self.epochs() != epochs or clock() - stamp > 60:
                diag.record(self.diagnostic, "APPROVAL_REJECTED", reason_code="STALE_CONTEXT")
                self.emit(output, result_for(preview, "NOT_READY", "STALE_CONTEXT"))
                return
            diag.record(self.diagnostic, "CONFIRM_DIALOG_ATTEMPT", preview)
            confirmation = confirm(preview)
            # Show returned; construction/Show exceptions must not claim a shown dialog.
            diag.record(self.diagnostic, "CONFIRM_DIALOG_SHOWN", preview)
            if not confirmation:
                diag.record(self.diagnostic, "CONFIRM_REJECTED", reason_code="USER_CANCELLED")
                self.emit(output, result_for(preview, "CANCELLED", "USER_CANCELLED"))
                return
            confirmed = clock()
            diag.record(self.diagnostic, "CONFIRM_ACCEPTED", elapsed_seconds=confirmed - stamp)
            if self.epochs() != epochs or confirmed - stamp > 60:
                diag.record(self.diagnostic, "APPROVAL_REJECTED",
                            reason_code="CONFIRMATION_EXPIRED" if confirmed - stamp > 60 else "STALE_CONTEXT")
                self.emit(output, result_for(preview, "NOT_READY", "CONFIRMATION_EXPIRED" if confirmed - stamp > 60 else "STALE_CONTEXT"))
                return
            diag.record(self.diagnostic, "POST_CONFIRM_CONTEXT_VALID", elapsed_seconds=confirmed - stamp)
            self.pending = freeze(preview, epochs, stamp, confirmed)
            diag.state(self, "APPROVAL_REGISTERED")
            diag.state(self, "EXTERNAL_EVENT_RAISE_ATTEMPT")
            raised = self.event.Raise()
            diag.raised(self.diagnostic, raised)
            if raised != UI.ExternalEventRequest.Accepted:
                self.pending = None
                self.emit(output, result_for(preview, "FAILED", "EXTERNAL_EVENT_NOT_ACCEPTED"))
            else:
                diag.state(self, "PUSHBUTTON_RETURN_AFTER_ACCEPTED")
        except Exception as error:
            diag.exception(self.diagnostic, "invoke", error)
            self.pending = None
            self.emit(output, result_for(preview, "FAILED", "CONFIRMATION_FAILED"))
        finally:
            if self.pending is None:
                session.write_busy = False

    def emit(self, output, result):
        self.complete(result)
        display(output, result, self.diagnostic)

    def complete(self, result):
        sink, owner = self.completion_sink, self.owner
        if sink is None or sink.receipt is not None:
            diag.record(self.diagnostic, "COMPLETION_SKIPPED",
                        reason_code="NO_SINK" if sink is None else "RECEIPT_ALREADY_STORED")
            return
        try:
            sink.store(result)
            diag.record(self.diagnostic, "COMPLETION_CREATED", result)
        except Exception as error:
            diag.exception(self.diagnostic, "completion_store", error)
            sink.error = "COMPLETION_CONTRACT_FAILED"
            self.admission.safety_locked = (self.executor.retained is not None or
                result.get("classification") == "MEP_PARAMETER_WRITE_INDETERMINATE")
            released = self.admission.release(owner, "COMPLETION_CONTRACT_FAILED")
            diag.record(self.diagnostic, "OWNER_RELEASED", released=released, reason_code="COMPLETION_CONTRACT_FAILED")
            return
        self.admission.safety_locked = (self.executor.retained is not None or
                                        result.get("classification") == "MEP_PARAMETER_WRITE_INDETERMINATE")
        def deliver():
            self.delivering = True
            try:
                diag.record(self.diagnostic, "COMPLETION_CALLBACK_STATE", callback_present=sink.callback is not None)
                delivered = sink.deliver(owner.logical_request_id)
                diag.record(self.diagnostic, "COMPLETION_DELIVERED", delivered=delivered,
                            success=delivered and sink.error is None, error=sink.error)
            finally:
                self.delivering = False
                released = self.admission.release(owner, "HOST_RESULT_READY")
                diag.record(self.diagnostic, "OWNER_RELEASED", released=released, reason_code="HOST_RESULT_READY")
        if sink.callback is None:
            deliver()
        else:
            try:
                # Deferred WPF callback: no Revit API context/objects provided.
                from System import Action
                self.session.panel.Dispatcher.BeginInvoke(Action(deliver))
            except Exception as error:
                diag.exception(self.diagnostic, "callback_dispatch", error)
                sink.error = "CALLBACK_DISPATCH_FAILED"
                sink.cleanup()
                released = self.admission.release(owner, "CALLBACK_DISPATCH_FAILED")
                diag.record(self.diagnostic, "OWNER_RELEASED", released=released, reason_code="CALLBACK_DISPATCH_FAILED")

    def cleanup(self, reason):
        diag.state(self, "COORDINATOR_CLEANUP", reason_code=reason)
        if reason not in ("DOCUMENT_CLOSE", "DOCUMENT_SWITCH", "PANE_DISPOSAL", "SHUTDOWN", "ABANDONED"):
            raise ValueError("INVALID_CLEANUP_REASON")
        if self.completion_sink is not None:
            self.completion_sink.cleanup()
        self.pending = None
        self.admission.cleanup(self.owner, reason, self.running, self.executor.retained is not None)
        if not self.running and self.executor.retained is None:
            self.session.write_busy = False

    def execute(self, uiapp):
        diag.state(self, "HANDLER_RUNNING_STATE")
        diag.state(self, "HANDLER_PENDING_STATE")
        if self.running:
            diag.state(self, "HANDLER_REJECTED", reason_code="ALREADY_RUNNING")
            return
        request = self.pending
        resolving = self.resolving
        self.pending = None  # Consume before any API evaluation; callback replay is inert.
        self.resolving = False
        if request is not None:
            diag.state(self, "PENDING_REQUEST_CONSUMED")
        if request is None and not resolving:
            diag.state(self, "HANDLER_REJECTED", reason_code="NO_PENDING_REQUEST")
            return
        self.running = True
        try:
            guid = framework.Guid.Parse(c.M4A_TEST_PARAMETER_GUID)
            if resolving:
                result = self.executor.check_pending(DB, guid)
            else:
                self.executor.diagnostic = self.diagnostic
                result = self.executor.execute(request, uiapp, self.epochs(), clock(), DB, guid)
            self.emit(self.output, result)
            if resolving and self.executor.retained is None:
                self.admission.resolve_safety(True)
        except Exception as error:
            diag.exception(self.diagnostic, "handler", error)
            preview = json.loads(request.preview_json) if request is not None else {}
            result = result_for(preview, "INDETERMINATE", "INTERNAL_ERROR")
            result["model_modified"] = None
            self.emit(self.output, result)
        finally:
            self.running = False
            self.session.write_busy = self.executor.retained is not None


def get_coordinator(session):
    """One event/controller per existing pane session; fail closed without epochs."""
    names = {name for source, name, delegate in session._subscriptions}
    if not {"SelectionChanged", "ViewActivated", "DocumentClosed", "DocumentOpened", "DocumentCreated"}.issubset(names):
        raise RuntimeError("Required lifecycle/selection subscriptions unavailable; restart Revit")
    owner = getattr(session, "m4a_write", None)
    if owner is None:
        owner = WriteCoordinator(session)
        session.m4a_write = owner
    return owner
