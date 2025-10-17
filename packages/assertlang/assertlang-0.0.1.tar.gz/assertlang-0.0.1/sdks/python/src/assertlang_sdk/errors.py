"""Promptware SDK error taxonomy."""


class PromptwareError(Exception):
    """Base exception for all SDK errors."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class CompatibilityError(PromptwareError):
    """Raised when SDK and daemon versions are incompatible."""

    def __init__(self, sdk_version: str, daemon_version: str, min_daemon_version: str):
        super().__init__(
            "E_COMPAT",
            f"SDK {sdk_version} requires daemon >={min_daemon_version}, found {daemon_version}",
        )


# Standard error codes (match daemon taxonomy)
E_RUNTIME = "E_RUNTIME"
E_POLICY = "E_POLICY"
E_TIMEOUT = "E_TIMEOUT"
E_BUILD = "E_BUILD"
E_JSON = "E_JSON"
E_FS = "E_FS"
E_METHOD = "E_METHOD"
E_COMPAT = "E_COMPAT"