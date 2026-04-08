# -*- coding: utf-8 -*-


class AgentSession(object):
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
        self.status = "idle"
        self.message = "Idle"

    def set_allow_destructive(self, enabled):
        self.allow_destructive = bool(enabled)

    def _add_step(self, command_id):
        command = self.catalog.get(command_id)
        if not command:
            return
        step = dict(command)
        step["enabled"] = True
        self.plan.append(step)

    def _match_goal(self, goal_text):
        goal = (goal_text or "").lower()
        ordered_ids = []

        def add_if_found(command_id, *phrases):
            for phrase in phrases:
                if phrase in goal and command_id not in ordered_ids:
                    ordered_ids.append(command_id)
                    return

        add_if_found("list-ducts-active-view", "list ducts in active view", "ducts in active view")
        add_if_found("find-unconnected-fittings", "unconnected fittings", "find unconnected fittings")
        add_if_found(
            "report-elements-without-system-assignment",
            "without system assignment",
            "system assignment",
        )
        add_if_found("health-check", "health check", "health summary", "model audit")
        add_if_found("count-ducts", "count ducts")
        add_if_found("total-duct-length", "total duct length", "duct length")
        add_if_found("export-schedule-names", "schedule names")
        add_if_found("export-all-schedule-data", "schedule data")
        add_if_found("clash-check", "clash check", "clash")

        if not ordered_ids:
            for command in self.catalog.values():
                prompt_text = (command.get("prompt_text") or "").lower()
                title = (command.get("title") or "").lower()
                if prompt_text and prompt_text in goal:
                    ordered_ids.append(command.get("id"))
                elif title and title in goal:
                    ordered_ids.append(command.get("id"))
                if len(ordered_ids) >= 3:
                    break

        return ordered_ids

    def plan_goal(self, goal_text):
        self.reset()
        self.goal = goal_text or ""
        self.status = "planning"
        self.message = "Planning"
        matched_ids = self._match_goal(goal_text)
        for command_id in matched_ids:
            self._add_step(command_id)
        if self.plan:
            self.status = "ready_to_execute"
            self.message = "Ready to execute"
        else:
            self.status = "failed"
            self.message = "Failed"
        return list(self.plan)

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
