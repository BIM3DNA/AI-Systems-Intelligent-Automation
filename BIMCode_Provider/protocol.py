"""Bounded one-shot scalar protocol; no host imports."""
import json
import re
import tool_protocol

MAX_REQUEST = 20000
MAX_TEXT = 12000
MESSAGES = {
    "CONFIG_MISSING_API_KEY": "Provider API key is not configured.",
    "CONFIG_MISSING_MODEL": "Provider model is not configured.",
    "INVALID_CONFIG": "Provider configuration is invalid.",
    "SIDECAR_PROTOCOL_ERROR": "Provider protocol is invalid.",
    "OPENAI_AUTH_ERROR": "OpenAI authentication or permission failed.",
    "OPENAI_RATE_LIMIT": "OpenAI rate limit reached. Try again later.",
    "OPENAI_QUOTA_OR_BILLING": "OpenAI quota or billing requires attention.",
    "OPENAI_TIMEOUT": "OpenAI request timed out.",
    "OPENAI_CONNECTION_ERROR": "OpenAI connection failed.",
    "OPENAI_API_ERROR": "OpenAI could not complete this request.",
    "OPENAI_EMPTY_RESPONSE": "OpenAI returned no assistant text.",
    "INTERNAL_PROVIDER_ERROR": "Provider is unavailable or failed internally.",
}
MESSAGES.update(tool_protocol.MESSAGES)


def failure(request_id, code, model=""):
    return dict(protocol_version=1, request_id=request_id, ok=False,
                provider="openai", model=model, text=None,
                error=dict(code=code, message=MESSAGES[code]))


def success(request_id, model, text):
    return dict(protocol_version=1, request_id=request_id, ok=True,
                provider="openai", model=model, text=text, error=None)


def parse(raw):
    if len(raw) > tool_protocol.MAX_REQUEST:
        raise ValueError("protocol")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("protocol")
            result[key] = value
        return result
    data = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(data, dict):
        raise ValueError("protocol")
    if (type(data.get("protocol_version")) is not int or data["protocol_version"] != 1
            or not isinstance(data.get("request_id"), str)
            or not re.fullmatch(r"[a-f0-9]{32}", data["request_id"])):
        raise ValueError("protocol")
    operation = data.get("operation")
    if operation in ("agent_turn", "tool_result"):
        return tool_protocol.validate_request(data)
    if len(raw) > MAX_REQUEST:
        raise ValueError("protocol")
    expected = {"protocol_version", "operation", "request_id"}
    if operation == "text_response":
        expected.add("user_text")
        text = data.get("user_text")
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError("protocol")
    elif operation != "readiness":
        raise ValueError("protocol")
    if set(data) != expected:
        raise ValueError("protocol")
    return data
