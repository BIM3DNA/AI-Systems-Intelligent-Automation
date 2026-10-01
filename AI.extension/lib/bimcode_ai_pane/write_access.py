"""M4B-0 pure permission/view model. Not wired to pane or provider execution.

Facts must eventually be captured by a host API adapter; unknown facts fail closed.
No API, environment, persistence, target selection, or execution dependencies.
"""
from bimcode_ai_pane.write_contracts import string_types


def document_eligibility(facts):
    """Evaluate explicit scalar host facts, never infer missing evidence as safe."""
    if type(facts) is not dict:
        return dict(eligible=False, reason_code="NO_VALID_DOCUMENT")
    checks = (
        ("valid_document", True, "NO_VALID_DOCUMENT"),
        ("active_uidocument", True, "NO_ACTIVE_UIDOCUMENT"),
        ("family_document", False, "FAMILY_DOCUMENT"),
        ("host_document", True, "NON_HOST_CONTEXT"),
        ("linked_document", False, "LINKED_DOCUMENT"),
        ("workshared", False, "WORKSHARED_DOCUMENT"),
        ("read_only", False, "READ_ONLY_DOCUMENT"),
        ("modifiable", False, "DOCUMENT_MODIFIABLE"),
        ("fixed_parameter_available", True, "FIXED_PARAMETER_MISSING"),
        ("fixed_parameter_binding_valid", True, "FIXED_PARAMETER_BINDING_INVALID"))
    for key, expected, reason in checks:
        if key not in facts or type(facts[key]) is not bool:
            return dict(eligible=False, reason_code="DOCUMENT_FACTS_UNREADABLE", field=key)
        if facts[key] is not expected:
            return dict(eligible=False, reason_code=reason)
    return dict(eligible=True, reason_code="COMPLETE")


class ControlledWritePermission(object):
    """Pure host-local state contract, not an authorization/security token.

    Caller must be a future explicit human UI control, never provider arguments.
    No visible control or event subscriptions are introduced in M4B-0/1.
    """
    def __init__(self):
        self._enabled = False
        self._document_key = None
        self.generation = 0

    def disable(self):
        self._enabled = False
        self._document_key = None
        self.generation += 1

    def enable_from_human(self, document_key, facts, human_confirmed=False):
        self.disable()
        eligibility = document_eligibility(facts)
        if (human_confirmed is not True or
                not isinstance(document_key, string_types) or not document_key):
            return False
        if not eligibility["eligible"]:
            return False
        self._document_key = document_key
        self._enabled = True
        return True

    def document_changed(self, document_key):
        if document_key != self._document_key:
            self.disable()

    def document_closed(self):
        self.disable()

    def pane_disposed(self):
        self.disable()

    def shutdown(self):
        self.disable()

    def view_model(self):
        return dict(enabled=self._enabled, document_key=self._document_key,
                    generation=self.generation,
                    status=("CONTROLLED WRITES: ENABLED FOR THIS SESSION" if self._enabled
                            else "CONTROLLED WRITES: DISABLED"),
                    dispatch_status="PROVIDER WRITE DISPATCH: NOT YET AVAILABLE",
                    provider_exposure_allowed=False)
