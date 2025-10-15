from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field
from pydantic.dataclasses import dataclass

from chainlit.context import context
from chainlit.input_widget import InputWidget


@dataclass
class Knowledge:
    """Represents a knowledge object."""

    id: str
    name: str
    type: str  # "document", "database", "api", "custom"
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)  # Type-specific configuration
    active: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    inputs_override: Optional[Dict[str, Any]] = None  # Per-item input property overrides

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "config": self.config,
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "inputs_override": self.inputs_override,
        }


@dataclass
class KnowledgeType:
    """Defines a knowledge type with its input widgets."""

    type: str
    label: str
    description: str
    icon: Optional[str] = None
    inputs: List[InputWidget] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "label": self.label,
            "description": self.description,
            "icon": self.icon,
            "inputs": [inp.to_dict() for inp in self.inputs],
        }


@dataclass
class KnowledgeSettings:
    """Main class for knowledge panel configuration."""

    types: List[KnowledgeType] = Field(default_factory=list)

    async def send(self):
        """Send knowledge panel configuration to frontend."""

        types_dict = [kt.to_dict() for kt in self.types]
        await context.emitter.emit("set_knowledge_types", types_dict)
