#!/usr/bin/env python3
"""
Action approval tool for SMCP.

Allows administrators to approve or reject queued destructive actions.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from ..confirm import ActionQueue, format_action_summary


def load_config(config_path: Optional[str] = None) -> Dict:
    """Load configuration from file or environment."""
    config = {}
    
    # Try to load from config file
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            if config_file.suffix.lower() in ['.yaml', '.yml'] and YAML_AVAILABLE:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
            elif config_file.suffix.lower() == '.json':
                with open(config_file, 'r') as f:
                    config = json.load(f)
    
    # Override with environment variables
    import os
    env_config = {
        "QUEUE_FILE": os.getenv("SMCP_QUEUE_FILE"),
        "LOG_PATH": os.getenv("SMCP_LOG_PATH"),
    }
    
    # Add non-None environment variables
    for key, value in env_config.items():
        if value is not None:
            config[key] = value
    
    return config


def list_pending_actions(queue: ActionQueue) -> List[Dict]:
    """List all pending actions."""
    return queue.get_pending_actions()


def display_action_details(action: Dict) -> None:
    """Display detailed information about an action."""
    print("=" * 60)
    print(format_action_summary(action))
    print("=" * 60)


def approve_action(queue: ActionQueue, action_id: str) -> bool:
    """Approve an action."""
    action = queue.approve_action(action_id)
    if action:
        print(f"✓ Action {action_id} approved")
        return True
    else:
        print(f"✗ Action {action_id} not found or already processed")
        return False


def reject_action(queue: ActionQueue, action_id: str) -> bool:
    """Reject an action."""
    if queue.reject_action(action_id):
        print(f"✗ Action {action_id} rejected")
        return True
    else:
        print(f"✗ Action {action_id} not found or already processed")
        return False


def interactive_approval(queue: ActionQueue) -> None:
    """Interactive approval mode."""
    print("Interactive approval mode. Type 'help' for commands.")
    
    while True:
        try:
            command = input("\nsmcp-approve> ").strip().lower()
            
            if command in ['quit', 'exit', 'q']:
                break
            elif command == 'help':
                print("Commands:")
                print("  list                    - List all pending actions")
                print("  show <action-id>        - Show action details")
                print("  approve <action-id>     - Approve an action")
                print("  reject <action-id>      - Reject an action")
                print("  cleanup [hours]         - Clean up old actions")
                print("  quit/exit/q             - Exit interactive mode")
            elif command == 'list':
                actions = list_pending_actions(queue)
                if not actions:
                    print("No pending actions")
                else:
                    print(f"\n{len(actions)} pending action(s):")
                    for action in actions:
                        timestamp = time.strftime("%H:%M:%S", time.localtime(action["timestamp"]))
                        print(f"  {action['id'][:8]}... - {action['function_name']} ({timestamp})")
            elif command.startswith('show '):
                action_id = command[5:].strip()
                actions = list_pending_actions(queue)
                action = next((a for a in actions if a['id'].startswith(action_id)), None)
                if action:
                    display_action_details(action)
                else:
                    print(f"Action not found: {action_id}")
            elif command.startswith('approve '):
                action_id = command[8:].strip()
                # Find full action ID from partial
                actions = list_pending_actions(queue)
                action = next((a for a in actions if a['id'].startswith(action_id)), None)
                if action:
                    approve_action(queue, action['id'])
                else:
                    print(f"Action not found: {action_id}")
            elif command.startswith('reject '):
                action_id = command[7:].strip()
                # Find full action ID from partial
                actions = list_pending_actions(queue)
                action = next((a for a in actions if a['id'].startswith(action_id)), None)
                if action:
                    reject_action(queue, action['id'])
                else:
                    print(f"Action not found: {action_id}")
            elif command.startswith('cleanup'):
                parts = command.split()
                hours = int(parts[1]) if len(parts) > 1 else 24
                removed = queue.cleanup_old_actions(hours)
                print(f"Removed {removed} old action(s)")
            else:
                print(f"Unknown command: {command}. Type 'help' for available commands.")
        
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main() -> None:
    """Main entry point for the approve CLI tool."""
    parser = argparse.ArgumentParser(
        description="Approve or reject queued SMCP actions"
    )
    parser.add_argument(
        "action_id",
        nargs="?",
        help="Action ID to approve (if not provided, enters interactive mode)"
    )
    parser.add_argument(
        "--reject", "-r",
        action="store_true",
        help="Reject the action instead of approving it"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all pending actions and exit"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--queue-file",
        help="Path to the action queue file (overrides config)"
    )
    parser.add_argument(
        "--cleanup",
        type=int,
        metavar="HOURS",
        help="Clean up actions older than specified hours"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enter interactive approval mode"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override queue file if specified
    if args.queue_file:
        config["QUEUE_FILE"] = args.queue_file
    
    # Initialize action queue
    queue_file = config.get("QUEUE_FILE", "/tmp/smcp_queue.json")
    queue = ActionQueue(queue_file)
    
    try:
        # Handle cleanup
        if args.cleanup:
            removed = queue.cleanup_old_actions(args.cleanup)
            print(f"Removed {removed} old action(s)")
            return
        
        # Handle list command
        if args.list:
            actions = list_pending_actions(queue)
            if not actions:
                print("No pending actions")
            else:
                print(f"{len(actions)} pending action(s):")
                for action in actions:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", 
                                            time.localtime(action["timestamp"]))
                    print(f"  {action['id']} - {action['function_name']} ({timestamp})")
            return
        
        # Handle interactive mode
        if args.interactive or not args.action_id:
            interactive_approval(queue)
            return
        
        # Handle specific action approval/rejection
        if args.action_id:
            # Find action (support partial IDs)
            actions = list_pending_actions(queue)
            action = next((a for a in actions if a['id'].startswith(args.action_id)), None)
            
            if not action:
                print(f"Action not found: {args.action_id}")
                sys.exit(1)
            
            action_id = action['id']
            
            # Show action details
            display_action_details(action)
            
            if args.reject:
                success = reject_action(queue, action_id)
            else:
                success = approve_action(queue, action_id)
            
            sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
