"""
Utils package initialization.
"""

from aixtools.logging.logging_config import get_logger  # pylint: disable=import-error
from aixtools.utils import config
from aixtools.utils.enum_with_description import EnumWithDescription
from aixtools.utils.persisted_dict import PersistedDict
from aixtools.utils.utils import (
    escape_backticks,
    escape_newline,
    find_file,
    prepend_all_lines,
    remove_quotes,
    tabit,
    to_str,
    tripple_quote_strip,
    truncate,
)

__all__ = [
    "config",
    "PersistedDict",
    "EnumWithDescription",
    "escape_newline",
    "escape_backticks",
    "find_file",
    "get_logger",
    "prepend_all_lines",
    "remove_quotes",
    "tabit",
    "to_str",
    "truncate",
    "tripple_quote_strip",
]
