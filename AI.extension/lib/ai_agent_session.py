# -*- coding: utf-8 -*-


class AgentSession(object):
    SUPPORTED_MESSAGE = (
        "Supported planner requests: select all ducts; count selected ducts; "
        "count all ducts in active view; list ducts in active view; "
        "find unconnected fittings; report elements without system assignment; create sheet."
    )

    def __init__(self, commands=None):
        self.allow_destructive = False
        self.refresh_catalog(commands or [])
        self.reset()

    def refresh_catalog(self, commands):
        self.catalog = {}
        for command in commands:
            self.catalog[command.get("id")] = dict(command)

    def reset(self):
        self.goal = ""
        self.plan = []
        self.plan_object = None
        self.status = "idle"
        self.message = "Idle"
        self.guidance = self.SUPPORTED_MESSAGE

    def set_allow_destructive(self, enabled):
        self.allow_destructive = bool(enabled)

    def _add_step(self, command_id):
        command = self.catalog.get(command_id)
        if not command:
            return
        step = dict(command)
        step["enabled"] = True
        self.plan.append(step)

    def get_supported_actions(self):
        actions = []
        for command in self.catalog.values():
            actions.append(
                {
                    "id": command.get("id"),
                    "title": command.get("title"),
                    "prompt_text": command.get("prompt_text"),
                    "requires_modification": command.get("role") == "modify",
                    "destructive": command.get("risk_level") == "high",
                }
            )
        return actions

    def _match_goal(self, goal_text):
        goal = (goal_text or "").lower()
        ordered_ids = []

        def add_if_found(command_id, *phrases):
            for phrase in phrases:
                if phrase in goal and command_id not in ordered_ids:
                    ordered_ids.append(command_id)
                    return

        add_if_found("select-all-ducts", "select all ducts", "select ducts")
        add_if_found(
            "count-selected-ducts",
            "count selected ducts",
            "count the selected ducts",
            "how many selected ducts are there",
            "how many selected ducts",
        )
        add_if_found(
            "count-ducts-active-view",
            "count all ducts in active view",
            "count ducts in active view",
            "how many ducts are in active view",
        )
        add_if_found(
            "list-ducts-active-view",
            "list ducts in active view",
            "list all ducts in active view",
            "ducts in active view",
        )
        add_if_found("find-unconnected-fittings", "unconnected fittings", "find unconnected fittings")
        add_if_found(
            "report-elements-without-system-assignment",
            "without system assignment",
            "system assignment",
        )
        add_if_found(
            "create-sheet-reviewed-template",
            "create sheet",
            "make a sheet",
            "create a sheet for me",
            "make sheet",
        )

        return ordered_ids

    def plan_goal(self, goal_text):
        self.reset()
        self.goal = goal_text or ""
        self.status = "planning"
        self.message = "Planning"
        matched_ids = self._match_goal(goal_text)
        if matched_ids:
            self.build_plan_from_action(
                matched_ids[0],
                confidence=0.75,
                summary="Local deterministic planner matched a supported action.",
            )
        else:
            self.plan_object = {
                "matched_action": "",
                "confidence": 0.0,
                "requires_modification": False,
                "destructive": False,
                "summary": "Unsupported request.",
                "execution_ready": False,
            }
            self.status = "failed"
            self.message = "Unsupported request"
            self.guidance = self.SUPPORTED_MESSAGE
        return list(self.plan)

    def build_plan_from_action(self, action_id, confidence, summary):
        self.reset()
        command = self.catalog.get(action_id)
        if not command:
            self.plan_object = {
                "matched_action": "",
                "confidence": 0.0,
                "requires_modification": False,
                "destructive": False,
                "summary": "Unsupported request.",
                "execution_ready": False,
            }
            self.status = "failed"
            self.message = "Unsupported request"
            self.guidance = self.SUPPORTED_MESSAGE
            return None

        self._add_step(action_id)
        self.plan_object = {
            "matched_action": action_id,
            "confidence": float(confidence),
            "requires_modification": command.get("role") == "modify",
            "destructive": command.get("risk_level") == "high",
            "summary": summary,
            "execution_ready": True,
        }
        self.status = "ready_to_execute"
        self.message = "Ready to execute"
        self.guidance = "Plan ready for review."
        return dict(self.plan_object)

    def toggle_command(self, command_id):
        for step in self.plan:
            if step.get("id") == command_id:
                step["enabled"] = not step.get("enabled", True)
                return step
        return None

    def get_visible_steps(self):
        return list(self.plan)

    def execute(self, executor):
        if not self.plan:
            self.status = "failed"
            self.message = "Failed"
            return []

        self.status = "executing"
        self.message = "Executing"
        results = []
        for step in self.plan:
            result = {"step": step, "status": "skipped", "message": "Disabled"}
            if step.get("enabled", True):
                if step.get("role") == "modify" and not self.allow_destructive:
                    result = {
                        "step": step,
                        "status": "blocked",
                        "message": "Modifying command blocked because destructive tools are disabled.",
                    }
                else:
                    try:
                        message = executor(step)
                        result = {"step": step, "status": "executed", "message": message}
                    except Exception as exc:
                        self.status = "failed"
                        self.message = "Failed"
                        result = {"step": step, "status": "failed", "message": str(exc)}
            results.append(result)

        if self.status != "failed":
            self.status = "idle"
            self.message = "Idle"
        return results
