"""mmar-utils package.

Utilities for multi-modal architectures team
"""

from mmar_utils.models import ResourcesModel
from mmar_utils.validators import ExistingDir

from .decorators_on_error_log_and_none import on_error_log_and_none
from .decorators_retries import retries
from .decorators_trace_with import FunctionCall, FunctionEnter, FunctionInvocation, trace_with
from .mmar_types import Either
from .parallel_map import parallel_map
from .utils import read_json, try_parse_bool, try_parse_float, try_parse_int, try_parse_json
from .utils_collections import edit_object, flatten
from .utils_texts import (
    chunk_respect_semantic,
    extract_text_inside,
    pretty_line,
    remove_prefix_if_present,
    remove_suffix_if_present,
    rindex_safe,
)
from .utils_texts_postprocessing import clean_and_fix_text, postprocess_text
from .validators import ExistingFile, ExistingPath, Message, Prompt, SecretStrNotEmpty, StrNotEmpty

__all__ = [
    "Either",
    "ExistingDir",
    "ExistingFile",
    "ExistingPath",
    "FunctionCall",
    "FunctionEnter",
    "FunctionInvocation",
    "Message",
    "Prompt",
    "SecretStrNotEmpty",
    "StrNotEmpty",
    "chunk_respect_semantic",
    "edit_object",
    "extract_text_inside",
    "flatten",
    "on_error_log_and_none",
    "parallel_map",
    "pretty_line",
    "read_json",
    "remove_prefix_if_present",
    "remove_suffix_if_present",
    "retries",
    "rindex_safe",
    "trace_with",
    "try_parse_bool",
    "try_parse_float",
    "try_parse_int",
    "try_parse_json",
    "postprocess_text",
    "ResourcesModel",
    "clean_and_fix_text",
]
