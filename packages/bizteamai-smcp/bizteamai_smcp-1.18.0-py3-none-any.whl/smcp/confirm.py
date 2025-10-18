"""
Destructive action confirmation queue and approval system.
"""

import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


class PendingApproval(Exception):
    """Raised when an action is queued for approval."""
    pass


class ActionQueue:
    """Manages queued actions awaiting approval."""
    
    def __init__(self, queue_file: Optional[str] = None):
        """
        Initialize the action queue.
        
        Args:
            queue_file: Path to the queue file (defaults to temp file)
        """
        self.queue_file = Path(queue_file or "/tmp/smcp_queue.json")
        self._ensure_queue_file()
    
    def _ensure_queue_file(self) -> None:
        """Ensure the queue file exists."""
        if not self.queue_file.exists():
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_queue([])
    
    def _load_queue(self) -> List[Dict[str, Any]]:
        """Load the current queue from disk."""
        try:
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_queue(self, queue: List[Dict[str, Any]]) -> None:
        """Save the queue to disk."""
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2, default=str)
    
    def add_action(self, action_id: str, function: Callable, args: Tuple, kwargs: Dict[str, Any]) -> None:
        """
        Add an action to the approval queue.
        
        Args:
            action_id: Unique identifier for the action
            function: Function to be executed
            args: Function arguments
            kwargs: Function keyword arguments
        """
        queue = self._load_queue()
        
        action = {
            "id": action_id,
            "function_name": function.__name__,
            "module": function.__module__,
            "args": args,
            "kwargs": kwargs,
            "timestamp": time.time(),
            "status": "pending"
        }
        
        queue.append(action)
        self._save_queue(queue)
    
    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get all pending actions."""
        queue = self._load_queue()
        return [action for action in queue if action["status"] == "pending"]
    
    def approve_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """
        Approve an action for execution.
        
        Args:
            action_id: ID of the action to approve
            
        Returns:
            The approved action data, or None if not found
        """
        queue = self._load_queue()
        
        for action in queue:
            if action["id"] == action_id and action["status"] == "pending":
                action["status"] = "approved"
                action["approved_at"] = time.time()
                self._save_queue(queue)
                return action
        
        return None
    
    def reject_action(self, action_id: str) -> bool:
        """
        Reject an action.
        
        Args:
            action_id: ID of the action to reject
            
        Returns:
            True if the action was found and rejected
        """
        queue = self._load_queue()
        
        for action in queue:
            if action["id"] == action_id and action["status"] == "pending":
                action["status"] = "rejected"
                action["rejected_at"] = time.time()
                self._save_queue(queue)
                return True
        
        return False
    
    def cleanup_old_actions(self, max_age_hours: int = 24) -> int:
        """
        Remove old actions from the queue.
        
        Args:
            max_age_hours: Maximum age in hours before removal
            
        Returns:
            Number of actions removed
        """
        queue = self._load_queue()
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        old_count = len(queue)
        queue = [action for action in queue if action["timestamp"] > cutoff_time]
        new_count = len(queue)
        
        if old_count != new_count:
            self._save_queue(queue)
        
        return old_count - new_count


# Global action queue instance
_action_queue = None


def get_action_queue(cfg: Dict[str, Any]) -> ActionQueue:
    """Get or create the global action queue."""
    global _action_queue
    if _action_queue is None:
        queue_file = cfg.get("QUEUE_FILE")
        _action_queue = ActionQueue(queue_file)
    return _action_queue


def maybe_queue(function: Callable, args: Tuple, kwargs: Dict[str, Any], cfg: Dict[str, Any]) -> bool:
    """
    Queue an action for approval if confirmation is required.
    
    Args:
        function: Function to potentially queue
        args: Function arguments
        kwargs: Function keyword arguments
        cfg: Configuration dictionary
        
    Returns:
        True if the action was queued (requiring approval)
        False if the action should proceed immediately
    """
    # Check if confirmation is enabled globally
    if not cfg.get("CONFIRMATION_ENABLED", True):
        return False
    
    # Generate unique action ID
    action_id = str(uuid.uuid4())
    
    # Add to queue
    queue = get_action_queue(cfg)
    queue.add_action(action_id, function, args, kwargs)
    
    # Store action ID for potential approval
    cfg["_last_action_id"] = action_id
    
    return True


def execute_approved_action(action_id: str, cfg: Dict[str, Any]) -> Any:
    """
    Execute a previously approved action.
    
    Args:
        action_id: ID of the action to execute
        cfg: Configuration dictionary
        
    Returns:
        Result of the executed function
        
    Raises:
        ValueError: If the action is not found or not approved
    """
    queue = get_action_queue(cfg)
    action_queue_data = queue._load_queue()
    
    # Find the action
    action = None
    for a in action_queue_data:
        if a["id"] == action_id:
            action = a
            break
    
    if not action:
        raise ValueError(f"Action {action_id} not found")
    
    if action["status"] != "approved":
        raise ValueError(f"Action {action_id} is not approved")
    
    # Import and execute the function
    # Note: This is a simplified version - in practice, you'd need
    # to properly reconstruct the function from module/name
    function_name = action["function_name"]
    args = tuple(action["args"])
    kwargs = action["kwargs"]
    
    # This would need to be implemented based on your specific requirements
    # for function reconstruction and execution
    raise NotImplementedError("Function execution from queue not implemented")


def list_pending_actions(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    List all pending actions.
    
    Args:
        cfg: Configuration dictionary
        
    Returns:
        List of pending action dictionaries
    """
    queue = get_action_queue(cfg)
    return queue.get_pending_actions()


def format_action_summary(action: Dict[str, Any]) -> str:
    """
    Format an action for display.
    
    Args:
        action: Action dictionary
        
    Returns:
        Human-readable action summary
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(action["timestamp"]))
    return (
        f"ID: {action['id']}\n"
        f"Function: {action['function_name']}\n"
        f"Time: {timestamp}\n"
        f"Args: {action['args']}\n"
        f"Kwargs: {action['kwargs']}\n"
        f"Status: {action['status']}"
    )
