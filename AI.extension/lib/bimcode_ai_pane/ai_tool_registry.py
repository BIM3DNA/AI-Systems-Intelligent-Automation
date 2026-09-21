"""Fixed M3D host allowlist. No discovery or caller-supplied action IDs."""
TOOLS = (
    ("summarize_selected_pipes", "PIPING-RO-001-A01", "Selected Pipes Summary"),
    ("inspect_selected_pipe_connectors", "PIPING-RO-001-A02", "Selected Pipe Connectors"),
    ("inspect_selected_pipe_system_assignment", "PIPING-RO-001-A03", "Selected Pipe System Assignment"),
    ("inspect_selected_pipe_qa_health", "PIPING-RO-001-A04", "Selected Pipe QA Health"),
    ("summarize_selected_ducts", "HVAC-RO-001-A01", "Selected Ducts Summary"),
    ("inspect_selected_duct_connectors", "HVAC-RO-001-A02", "Selected Duct Connectors"),
    ("inspect_selected_duct_system_assignment", "HVAC-RO-001-A03", "Selected Duct System Assignment"),
    ("inspect_selected_duct_qa_health", "HVAC-RO-001-A04", "Selected Duct QA Health"),
)
ACTIONS = dict((name, action) for name, action, label in TOOLS)
LABELS = dict((action, label) for name, action, label in TOOLS)
SPECIALTIES = dict((action, action.split("-", 1)[0]) for name, action, label in TOOLS)
