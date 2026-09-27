"""M4A preview contracts only. No provider registration or execution authority."""
import re

M4A_FEATURE_ID = "MEP-PARAM-WR-001"
M4A_ACTION_ID = "MEP-PARAM-WR-001-A01"
M4A_TEST_PARAMETER_NAME = "BIMCode_M4A_TestText"
M4A_TEST_PARAMETER_GUID = "2f3c955d-45ee-4258-bc61-08acd40a2912"
M4A_CATEGORY = "OST_PipeCurves"
M4A_MAX_TEXT_LENGTH = 64
PREVIEW_OK = "MEP_PARAMETER_WRITE_PREVIEW_OK"
PREVIEW_NOT_READY = "MEP_PARAMETER_WRITE_PREVIEW_NOT_READY"
PREVIEW_FAILED = "MEP_PARAMETER_WRITE_PREVIEW_FAILED"

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)

_VALUE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9 _-]{0,63}\Z")


def validate_value(value):
    """Never coerce, trim, normalize or truncate a proposed value."""
    valid = (isinstance(value, string_types) and
             bool(_VALUE.match(value)) and value == value.strip())
    return {"valid": valid, "reason_code": "COMPLETE" if valid else "INVALID_VALUE",
            "value": value if valid else None}
