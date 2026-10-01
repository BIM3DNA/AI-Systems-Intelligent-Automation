"""M4B-8A local permission presentation and cleanup; never a write dispatcher."""
import hashlib
from bimcode_ai_pane.write_access import ControlledWritePermission, document_eligibility
from bimcode_ai_pane.ai_tool_registry import TOOLS
from bimcode_ai_pane.controlled_write_registry import metadata


def read_document(uiapp, db, guid):
    """Revit API context ONLY. Document/binding reads; no selection or preview."""
    from bimcode_ai_pane.tools import document_key
    from bimcode_ai_pane.write_contracts import M4A_TEST_PARAMETER_NAME
    from bimcode_write_runtime import verify_binding, PreviewBlocked
    facts = {}
    identity = None
    try:
        uidoc = uiapp.ActiveUIDocument
        if uidoc is None:
            facts["valid_document"] = False
            return identity, facts
        doc = uidoc.Document
        if doc is None or not doc.IsValidObject:
            facts["valid_document"] = False
            return identity, facts
        key = document_key(uiapp)
        if key is None:
            return None, {}  # Unknown identity cannot authorize anything.
        identity = hashlib.sha256(repr(key).encode("utf-8")).hexdigest()
        facts.update(valid_document=True, active_uidocument=True)
        # Read in predicate order: retain the first exact rejection even if a
        # later API property is unavailable. Never traverse linked documents.
        for field, attr, expected in (("family_document", "IsFamilyDocument", False),
                                      ("linked_document", "IsLinked", False),
                                      ("workshared", "IsWorkshared", False),
                                      ("read_only", "IsReadOnly", False),
                                      ("modifiable", "IsModifiable", False)):
            if field == "linked_document":
                facts["host_document"] = True  # Only ActiveUIDocument.Document.
            facts[field] = bool(getattr(doc, attr))
            if facts[field] != expected:
                return identity, facts
        shared = db.SharedParameterElement.Lookup(doc, guid)
        facts["fixed_parameter_available"] = shared is not None
        if shared is not None:
            try:
                facts["fixed_parameter_binding_valid"] = False
                if shared.GuidValue.Equals(guid) and shared.Name == M4A_TEST_PARAMETER_NAME:
                    verify_binding(doc, shared, db)
                    facts["fixed_parameter_binding_valid"] = True
            except PreviewBlocked:
                pass
            except Exception:
                facts.pop("fixed_parameter_binding_valid", None)
    except Exception:
        pass  # Missing evidence is DOCUMENT_FACTS_UNREADABLE, never eligible.
    return identity, facts


class SessionWriteGate(object):
    """UI-thread state, one existing permission instance; no environment/disk IO.

    lifecycle/request are an optional host-owned M4B-7 cleanup slot. No request
    is created here or by provider dispatch in this checkpoint. A retained
    lifecycle owns its immutable receipt and unresolved-safety evidence.
    """
    def __init__(self, admission):
        self.permission = ControlledWritePermission()
        self.admission = admission
        self.document = None
        self.facts = dict(valid_document=False)
        self.lifecycle = None
        self.request = None
        self.last_cleanup = None
        self.cleanup_generation = 0
        self.enable_pending = None
        self.closed = False
        self.confirmation_active = False
        self.note = ""

    def observe(self, identity, facts):
        if self.closed:
            return
        if identity != self.document:
            self.cleanup("DOCUMENT_SWITCH")
        self.document, self.facts = identity, dict(facts)
        if not document_eligibility(facts)["eligible"] and self.permission.view_model()["enabled"]:
            self.cleanup("ABANDONED")

    def queue_enable(self):
        if self.closed or self.enable_pending is not None or self.permission.view_model()["enabled"]:
            return False
        self.enable_pending = (self.document, self.cleanup_generation)
        self.note = "Enable queued; awaiting local confirmation"
        return True

    def enable(self, ticket, confirmed):
        # Rechecked after the native dialog: switch/close/hide/Disable wins.
        if (self.closed or ticket != (self.document, self.cleanup_generation)
                or self.admission.active is not None or self.admission.safety_locked
                or (self.admission.busy is not None and self.admission.busy())):
            self.note = "ENABLE_INVALIDATED_OR_BUSY"
            return False
        ok = self.permission.enable_from_human(self.document, self.facts, confirmed)
        self.note = "" if ok else ("ENABLE_CANCELLED" if not confirmed else
                                    document_eligibility(self.facts)["reason_code"])
        return ok

    def cleanup(self, reason):
        self.enable_pending = None
        # Existing foundation validates correlation, consumes leases/callbacks,
        # suppresses continuation, and preserves actual receipts/executing locks.
        changed = False
        if self.lifecycle is not None:
            try:
                result = self.lifecycle.cleanup(reason, self.request)
                changed = result is not self.last_cleanup
                self.last_cleanup = result
                if result.owner_released:
                    self.lifecycle = None
                    self.request = None
            except Exception:
                # Corrupt/missing host evidence must never release an owner.
                self.admission.safety_locked = True
                self.lifecycle.leases.invalidate(reason)
                self.lifecycle.sink.cleanup()
                if self.lifecycle.continuation is not None:
                    self.lifecycle.continuation.close("cancelled")
                self.note = "CLEANUP_EVIDENCE_INVALID"
        if self.permission.view_model()["enabled"]:
            self.permission.disable()
            changed = True
        # A generation also invalidates a dialog in progress while permission
        # is still off. Duplicate cleanup with no intent has no further effect.
        if changed or self.confirmation_active:
            self.cleanup_generation += 1
        if reason in ("DOCUMENT_CLOSE", "PANE_DISPOSAL", "SHUTDOWN"):
            self.document, self.facts = None, dict(valid_document=False)

    def view_model(self):
        state = self.permission.view_model()
        eligibility = document_eligibility(self.facts)
        leases = self.lifecycle.leases if self.lifecycle is not None else None
        owner = self.admission.active
        return dict(status=state["status"], dispatch_status=state["dispatch_status"],
            eligibility_text="Eligible: {0} ({1})".format(
                "YES" if eligibility["eligible"] else "NO", eligibility["reason_code"]),
            controlled_write_permission_enabled=state["enabled"],
            controlled_write_permission_scope="CURRENT_DOCUMENT / SESSION_ONLY" if state["enabled"] else "NONE",
            controlled_write_document_eligible=eligibility["eligible"],
            controlled_write_eligibility_reason=eligibility["reason_code"],
            controlled_write_provider_exposed=False, controlled_write_dispatch_available=False,
            active_provider_tool_count=len(TOOLS), controlled_write_metadata_count=len(metadata()),
            preview_lease_active=leases is not None and leases.preview.state == "ACTIVE",
            execution_queue_lease_active=leases is not None and leases.queue.state == "ACTIVE",
            current_owner=owner.owner_type if owner is not None else "NONE",
            retained_safety_lock=self.admission.safety_locked,
            cleanup_generation=self.cleanup_generation, note=self.note,
            enable_available=not self.closed and not state["enabled"] and self.enable_pending is None,
            disable_available=not self.closed)
