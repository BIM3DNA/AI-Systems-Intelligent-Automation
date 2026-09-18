"""Python 3 configuration loader. Credentials never leave this process."""
from dataclasses import dataclass, field
from pathlib import Path
import os
import re


@dataclass(repr=False)
class Config:
    state: str
    api_key: str = field(default="", repr=False)
    model: str = ""

    def __repr__(self):
        return "Config(state={!r})".format(self.state)


def load_config(root, environ=None):
    env = os.environ if environ is None else environ
    names = ("OPENAI_API_KEY", "OPENAI_MODEL")
    values = {k: env[k] for k in names if k in env}
    try:
        if len(values) != 2:
            path = Path(root) / ".env.local"
            parsed = {}
            if path.exists():
                if path.stat().st_size > 65536:
                    return Config("INVALID_CONFIG")
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip() or line.lstrip().startswith("#"):
                        continue
                    key, sep, value = line.partition("=")
                    key = key.strip()
                    if key not in names:
                        continue
                    if not sep or key in parsed:
                        return Config("INVALID_CONFIG")
                    value = value.strip()
                    if value.startswith(("'", '"')):
                        if len(value) < 2 or value[-1] != value[0]:
                            return Config("INVALID_CONFIG")
                        value = value[1:-1]
                    parsed[key] = value
            for key in names:
                if key not in values:
                    values[key] = parsed.get(key, "")
        key, model = (values.get(k, "") for k in names)
        if not isinstance(key, str) or not isinstance(model, str):
            return Config("INVALID_CONFIG")
        if not key.strip():
            return Config("MISSING_API_KEY")
        if not model.strip():
            return Config("MISSING_MODEL")
        if (len(key) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in key)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", model)
                or key in model):
            return Config("INVALID_CONFIG")
        return Config("READY", key, model)
    except Exception:
        return Config("INVALID_CONFIG")
