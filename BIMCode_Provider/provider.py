"""Only approved network boundary: official SDK -> fixed OpenAI Responses API."""
from openai import OpenAI
import openai
import httpx2
from protocol import failure, success, MAX_TEXT

INSTRUCTION = (
    "You are BIMCode AI running inside Autodesk Revit. Answer the user's text only. "
    "You cannot inspect or modify the active Revit model through AI tools. "
    "No ModelMind tools are available in this milestone."
)


def client_for(config):
    # Ignore endpoint/proxy customization, redirects, retries and SDK diagnostics.
    return OpenAI(api_key=config.api_key, base_url="https://api.openai.com/v1",
                  admin_api_key="", organization="", project="", webhook_secret="",
                  timeout=45.0, max_retries=0,
                  http_client=httpx2.Client(trust_env=False, follow_redirects=False,
                                            timeout=45.0))


def send(config, request, factory=client_for):
    request_id = request["request_id"]
    try:
        with factory(config) as client:
            response = client.responses.create(
                model=config.model, input=request["user_text"], instructions=INSTRUCTION,
                max_output_tokens=2048, store=False, background=False)
        if getattr(response, "status", None) != "completed":
            return failure(request_id, "OPENAI_API_ERROR", config.model)
        text = response.output_text
        if not isinstance(text, str) or not text.strip():
            return failure(request_id, "OPENAI_EMPTY_RESPONSE", config.model)
        # Reject accidental credential echoes rather than returning partial secrets.
        if config.api_key in text or "authorization:" in text.lower():
            return failure(request_id, "INTERNAL_PROVIDER_ERROR", config.model)
        if len(text) > MAX_TEXT:
            text = text[:MAX_TEXT - 40] + "\n[Response truncated by display limit.]"
        return success(request_id, config.model, text)
    except (openai.AuthenticationError, openai.PermissionDeniedError):
        code = "OPENAI_AUTH_ERROR"
    except openai.RateLimitError as exc:
        code = ("OPENAI_QUOTA_OR_BILLING" if getattr(exc, "code", None) in
                ("insufficient_quota", "billing_hard_limit_reached", "billing_not_active")
                else "OPENAI_RATE_LIMIT")
    except openai.APITimeoutError:
        code = "OPENAI_TIMEOUT"
    except openai.APIConnectionError:
        code = "OPENAI_CONNECTION_ERROR"
    except openai.APIError:
        code = "OPENAI_API_ERROR"
    except Exception:
        code = "INTERNAL_PROVIDER_ERROR"
    return failure(request_id, code, config.model)
