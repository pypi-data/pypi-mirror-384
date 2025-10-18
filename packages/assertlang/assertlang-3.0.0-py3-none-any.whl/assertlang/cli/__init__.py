"""CLI utilities for Promptware."""

# Existing validation utilities
from .validate_contract import (
    validate_contract,
    print_validation_result,
    ContractValidator,
    ValidationResult,
)

# New UX improvement utilities (will be added)
try:
    from .progress import timed_step, show_progress, show_completion
    from .error_formatter import format_parse_error, get_parse_error_suggestions, format_file_not_found_error
    from .file_helpers import find_similar_files, check_file_writable
    _has_ux_utils = True
except ImportError:
    _has_ux_utils = False

__all__ = [
    'validate_contract',
    'print_validation_result',
    'ContractValidator',
    'ValidationResult',
]

if _has_ux_utils:
    __all__.extend([
        'timed_step',
        'show_progress',
        'show_completion',
        'format_parse_error',
        'get_parse_error_suggestions',
        'format_file_not_found_error',
        'find_similar_files',
        'check_file_writable',
    ])
