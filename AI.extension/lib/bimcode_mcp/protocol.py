"""Small shared IPC contract. Python 2.7/3 compatible; no Revit/SDK imports."""
import binascii
import json
import os
import re
import sys
import time

VERSION = 1
MAX_REQUEST = 4096
MAX_RESPONSE = 100000
CONTEXT_SECONDS = 30.0
EXECUTION_SECONDS = 20.0
TOOLS = ("summarize_selected_pipes", "inspect_selected_pipe_connectors",
         "summarize_selected_mep_elements")
TEXT = (str, type(u""))


def monotonic():
    if sys.platform == "cli":
        from System.Diagnostics import Stopwatch
        return float(Stopwatch.GetTimestamp()) / Stopwatch.Frequency
    return time.monotonic()


def secret():
    return binascii.hexlify(os.urandom(32)).decode("ascii")


def is_token(value):
    return isinstance(value, TEXT) and re.match(r"\A[0-9a-f]{64}\Z", value) is not None


def equal_token(left, right):
    if not is_token(left) or not is_token(right):
        return False
    difference = 0
    for a, b in zip(left, right):
        difference |= ord(a) ^ ord(b)
    return difference == 0


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("DUPLICATE_KEY")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("NON_FINITE_JSON")


def loads(raw):
    return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)


def encode(value, limit):
    raw = json.dumps(value, ensure_ascii=True, allow_nan=False,
                     separators=(",", ":")).encode("ascii") + b"\n"
    if len(raw) > limit:
        raise ValueError("MESSAGE_TOO_LARGE")
    return raw


def receive(sock, limit, deadline):
    """One bounded line with a total deadline, including slow partial sends."""
    chunks = []
    size = 0
    while size < limit:
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise ValueError("DEADLINE_EXCEEDED")
        sock.settimeout(remaining)
        part = sock.recv(min(4096, limit - size))
        if not part:
            raise ValueError("INCOMPLETE_MESSAGE")
        chunks.append(part)
        size += len(part)
        if b"\n" in part:
            raw = b"".join(chunks)
            if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
                raise ValueError("INVALID_FRAME")
            return loads(raw.decode("utf-8"))
    raise ValueError("MESSAGE_TOO_LARGE")


def validate_request(value, token):
    if not isinstance(value, dict) or not equal_token(value.get("token"), token):
        raise ValueError("UNAUTHORIZED")
    if (type(value.get("version")) is not int or value["version"] != VERSION
            or not is_token(value.get("request_id"))):
        raise ValueError("INVALID_REQUEST")
    common = set(("version", "token", "request_id", "operation"))
    if value.get("operation") in ("ping", "context") and set(value) == common:
        return value
    if (value.get("operation") == "inspect"
            and set(value) == common | set(("tool", "context_token"))
            and isinstance(value["tool"], TEXT) and value["tool"] in TOOLS
            and is_token(value["context_token"])):
        return value
    raise ValueError("INVALID_REQUEST")


def result(request_id, data=None, error=None):
    return dict(version=VERSION, request_id=request_id, ok=error is None,
                data=data if error is None else None, error_code=error)
