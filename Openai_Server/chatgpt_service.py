import json
import os
import sys


def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")


def get_openai_client():
    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def get_provider_state():
    api_key = get_openai_api_key()
    if not api_key:
        return {
            "available": False,
            "state": "missing_api_key",
            "message": "Cloud unavailable: missing OPENAI_API_KEY",
        }
    return {
        "available": True,
        "state": "available",
        "message": "Cloud available",
    }


def ask_openai(
    question,
    model="gpt-4o-mini",
    max_tokens=300,
    temperature=0.2,
):
    client = get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def normalize_intent_to_supported_action(user_request, supported_actions, model_name="gpt-4o-mini"):
    supported_actions = supported_actions or []
    prompt = """You are a strict BIM planning normalizer.
Choose exactly one supported action from the list or reject the request.
Do not invent new tools or actions.
Return machine-readable JSON only with this schema:
{
  "matched_action": "<action id or empty string>",
  "confidence": 0.0,
  "summary": "<brief explanation>",
  "execution_ready": true,
  "rejected": false
}
If unsupported or ambiguous, return:
{
  "matched_action": "",
  "confidence": 0.0,
  "summary": "<why unsupported or ambiguous>",
  "execution_ready": false,
  "rejected": true
}
Supported actions:
{actions}
User request:
{request}
""".format(
        actions=json.dumps(supported_actions, indent=2),
        request=user_request,
    )
    raw = ask_openai(prompt, model=model_name, max_tokens=250, temperature=0.0)
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
        data = json.loads(raw)
    except Exception:
        raise RuntimeError("Cloud planner returned non-JSON output.")

    return {
        "matched_action": data.get("matched_action", "") or "",
        "confidence": float(data.get("confidence", 0.0) or 0.0),
        "summary": data.get("summary", "") or "",
        "execution_ready": bool(data.get("execution_ready", False)),
        "rejected": bool(data.get("rejected", False)),
    }


def _read_stdin_payload():
    raw = sys.stdin.read()
    if not raw:
        return {}
    return json.loads(raw)


def _write_json(data):
    sys.stdout.write(json.dumps(data))


def main():
    if len(sys.argv) < 2:
        _write_json({"ok": False, "error": "No command provided."})
        return 1

    command = sys.argv[1]
    try:
        if command == "--provider-state":
            _write_json({"ok": True, "result": get_provider_state()})
            return 0

        if command == "--normalize-intent":
            payload = _read_stdin_payload()
            result = normalize_intent_to_supported_action(
                payload.get("user_request", ""),
                payload.get("supported_actions", []),
                payload.get("model_name", "gpt-4o-mini"),
            )
            _write_json({"ok": True, "result": result})
            return 0

        if command == "--ask":
            payload = _read_stdin_payload()
            result = ask_openai(
                payload.get("question", ""),
                model=payload.get("model", "gpt-4o-mini"),
                max_tokens=int(payload.get("max_tokens", 300)),
                temperature=float(payload.get("temperature", 0.2)),
            )
            _write_json({"ok": True, "result": result})
            return 0

        _write_json({"ok": False, "error": "Unknown command: {0}".format(command)})
        return 1
    except Exception as exc:
        _write_json({"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
