""" Case management data models for PySOAR """

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class Severity(Enum):
    """ Case severity levels """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(Enum):
    """ Case stastus """
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EventType(Enum):
    """ Types of case events """
    CREATED = "created"
    COMMENT = "comment"
    STATUS_CHANGE = "status_change"
    PLAYBOOK_RUN = "playbook_run"
    ARTIFACT_ADDED = "artifact_added"
    ASSIGNED = "assigned"


@dataclass
class Artifact:
    """ Security artifact (IOC) associated with a case """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: str = "" # ip, domain, hash, email, url
    value: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    added_at: datetime = field(default_factory=datetime.now)


    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "artifact_type": self.artifact_type,
            "value": self.value,
            "description": self.description,
            "tags": self.tags,
            "added_at": self.added_at.isoformat()
        }


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Artifact':
        artifact = cls(
            id=data.get("id", str(uuid.uuid4())),
            artifact_type=data.get("artifact_type", ''),
            value=data.get("value", ''),
            description=data.get("description", ''),
            tags=data.get("tags", [])
        )
        if "added_at" in data:
            artifact.added_at = datetime.fromisoformat(data["added_at"])
        return artifact


@dataclass
class CaseEvent:
    """ Event in a case timeline """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = EventType.COMMENT.value
    description: str = ""
    user: str = "system"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "description": self.description,
            "user": self.user,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaseEvent":
        event = cls(
            id=data.get("id", str(uuid.uuid4())),
            event_type=data.get("event_type", EventType.COMMENT.value),
            description=data.get("description", ''),
            user=data.get("user", "system"),
            metadata=data.get("metadata", {})
        )
        if "timestamp" in data:
            event.timestamp = datetime.fromisoformat(data["timestamp"])
        return event


@dataclass
class Case:
    """ Security case/incident """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    severity: str = Severity.MEDIUM.value
    status: str = Status.OPEN.value
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    
    # Related data
    artifacts: List[Artifact] = field(default_factory=list)
    events: List[CaseEvent] = field(default_factory=list)
    playbooks_executed: List[str] = field(default_factory=list)


    def __post_init__(self):
        """ Add creation event """
        if not self.events:
            self.add_event(
                EventType.CREATED.value,
                f"Case created: {self.title}",
                user="system"
            )


    def add_event(self, event_type: str, description: str, user: str = "system", metadata: Dict[str, Any] = None): # type: ignore
        """ Add an event to the case timeline """
        event = CaseEvent(
            event_type=event_type,
            description=description,
            user=user,
            metadata=metadata or {}
        )
        self.events.append(event)
        self.updated_at = datetime.now()


    def add_artifact(self, artifact_type: str, value: str, description: str = "", tags: List[str] = None): # type: ignore
        """ Add an artifact to the case """
        artifact = Artifact(
            artifact_type=artifact_type,
            value=value,
            description=description,
            tags=tags or []
        )
        self.artifacts.append(artifact)
        self.add_event(
            EventType.ARTIFACT_ADDED.value,
            f"Added {artifact_type}: {value}",
            user="system"
        )
        return artifact


    def update_status(self, new_status: str, user: str = "system"):
        """ Update case status """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()

        if new_status == Status.CLOSED.value:
            self.closed_at = datetime.now()

        self.add_event(
            EventType.STATUS_CHANGE.value,
            f"Status changed from {old_status} to {new_status}",
            user=user
        )


    def add_comment(self, comment: str, user: str = "system"):
        """ Add a comment to the case """
        self.add_event(
            EventType.COMMENT.value,
            comment,
            user=user
        )


    def execute_playbook(self, playbook_name: str, result: Dict[str, Any]):
        """ Record playbook execution """
        self.playbooks_executed.append(playbook_name)
        self.add_event(
            EventType.PLAYBOOK_RUN.value,
            f"Executed playbook: {playbook_name} - Status: {result.get('status')}",
            user="system",
            metadata={"playbook": playbook_name, "result": result}
        )


    def to_dict(self) -> Dict[str, Any]:
        """ Convert case to dictionary """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "events": [e.to_dict() for e in self.events],
            "playbooks_executed": self.playbooks_executed
        }


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Case":
        """ Create case from dictionary """
        case = cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ''),
            description=data.get("description", ''),
            severity=data.get("severity", Severity.MEDIUM.value),
            status=data.get("status", Status.OPEN.value),
            assigned_to=data.get("assigned_to"),
            tags=data.get("tags", []),
            playbooks_executed=data.get("playbooks_executed", [])
        )
        
        # Parse dates
        if "created_at" in data:
            case.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            case.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("closed_at"):
            case.closed_at = datetime.fromisoformat(data["closed_at"])
        
        # Parse artifacts
        case.artifacts = [Artifact.from_dict(a) for a in data.get("artifacts", [])]
        
        # Parse events
        case.events = [CaseEvent.from_dict(e) for e in data.get("events", [])]
        
        return case   