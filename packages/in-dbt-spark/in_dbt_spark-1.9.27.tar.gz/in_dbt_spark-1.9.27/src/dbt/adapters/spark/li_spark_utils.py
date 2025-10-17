from typing import Any, Optional

from jinja2.runtime import Undefined


def remove_undefined(v: Any) -> Any:
    return None if isinstance(v, Undefined) else v


def is_openhouse(database: Optional[str], schema: Optional[str]) -> bool:
    return database == "openhouse" or "." in str(schema)
