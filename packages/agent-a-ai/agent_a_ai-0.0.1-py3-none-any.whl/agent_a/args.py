
# Copyright (C) 2025 The Agent A Open Source Project
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

def _print_bundle_usage():
    print("Usage: a bundle|b [subcommand] [options]", file=sys.stderr)
    print("\nManages context bundles (workflow instances).", file=sys.stderr)
    print("\nSubcommands:", file=sys.stderr)
    print("  (no subcommand)            Display current status of the active bundle", file=sys.stderr)
    print("  new <bundle> <wf>          Create a new bundle from a workflow", file=sys.stderr)
    print("  set <bundle>               Set the active bundle", file=sys.stderr)
    print("  list                       List all local bundles", file=sys.stderr)
    print("  next | n                   Move to the next step in the active bundle", file=sys.stderr)
    print("  prev | p                   Move to the previous step", file=sys.stderr)
    print("  exit                       Exit the current bundle session", file=sys.stderr)
    print("  select                     Open a TUI to manage file permissions", file=sys.stderr)
    print("  add file \"<pattern>\" --perms \"<...>\": Add a file pattern (use quotes)", file=sys.stderr)
    sys.exit(1)

def _print_workflow_usage():
    print("Usage: a workflow|wf <subcommand>", file=sys.stderr)
    print("\nManages workflow definitions.", file=sys.stderr)
    print("\nSubcommands:", file=sys.stderr)
    print("  list              List available workflows from config files", file=sys.stderr)
    sys.exit(1)

def parse_args():
    """
    Parses command line arguments for the agent.
    """
    if len(sys.argv) < 2:
        print(f"Usage: a <prompt|command> [options]", file=sys.stderr)
        print("Commands: diff [--color|-c], undo, workflow, bundle", file=sys.stderr)
        sys.exit(1)
    
    # --- Handle Workflow & Bundle Commands ---
    if sys.argv[1] in ['workflow', 'wf']:
        argv = sys.argv[2:]
        if len(argv) == 1 and argv[0] == 'list':
            return {'command': 'workflow', 'subcommand': 'list_workflows'}
        _print_workflow_usage()

    if sys.argv[1] in ['bundle', 'b']:
        argv = sys.argv[2:]
        if not argv: # 'a bundle'
            return {'command': 'bundle', 'subcommand': 'status'}

        subcommand = argv[0]
        if subcommand == 'new':
            if len(argv) != 3: _print_bundle_usage()
            return {'command': 'bundle', 'subcommand': 'new', 'bundle_name': argv[1], 'workflow_name': argv[2]}
        elif subcommand == 'set':
            if len(argv) != 2: _print_bundle_usage()
            return {'command': 'bundle', 'subcommand': 'set', 'bundle_name': argv[1]}
        elif subcommand == 'list':
            if len(argv) != 1: _print_bundle_usage()
            return {'command': 'bundle', 'subcommand': 'list_bundles'}
        elif subcommand in ['next', 'n']:
            return {'command': 'bundle', 'subcommand': 'next'}
        elif subcommand in ['prev', 'p']:
            return {'command': 'bundle', 'subcommand': 'prev'}
        elif subcommand == 'exit':
            return {'command': 'bundle', 'subcommand': 'exit'}
        elif subcommand == 'select':
            if len(argv) != 1: _print_bundle_usage()
            return {'command': 'bundle', 'subcommand': 'select'}
        elif subcommand == 'add' and len(argv) > 1 and argv[1] == 'file':
            try:
                path = argv[2]
                perms_idx = argv.index('--perms')
                perms = argv[perms_idx + 1]
                return {'command': 'bundle', 'subcommand': 'add_file', 'path': path, 'perms': perms}
            except (ValueError, IndexError):
                print("Error: `add file` requires a path and --perms option.", file=sys.stderr)
                _print_bundle_usage()
        _print_bundle_usage()

    # --- Handle Other Commands ---
    if sys.argv[1] == 'diff':
        color_enabled = '-c' in sys.argv or '--color' in sys.argv
        return {"command": "diff", "color": color_enabled}
    
    if sys.argv[1] == 'undo':
        return {"command": "undo"}

    # --- Parse regular prompt arguments ---
    prompt_parts = []
    history_file = None
    keep_history = False
    editable_files_str = None
    mode_str = None
    ai_str = None
    user_tag = None
    references_str = None
    add_references_str = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg in ['--history', '-h']:
            if i + 1 < len(args): history_file = args[i + 1]; i += 1
            else: print("Error: --history/-h flag requires a file path.", file=sys.stderr); sys.exit(1)
        elif arg in ['--keep', '-k']:
            keep_history = True
        elif arg in ['--edit', '-e']:
            if i + 1 < len(args): editable_files_str = args[i + 1]; i += 1
            else: print("Error: --edit/-e flag requires a file path or pattern.", file=sys.stderr); sys.exit(1)
        elif arg in ['--mode', '-mo']:
            if i + 1 < len(args) and not args[i+1].startswith('-'): mode_str = args[i+1]; i += 1
            else: print("Error: --mode/-mo flag requires a mode name.", file=sys.stderr); sys.exit(1)
        elif arg in ['--ai', '-a']:
            if i + 1 < len(args) and not args[i+1].startswith('-'): ai_str = args[i+1]; i += 1
            else: print("Error: --ai/-a flag requires an AI model string.", file=sys.stderr); sys.exit(1)
        elif arg in ['--user-tag', '-u']:
            if i + 1 < len(args) and not args[i+1].startswith('-'): user_tag = args[i+1]; i += 1
            else: print("Error: --user-tag/-u flag requires a tag string.", file=sys.stderr); sys.exit(1)
        elif arg in ['--references', '-r']:
            if i + 1 < len(args) and not args[i+1].startswith('-'): references_str = args[i+1]; i += 1
            else: print("Error: --references/-r flag requires a file path or pattern.", file=sys.stderr); sys.exit(1)
        elif arg in ['--add_references', '-ar']:
            if i + 1 < len(args) and not args[i+1].startswith('-'): add_references_str = args[i+1]; i += 1
            else: print("Error: --add_references/-ar flag requires a file path or pattern.", file=sys.stderr); sys.exit(1)
        elif arg in ['--coding', '-c']:
            print("Warning: --coding/-c is deprecated. Use --edit/-e with --mode coding instead.", file=sys.stderr)
            if i + 1 < len(args):
                editable_files_str = args[i + 1]
                if mode_str is None: mode_str = "coding"
                i += 1
            else: print("Error: --coding/-c flag requires a file path or pattern.", file=sys.stderr); sys.exit(1)
        elif arg in ['--model', '-m']:
            print("Warning: --model/-m is deprecated. Use --ai/-a instead.", file=sys.stderr)
            if i + 1 < len(args) and not args[i+1].startswith('-'): ai_str = args[i+1]; i += 1
            else: print("Error: --model/-m flag requires a model string.", file=sys.stderr); sys.exit(1)
        else:
            prompt_parts.append(arg)
        
        i += 1
    
    prompt = " ".join(prompt_parts)

    if not prompt:
        print("Error: Prompt is missing.", file=sys.stderr)
        print(f"Usage: a <prompt> [options]", file=sys.stderr)
        sys.exit(1)
        
    return {
        "command": "run",
        "prompt": prompt,
        "history_file": history_file,
        "keep_history": keep_history,
        "editable_files_str": editable_files_str,
        "mode_str": mode_str,
        "ai_str": ai_str,
        "user_tag": user_tag,
        "references_str": references_str,
        "add_references_str": add_references_str
    }
