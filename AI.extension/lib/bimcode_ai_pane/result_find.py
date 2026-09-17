"""Local search of displayed blocks only; no host or tool dependencies."""
import re


class ResultFind(object):
    def __init__(self):
        self.matches = []
        self.current = -1

    def search(self, presentation, query):
        self.matches = []
        self.current = -1
        if query:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            for index, block in enumerate(presentation.get("blocks", [])):
                for match in pattern.finditer(block["label"] + block["text"]):
                    self.matches.append((index, match.start(), match.end()))
        if self.matches:
            self.current = 0

    def move(self, step):
        if self.matches:
            self.current = (self.current + step) % len(self.matches)

    def caption(self):
        return "{0}/{1}".format(self.current + 1, len(self.matches))


def fragments(text, offset, matches, active):
    """Split a label/value into non-overlapping styled runs, preserving text."""
    pending_text, pending_brush = "", None
    for content, brush in _fragments(text, offset, matches, active):
        if pending_text and brush != pending_brush:
            yield pending_text, pending_brush
            pending_text = ""
        pending_text += content
        pending_brush = brush
    if pending_text:
        yield pending_text, pending_brush


def _fragments(text, offset, matches, active):
    cursor = 0
    for number, start, end in matches:
        start, end = max(0, start - offset), min(len(text), end - offset)
        if end <= start:
            continue
        if start > cursor:
            yield text[cursor:start], None
        yield text[start:end], "AccentBrush" if number == active else "ButtonHoverBrush"
        cursor = end
    if cursor < len(text):
        yield text[cursor:], None
