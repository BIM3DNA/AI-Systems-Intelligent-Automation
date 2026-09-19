"""Fixed M3C host allowlist. No discovery or caller-supplied action IDs."""
TOOLS = (
    ("summarize_selected_pipes", "PIPING-RO-001-A01", "Selected Pipes Summary"),
    ("inspect_selected_pipe_connectors", "PIPING-RO-001-A02", "Selected Pipe Connectors"),
    ("inspect_selected_pipe_system_assignment", "PIPING-RO-001-A03", "Selected Pipe System Assignment"),
    ("inspect_selected_pipe_qa_health", "PIPING-RO-001-A04", "Selected Pipe QA Health"),
)
ACTIONS = dict((name, action) for name, action, label in TOOLS)
LABELS = dict((action, label) for name, action, label in TOOLS)
