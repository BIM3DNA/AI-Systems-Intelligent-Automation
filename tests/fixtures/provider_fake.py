"""Native process test fixture: no configuration, SDK, network or model access."""
import json
import sys
import time

request = json.loads(sys.stdin.read())
mode = request.get("user_text", "valid")
if mode == "timeout":
    time.sleep(10)
if mode == "nonzero":
    sys.stderr.write("fake-private-error")
    sys.exit(1)
if mode == "malformed":
    sys.stdout.write("not-json")
    sys.exit(0)
if mode == "stderr":
    sys.stderr.write("fake-private-error" * 10000)
result = dict(protocol_version=1, request_id=request["request_id"], ok=True,
              provider="openai", model="fake-model", text="fake answer", error=None)
if mode == "mismatch":
    result["request_id"] = "b" * 32
sys.stdout.write(json.dumps(result))
