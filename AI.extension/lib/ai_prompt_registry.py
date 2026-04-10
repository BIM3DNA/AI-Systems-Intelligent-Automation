# -*- coding: utf-8 -*-
import json
import os
import time


class PromptCatalog(object):
    CATEGORY_ORDER = [
        "Delete",
        "Count",
        "Reports",
        "Lists",
        "Materials",
        "Tags / Tools",
        "Select All",
        "Totals",
        "Clash Check",
    ]
    def __init__(self, catalog_path, approved_path):
        self.catalog_path = catalog_path
        self.approved_path = approved_path

    def _read_list(self, path):
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as stream:
                loaded = json.load(stream)
            if isinstance(loaded, list):
                return loaded
        except Exception:
            pass
        return []

    def _write_list(self, path, items):
        with open(path, "w") as stream:
            json.dump(items, stream, indent=2, sort_keys=True)

    def get_base_entries(self):
        return self._read_list(self.catalog_path)

    def get_approved_entries(self):
        return self._read_list(self.approved_path)

    def get_enabled_entries(self):
        items = []
        for entry in self.get_base_entries():
            if entry.get("enabled", True):
                items.append(self._normalize_entry(entry))
        return items

    def _normalize_entry(self, entry):
        normalized = dict(entry or {})
        normalized["discipline"] = normalized.get("discipline", "General")
        normalized["scope_type"] = normalized.get("scope_type", "project")
        normalized["planner_aliases"] = list(normalized.get("planner_aliases") or [])
        normalized["deterministic_handler"] = normalized.get("deterministic_handler", "")
        normalized["requires_confirmation"] = bool(normalized.get("requires_confirmation", False))
        return normalized

    def is_shared_reviewed_action(self, entry):
        entry = self._normalize_entry(entry)
        return bool(entry.get("enabled", True) and entry.get("deterministic_handler"))

    def get_entry_by_prompt(self, prompt_text):
        target = (prompt_text or "").strip().lower()
        for entry in self.get_enabled_entries():
            prompt = (entry.get("prompt_text") or "").strip().lower()
            title = (entry.get("title") or "").strip().lower()
            aliases = [str(alias).strip().lower() for alias in entry.get("planner_aliases") or []]
            if prompt == target or title == target or target in aliases:
                return entry
        return None

    def _matches_filter(self, entry, filter_text):
        if not filter_text:
            return True
        haystacks = [
            entry.get("title", ""),
            entry.get("category", ""),
            entry.get("prompt_text", ""),
            entry.get("role", ""),
            entry.get("mode", ""),
            entry.get("discipline", ""),
            entry.get("scope_type", ""),
            " ".join(entry.get("planner_aliases") or []),
        ]
        ft = filter_text.lower()
        for text in haystacks:
            if ft in str(text).lower():
                return True
        return False

    def get_tree_sections(self, filter_text=None):
        filter_text = filter_text or ""
        grouped = {}
        for entry in self.get_enabled_entries():
            if not self._matches_filter(entry, filter_text):
                continue
            category = entry.get("category", "Uncategorized")
            grouped.setdefault(category, []).append(entry)

        sections = []
        ordered = []
        for category in self.CATEGORY_ORDER:
            if category in grouped:
                ordered.append(category)
        for category in grouped.keys():
            if category not in ordered:
                ordered.append(category)
        for category in ordered:
            sections.append({"header": category, "items": grouped[category], "kind": "catalog"})

        approved = []
        for entry in self.get_approved_entries():
            if self._matches_filter(entry, filter_text):
                approved.append(entry)
        if approved:
            sections.append({"header": "Approved Recipes", "items": approved, "kind": "approved"})
        return sections

    def get_reviewed_actions(self):
        actions = []
        for entry in self.get_enabled_entries():
            if self.is_shared_reviewed_action(entry):
                actions.append(self._normalize_entry(entry))
        return actions

    def get_agent_commands(self):
        commands = []
        for entry in self.get_reviewed_actions():
            commands.append(dict(entry))
        return commands

    def save_approved_recipe(self, metadata, code_text, source_entry=None):
        source_entry = source_entry or {}
        metadata = metadata or {}
        items = self.get_approved_entries()
        recipe = {
            "id": metadata.get("id") or "approved-{0}".format(int(time.time())),
            "title": metadata.get("title") or source_entry.get("title") or "Approved recipe",
            "category": metadata.get("category") or source_entry.get("category", "Approved Recipes"),
            "role": metadata.get("role") or source_entry.get("role", "modify"),
            "risk_level": metadata.get("risk_level") or source_entry.get("risk_level", "medium"),
            "mode": source_entry.get("mode", "deterministic"),
            "prompt_text": metadata.get("source_prompt") or metadata.get("prompt_text") or "",
            "source_prompt": metadata.get("source_prompt") or metadata.get("prompt_text") or "",
            "enabled": bool(metadata.get("enabled", True)),
            "source": "approved_recipe",
            "stored_code": code_text,
            "approved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        items.append(recipe)
        self._write_list(self.approved_path, items)
        return recipe
