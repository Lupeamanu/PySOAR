"""
Playbook execution engine for PySOAR
"""
import re
import yaml
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.playbook import Playbook, Action


class PlaybookEngine:
    """Executes security playbooks"""
    
    def __init__(self, integration_manager=None):
        self.context = {}  # Stores variables during execution
        self.execution_log = []  # Tracks all actions taken
        self.integration_manager = integration_manager
    
    def load_playbook(self, playbook_path: str) -> Playbook:
        """Load a playbook from a YAML file"""
        with open(playbook_path, 'r') as f:
            data = yaml.safe_load(f)
        return Playbook.from_dict(data)
    
    def execute(self, playbook: Playbook, inputs: Dict[str, Any] = None) -> Dict[str, Any]: # type: ignore
        """Execute a playbook with given inputs"""
        self.context = {'inputs': inputs or {}}
        self.execution_log = []
        
        start_time = datetime.now()
        self._log(f"Starting playbook: {playbook.name}")
        
        try:
            # Execute all actions in sequence
            for action in playbook.actions:
                self._execute_action(action)
            
            status = "SUCCESS"
            error = None
        except Exception as e:
            status = "FAILED"
            error = str(e)
            self._log(f"Playbook execution failed: {error}", level="ERROR")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "status": status,
            "error": error,
            "duration_seconds": duration,
            "execution_log": self.execution_log,
            "context": self.context
        }
    
    def _execute_action(self, action: Action):
        """Execute a single action"""
        self._log(f"Executing action: {action.id} (type: {action.type})")
        
        # Handle different action types
        if action.type == "log":
            self._action_log(action)
        elif action.type == "python_code":
            self._action_python_code(action)
        elif action.type == "condition":
            self._action_condition(action)
        elif action.type == "set_variable":
            self._action_set_variable(action)
        elif action.type == "api_call":
            self._action_api_call(action)
        else:
            raise ValueError(f"Unknown action type: {action.type}")
    
    def _action_log(self, action: Action):
        """Log action - prints a message"""
        message = action.parameters.get('message', '')
        message = self._resolve_variables(message)
        self._log(f"LOG: {message}", level="INFO")
    
    def _action_python_code(self, action: Action):
        """Execute Python code action"""
        code = action.parameters.get('code', '')
        
        # Create a safe execution environment with context variables
        exec_globals = {'__builtins__': __builtins__}
        exec_globals.update(self.context)
        
        # Execute the code
        exec(code, exec_globals)
        
        # If there's a return variable, capture it
        if action.output_variable and 'result' in exec_globals:
            self.context[action.output_variable] = exec_globals['result']
            self._log(f"Stored result in variable: {action.output_variable}")
    
    def _action_condition(self, action: Action):
        """Execute conditional action"""
        condition = self._resolve_variables(action.condition) # type: ignore
        
        # Evaluate condition
        result = eval(condition, {"__builtins__": {}}, self.context)
        self._log(f"Condition '{condition}' evaluated to: {result}")
        
        # Execute appropriate branch
        if result and action.if_true:
            for sub_action in action.if_true:
                self._execute_action(sub_action)
        elif not result and action.if_false:
            for sub_action in action.if_false:
                self._execute_action(sub_action)
    
    def _action_set_variable(self, action: Action):
        """Set a variable in the context"""
        var_name = action.parameters.get('name')
        var_value = action.parameters.get('value')
        var_value = self._resolve_variables(var_value) # type: ignore
        
        self.context[var_name] = var_value # type: ignore
        self._log(f"Set variable '{var_name}' = {var_value}")
    
    def _action_api_call(self, action: Action):
        """Execute an API call action"""
        if not self.integration_manager:
            raise ValueError("Integration manager not configured")
        
        integration = action.parameters.get('integration')
        method = action.parameters.get('method')
        params = action.parameters.get('parameters', {})
        
        # Resolve variables in parameters
        resolved_params = {}
        for key, value in params.items():
            resolved_params[key] = self._resolve_variables(value)
        
        self._log(f"Calling {integration}.{method} with params: {resolved_params}")
        
        # Execute the API call
        result = self.integration_manager.execute_action(integration, method, resolved_params)
        
        # Store result if output variable specified
        if action.output_variable:
            self.context[action.output_variable] = result
            self._log(f"Stored API result in variable: {action.output_variable}")
        
        return result
    
    def _resolve_variables(self, text: str) -> str:
        """Replace {{variable}} placeholders with actual values"""
        if not isinstance(text, str):
            return text
        
        # Find all {{variable}} patterns
        pattern = r'\{\{([^}]+)\}\}'
        
        def replacer(match):
            var_path = match.group(1).strip()
            value = self._get_nested_value(var_path)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(pattern, replacer, text)
    
    def _get_nested_value(self, path: str) -> Any:
        """Get a value from context using dot notation (e.g., 'inputs.ip_address')"""
        parts = path.split('.')
        value = self.context
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
    
    def _log(self, message: str, level: str = "INFO"):
        """Add entry to execution log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.execution_log.append(log_entry)
        print(f"[{level}] {message}")