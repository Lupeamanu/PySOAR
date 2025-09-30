""" Basic playbook data model """

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Action:
    """ Represents a single action in a playbook """
    id: str
    type: str # "log", "python_code", "condition", "api_call"
    parameters: Dict[str, Any] = field(default_factory=dict)
    output_variable: Optional[str] = None

    # For conditional actions
    condition: Optional[str] = None
    if_true: Optional[List["Action"]] = None
    if_false: Optional[List["Action"]] = None


@dataclass
class Playbook:
    """ Represents a complete """
    name: str
    description: str
    trigger: str # "manual", "api_call", "scheduled"
    inputs: List[str] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Playbook":
        """ Create a Playbook instance from a dictionary """
        playbook_data = data.get("playbook", {})

        actions = []
        for action_data in playbook_data.get("actions", []):
            actions.append(cls._parse_action(action_data))

        return cls(
            name=playbook_data.get("name", "Unnamed Playbook"),
            description=playbook_data.get("description", ''),
            trigger=playbook_data.get("trigger", "manual"),
            inputs=playbook_data.get("inputs", []),
            actions=actions
        )


    @classmethod
    def _parse_action(cls, action_data: Dict[str, Any]) -> Action:
        """ Parse an action from dictionary """
        action = Action(
            id=action_data.get("id", ''),
            type=action_data.get("type", ''),
            parameters=action_data.get("parameters", {}),
            output_variable=action_data.get("output_variable"),
            condition=action_data.get("condition")
        )

        # Parse contitional branches
        if action.type == "condition":
            if "if_true" in action_data:
                action.if_true = [cls._parse_action(a) for a in action_data["if_true"]]
            if "if_false" in action_data:
                action.if_false = [cls._parse_action(a) for a in action_data["if_false"]]

        return action