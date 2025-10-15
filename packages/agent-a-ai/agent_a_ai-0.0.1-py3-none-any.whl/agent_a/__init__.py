"""
Agent A - Workflow automation package.

Command-line tools:
    a      - Main agent entry point
    adiff  - Run diff command
    lwc    - Run lwc command
"""

__version__ = "0.0.1"

# Import main functions for programmatic use
from agent_a.agent import main, run_diff_command_entry_point, run_lwc_command_entry_point

__all__ = [
    "main",
    "run_diff_command_entry_point", 
    "run_lwc_command_entry_point"
]