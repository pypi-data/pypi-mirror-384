from dataclasses import dataclass
from pathlib import Path

from serialite import field, serializable


@serializable
@dataclass(frozen=True, kw_only=True)
class QspDesignerModelFromBytes:
    base64_content: str
    imports: dict[Path, str] = field(default_factory=dict)
