"""Provider UI dispatch and presentation, separate from ModelMind events."""
from bimcode_ai_pane import provider_bridge
from bimcode_ai_pane.result_presentation import _Budget, NOTICE
from bimcode_ai_pane.ai_tool_registry import LABELS


def launch(payload, dispatcher, complete):
    from System import Action
    from System.Threading import Thread, ThreadStart

    def worker():
        try:
            result = provider_bridge.run(payload)
        except Exception:
            result = provider_bridge.failure(payload["request_id"], "SIDECAR_START_FAILED")
        # This is the sole UI interaction on this thread: enqueue, never touch controls.
        try:
            dispatcher.BeginInvoke(Action(lambda: complete(result)))
        except Exception:
            # Dispatcher shutdown: the session is ending; no UI or Revit access.
            pass
    thread = Thread(ThreadStart(worker))
    thread.IsBackground = True
    thread.Start()


def presentation(result):
    budget = _Budget()
    blocks = []
    budget.add(blocks, "title", "AI Response")
    budget.add(blocks, "fact", "OpenAI", "Provider: ")
    budget.add(blocks, "fact", result.get("model") or "Unavailable", "Model: ")
    budget.add(blocks, "status", "COMPLETE" if result["ok"] else "FAILED",
               tone="SuccessBrush" if result["ok"] else "ErrorBrush")
    provenance = result.get("tool_provenance")
    if provenance:
        budget.add(blocks, "fact", LABELS.get(provenance["action_id"], "Unavailable"), "Tool used: ")
        budget.add(blocks, "technical", provenance["action_id"], "Action: ")
        budget.add(blocks, "technical", provenance["classification"], "Tool classification: ")
        budget.add(blocks, "technical", provenance["reason_code"], "Tool reason: ")
        if provenance["action_id"] == "MEP-MULTI-RO-001-A01":
            budget.add(blocks, "technical", ", ".join(provenance.get("sub_actions", [])) or "None", "Sub-actions evaluated: ")
            for child in provenance.get("children", []):
                budget.add(blocks, "technical", "{0}: {1} / {2} / {3}".format(child["action_id"],
                    child["execution_state"], child["classification"], child["reason_code"]), "Child: ")
            if provenance.get("transport_truncated"):
                budget.add(blocks, "note", "Composite transport omissions apply.", tone="WarningBrush")
    if result["ok"]:
        budget.add(blocks, "heading", "Response")
        budget.add(blocks, "text", result["text"])
    else:
        budget.add(blocks, "technical", result["error"]["code"], "Classification: ")
        budget.add(blocks, "text", result["error"]["message"], "Message: ")
    if budget.truncated:
        blocks.append(dict(kind="note", label="", text=NOTICE, tone="WarningBrush"))
    return dict(blocks=blocks, truncated=budget.truncated,
                character_count=sum(len(b["label"]) + len(b["text"]) + 2 for b in blocks))
