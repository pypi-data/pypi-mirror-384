
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
import os
import json
import glob
import time
import random
import re
import shutil
import subprocess
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone

try:
    from importlib import resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

from agent_a import install_upgrade
from agent_a.args import parse_args
from agent_a.utils import get_file_hash, discover_mimetype, update_status
from agent_a.providers import get_router
from agent_a.providers.base import BaseProvider, FileObject
from agent_a.config import load_raw_config, load_config
from agent_a.workflows import WorkflowManager

FILE_CACHE_PATH = ".agent_a/file_cache.json"

def generate_session_hash():
    """Generate a simple session-unique hash for content delimiting."""
    timestamp = int(time.time())
    suffix = ''.join(random.choices('0123456789abcdef', k=4))
    return f"HASH_{timestamp}_{suffix}"

def parse_hash_delimited_response(raw_text, hash_delimiter):
    """
    Parse hash-delimited agent response into summary and file changes.

    Args:
        raw_text: Raw response text from the agent
        hash_delimiter: The hash string used to delimit content sections

    Returns:
        dict with 'summary_of_changes' and 'files_to_change'
    """
    result = {
        'summary_of_changes': '',
        'files_to_change': []
    }

    # Escape special regex characters in hash_delimiter
    escaped_hash = re.escape(hash_delimiter)

    # Extract summary section
    summary_pattern = f"SUMMARY.*?{escaped_hash}(.*?){escaped_hash}"
    summary_match = re.search(summary_pattern, raw_text, re.DOTALL | re.IGNORECASE)
    if summary_match:
        result['summary_of_changes'] = summary_match.group(1).strip()
    else:
        result['summary_of_changes'] = "No summary provided."

    # Extract file sections
    file_pattern = (
        rf"file_path:\s*(.+?)\s+"
        rf"file_content:\s*{escaped_hash}(.*?){escaped_hash}"
    )
    file_matches = re.finditer(file_pattern, raw_text, re.DOTALL)

    for match in file_matches:
        file_path = match.group(1).strip()
        file_content = match.group(2)
        result['files_to_change'].append({
            'file_path': file_path,
            'new_content': file_content
        })

    return result

def load_file_cache():
    """Loads the file cache from disk."""
    if not os.path.exists(FILE_CACHE_PATH):
        return {}
    try:
        with open(FILE_CACHE_PATH, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        print(f"Warning: Could not read file cache from {FILE_CACHE_PATH}", file=sys.stderr)
        return {}

def save_file_cache(cache_data):
    """Saves the file cache to disk."""
    try:
        path = Path(FILE_CACHE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(FILE_CACHE_PATH, 'w') as f:
            json.dump(cache_data, f, indent=4)
    except IOError:
        print(f"Warning: Could not save file cache to {FILE_CACHE_PATH}", file=sys.stderr)


def get_response_and_update_history(provider: BaseProvider, 
                                    model_name: str, 
                                    prompt: str, 
                                    history: list, 
                                    uploaded_file_objects: list = None):
    """
    Performs a streaming query with optional files, updates the history, and returns streamed chunks.
    Now handles both Gemini-style and Claude-style file objects.
    """
    full_response_text = ""
    
    # Build user parts - files first (for Claude), then text
    user_parts = []
    
    if uploaded_file_objects:
        for file_obj_info in uploaded_file_objects:
            file_obj = file_obj_info["file_object"]
            # Add FileObject directly - provider will handle conversion
            user_parts.append(file_obj)
    
    # Add text prompt last (after files)
    user_parts.append({'text': prompt})
    
    current_user_content = {'role': 'user', 'parts': user_parts}
    conversation = history + [current_user_content]
        
    for chunk_text in provider.generate_content_stream(model_name, conversation):
        full_response_text += chunk_text
        yield chunk_text
    
    history.append(current_user_content)
    history.append({'role': 'model', 'parts': [{'text': full_response_text}]})

def get_coding_response(provider: BaseProvider,
                        model_name: str,
                        prompt: str,
                        reference_file_objects: list,
                        coding_file_objects: list) -> Optional[str]:
    """
    Sends files and a prompt to the model using batched streaming,
    returning the complete text response.
    """
    try:
        # Build contents list - text prompt first, then file objects
        contents = [{'text': prompt}]

        # Add reference files
        if reference_file_objects:
            for file_obj_info in reference_file_objects:
                file_obj = file_obj_info["file_object"]
                contents.append(file_obj)

        # Add coding files
        if coding_file_objects:
            for file_obj_info in coding_file_objects:
                file_obj = file_obj_info["file_object"]
                contents.append(file_obj)

        raw_text = provider.generate_content_stream_batched(
            model_name=model_name,
            contents=contents,
        )

        return raw_text

    except Exception as e:
        print(f"An error occurred during coding response generation: {e}",
              file=sys.stderr)
        return None

def run_diff_command_entry_point():
    """Entry point for the 'adiff' script."""
    run_diff_command(color=True)

def run_lwc_command_entry_point():
    """Entry point for the 'lwc' script. Finds and executes the script."""
    try:
        # The script is package data. We need to get a real path to it.
        # It's located in agent/files/scripts/lwc
        lwc_script_ref = pkg_resources.files('agent_a.files.scripts').joinpath('lwc')
        with pkg_resources.as_file(lwc_script_ref) as lwc_script_path:
            # Ensure the script is executable
            if not os.access(lwc_script_path, os.X_OK):
                os.chmod(lwc_script_path, 0o755)
            
            # Pass any command-line arguments to the script
            result = subprocess.run([lwc_script_path] + sys.argv[1:], check=False)
            sys.exit(result.returncode)
    except (ModuleNotFoundError, FileNotFoundError):
        # This could happen if importlib.resources can't find the file/module
        print("Error: 'lwc' script not found within the package.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while trying to run 'lwc': {e}", file=sys.stderr)
        sys.exit(1)

def run_diff_command(color=False):
    """Runs git diff on the last set of changed files."""
    changes_file_path = Path(".agent_a/latest_changes.json")
    if not changes_file_path.exists():
        print("No changes have been logged yet.", file=sys.stderr)
        return

    try:
        with open(changes_file_path, 'r', encoding='utf-8') as f:
            changelog_data = json.load(f)
        
        changelog = changelog_data.get("changelog")
        if not changelog:
            print("Changelog is empty.", file=sys.stderr)
            return

        last_change = changelog[-1]
        changed_files = last_change.get("files", [])
        
        if not changed_files:
            print("Last change entry has no files.", file=sys.stderr)
            return

        all_diffs = []
        for change in changed_files:
            file_path = change.get("file_path")
            backup_path = change.get("backup_path")
            
            if not file_path or not backup_path:
                print(f"Warning: Incomplete change record found: {change}", file=sys.stderr)
                continue
            
            diff_cmd = ["git", "--no-pager", "diff", "--no-index", "--", backup_path, file_path]
            try:
                result = subprocess.run(diff_cmd, text=True, capture_output=True)
                if result.stderr:
                    print(f"Error running git diff for {file_path}:\n{result.stderr}", file=sys.stderr)
                else:
                    diff_output = result.stdout
                    if color:
                        colored_lines = []
                        for line in diff_output.splitlines():
                            if line.startswith('+'):
                                colored_lines.append(f"\033[92m{line}\033[0m")
                            elif line.startswith('-'):
                                colored_lines.append(f"\033[91m{line}\033[0m")
                            elif line.startswith('@'):
                                colored_lines.append(f"\033[96m{line}\033[0m")
                            else:
                                colored_lines.append(line)
                        all_diffs.append("\n".join(colored_lines))
                    else:
                        all_diffs.append(diff_output)

            except FileNotFoundError:
                print("Error: 'git' command not found. Please ensure git is installed and in your PATH.", file=sys.stderr)
                return
            except Exception as e:
                print(f"Error running diff for '{file_path}': {e}", file=sys.stderr)
        
        if all_diffs:
            print("\n".join(all_diffs), end='')
            print()

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing changelog file: {e}", file=sys.stderr)

def run_undo_command():
    """Reverts the last set of changes logged in latest_changes.json."""
    changes_file_path = Path(".agent_a/latest_changes.json")
    if not changes_file_path.exists() or changes_file_path.stat().st_size == 0:
        print("No changes have been logged yet. Nothing to undo.", file=sys.stderr)
        return

    try:
        with open(changes_file_path, 'r', encoding='utf-8') as f:
            changelog_data = json.load(f)
        
        changelog = changelog_data.get("changelog")
        if not changelog:
            print("Changelog is empty. Nothing to undo.", file=sys.stderr)
            return

        last_change = changelog.pop()
        files_to_revert = last_change.get("files", [])
        
        if not files_to_revert:
            print("Last change entry has no files. Nothing to undo.", file=sys.stderr)
            with open(changes_file_path, 'w', encoding='utf-8') as f:
                json.dump(changelog_data, f, indent=2)
            return

        user_approval = input("\nDo you want to undo the latest changes? (y/n): ").lower()
        
        if user_approval != 'y': 
            print("Undo aborted")
            return

        print("Attempting to revert the following changes:")
        success_count = 0
        failure_count = 0
        for change in files_to_revert:
            file_path_str = change.get("file_path")
            backup_path_str = change.get("backup_path")
            
            if not file_path_str or not backup_path_str:
                print(f"Warning: Incomplete change record found, cannot revert: {change}", file=sys.stderr)
                failure_count += 1
                continue

            backup_path = Path(backup_path_str)
            if not backup_path.exists():
                print(f"Error: Backup file '{backup_path_str}' not found for '{file_path_str}'. Cannot revert.", file=sys.stderr)
                failure_count += 1
                continue
            
            try:
                shutil.move(backup_path_str, file_path_str)
                print(f"  - Reverted '{file_path_str}' from '{backup_path_str}'")
                success_count += 1
            except Exception as e:
                print(f"Error reverting '{file_path_str}' from '{backup_path_str}': {e}", file=sys.stderr)
                failure_count += 1

        with open(changes_file_path, 'w', encoding='utf-8') as f:
            json.dump(changelog_data, f, indent=2)
        
        print("\nUndo operation summary:")
        print(f"  Successfully reverted: {success_count} file(s)")
        if failure_count > 0:
            print(f"  Failed to revert: {failure_count} file(s). Please check errors above.", file=sys.stderr)
        print(f"Changes log updated at '{changes_file_path}'.")

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing changelog file: {e}", file=sys.stderr)
    except IndexError:
        print("Changelog is empty. Nothing to undo.", file=sys.stderr)


def format_file_list(file_objects: list) -> str:
    """
    Formats a list of file objects for display in prompts.
    
    Args:
        file_objects: List of dicts with 'disk_path' and 'file_object'
    
    Returns:
        Formatted string listing the files
    """
    if not file_objects:
        return "None"
    
    lines = []
    for i, item in enumerate(file_objects, 1):
        file_obj = item['file_object']
        lines.append(f"{i}. {item['disk_path']} (type: {file_obj.mime_type})")
    
    return "\n".join(lines)


def main():
    install_upgrade.check_and_run()
    plain_text_guide = """Please use the following prompt template for plain text output:

ALL HEADERS MUST BE IN FULL CAPS.

NO BOLD OR CODE FORMATTING: Do not use asterisks, backticks, or any other markup.

subheadings:

  Subheadings are lowercase.

    Content following a subheading must be indented by two spaces.

      Headings and subheading should have leave an empty line on the prior line

MAXIMUM LINE WIDTH: All lines must not exceed 80 characters.

numbered lists:
  1. Start with a number followed by a period (e.g., '1.', '2.').
  2. Each item must be on a new line.

bullet point lists:
  - Use a hyphen followed by a space for each item (e.g., '- Item').
  - Each item must be on a new line."""
    
    args = parse_args()

    # --- Workflow Integration ---
    raw_config = load_raw_config()
    workflow_manager = WorkflowManager(raw_config)
    
    command = args.get("command")

    if command in ["workflow", "bundle"]:
        workflow_manager.handle_command(args)
        return
    # --- End Workflow Integration ---

    if command == "diff":
        run_diff_command(color=args.get("color", False))
        return
    elif command == "undo":
        run_undo_command()
        return

    # --- Get Context from Workflow (if any) ---
    workflow_context = workflow_manager.get_workflow_context()
    wf_ref_files, wf_edit_files = [], []
    
    prompt = args["prompt"]
    user_tag = args.get("user_tag")

    # --- Auto-run feature ---
    if prompt.lower() in ["auto", "*"]:
        if not workflow_context:
            print("Error: Auto-run command can only be used when a workflow "
                  "bundle is active.", file=sys.stderr)
            sys.exit(1)
        
        auto_prompt = workflow_context.get("auto_prompt")
        current_step_name = workflow_context.get("current_step_name",
                                                 "Unknown")

        if not auto_prompt:
            print(f"Error: The current workflow step '{current_step_name}' "
                  "does not have an 'auto_prompt' defined.",
                  file=sys.stderr)
            sys.exit(1)
        
        print(f"\n>> Auto-run for step '{current_step_name}' activated. "
              "Using pre-configured prompt.")
        prompt = auto_prompt # Overwrite the prompt
    # --- End Auto-run ---

    if workflow_context:
        print(f"\n>> {workflow_context['display_status']}\n")
        if workflow_context.get('user_tag'):
            user_tag = workflow_context['user_tag'] # Override
        wf_ref_files = workflow_context.get('reference_files', [])
        wf_edit_files = workflow_context.get('editable_files', [])
    
    # Load config *after* resolving user_tag from workflow/CLI
    ai_str, mode, additional_context, additional_references, prompt_manager = load_config(
        raw_config,
        user_tag,
        args.get("ai_str"),
        args.get("mode_str")
    )
    
    history_file = args["history_file"]
    keep_history = args["keep_history"]
    editable_files_str = args["editable_files_str"]

    # Validate mode requirements
    has_editable_files = bool(editable_files_str) or bool(wf_edit_files)
    if not prompt_manager.validate_mode_requirements(mode, has_editable_files):
        mode_config = prompt_manager.get_mode_config(mode)
        if mode_config and mode_config.get('requires_editable_files'):
            print(f"Error: Mode '{mode}' requires editable files. Use -e flag or a workflow to specify files.", 
                  file=sys.stderr)
            sys.exit(1)

    # Parse AI string
    try:
        router_name, provider_name, model_name = ai_str.split(':', 2)
    except ValueError:
        print(f"Error: Invalid AI string format: '{ai_str}'. Expected 'router:provider:model'.", file=sys.stderr)
        sys.exit(1)

    try:
        provider = get_router(router_name)
        file_cache = load_file_cache()
        provider_cache = file_cache.setdefault(provider.name, {})
        
        # --- Collect and upload files ---
        # 1. Collect files from CLI arguments and config
        cli_reference_files = []
        
        if additional_references:
            temp_paths = []
            for path_pattern in additional_references:
                temp_paths.extend(glob.glob(path_pattern, recursive=True))
            cli_reference_files.extend(temp_paths)
        
        if args.get("add_references_str"):
            path_patterns = args["add_references_str"].strip('"').split(os.pathsep)
            temp_paths = []
            for path_pattern in path_patterns:
                temp_paths.extend(glob.glob(path_pattern, recursive=True))
            cli_reference_files.extend(temp_paths)
        
        if args.get("references_str"):
            path_patterns = args["references_str"].strip('"').split(os.pathsep)
            cli_reference_files = []  # -r overrides other CLI/config refs
            for path_pattern in path_patterns:
                cli_reference_files.extend(glob.glob(path_pattern, recursive=True))
        
        cli_editable_files = []
        if editable_files_str:
            path_patterns = editable_files_str.strip('"').split(os.pathsep)
            for pattern in path_patterns:
                is_pattern = any(c in pattern for c in '*?[')
                if not is_pattern and not Path(pattern).exists():
                    print(f"Error: The specified file or directory does not exist: {pattern}", file=sys.stderr)
                    sys.exit(1)
            
            temp_paths = []
            for path_pattern in path_patterns:
                temp_paths.extend(glob.glob(path_pattern, recursive=True))
            cli_editable_files.extend(temp_paths)

        # 2. Combine with workflow files and de-duplicate
        reference_file_paths = sorted(list(set(wf_ref_files + cli_reference_files)))
        editable_file_paths = sorted(list(set(wf_edit_files + cli_editable_files)))

        # Upload reference files
        uploaded_reference_files = []
        if reference_file_paths:
            print(f"Found {len(reference_file_paths)} reference file(s):")
            for file_path in reference_file_paths:
                uploaded_file = provider.handle_file_upload(file_path, provider_cache)
                if uploaded_file:
                    uploaded_reference_files.append({"disk_path": file_path, "file_object": uploaded_file})

        # Upload editable files
        uploaded_editable_files = []
        if editable_file_paths:
            print(f"Found {len(editable_file_paths)} editable file(s):")
            for file_path in editable_file_paths:
                uploaded_file = provider.handle_file_upload(file_path, provider_cache)
                if uploaded_file:
                    uploaded_editable_files.append({"disk_path": file_path, "file_object": uploaded_file})

        # Generate session hash for content delimiting (used in coding mode)
        session_hash = generate_session_hash()

        # Get prompt template for this mode and AI
        template = prompt_manager.get_prompt_template(mode, ai_str)
        if not template:
            print(f"Error: No prompt template found for mode '{mode}' and AI '{ai_str}'",
                  file=sys.stderr)
            sys.exit(1)

        # Format prompt with template variables
        formatted_prompt = prompt_manager.format_prompt(
            template,
            prompt=prompt,
            context=additional_context if additional_context else "None",
            reference_files=format_file_list(uploaded_reference_files),
            editable_files=format_file_list(uploaded_editable_files),
            plain_text_guide=plain_text_guide,
            model_name=model_name,
            router=router_name,
            provider=provider_name,
            escape_hash=session_hash
        )
        
        # Determine execution mode based on mode configuration
        mode_config = prompt_manager.get_mode_config(mode)
        requires_structured_output = mode_config.get('requires_editable_files', False)
        
        if requires_structured_output and uploaded_editable_files:
            # Coding/editing mode - use non-streaming for hash-delimited output
            print(f"\n--- {mode.title()} Mode Activated ({model_name}) ---")

            # Save prompt to history if requested
            if history_file:
                history_parts = [{'text': formatted_prompt}]
                coding_history = [{'role': 'user', 'parts': history_parts}]
                try:
                    with open(history_file, 'w', encoding='utf-8') as f:
                        json.dump(coding_history, f, indent=4)
                    print(f"Prompt saved to history file '{history_file}'.", file=sys.stderr)
                except IOError as e:
                    print(f"Error saving prompt to history file: {e}", file=sys.stderr)

            start_time = time.time()
            raw_text = get_coding_response(
                provider, model_name, formatted_prompt,
                uploaded_reference_files, uploaded_editable_files
            )
            end_time = time.time()
            elapsed_time = end_time - start_time

            if raw_text:
                response_data = parse_hash_delimited_response(raw_text,
                                                              session_hash)
            else:
                response_data = None

            if response_data and 'files_to_change' in response_data:
                summary = response_data.get("summary_of_changes", "No summary provided.")
                modifications = response_data['files_to_change']
                
                print("\n--- Model's Summary of Changes ---")
                print(summary)
                print(f"\n--- {elapsed_time:.2f}s --------------------------")

                if not modifications:
                    print("The model did not suggest any file modifications.")
                    print(raw_text)
                    return

                print("\nThe model suggested modifications for the following files:")
                for mod in modifications:
                    print(f" - {mod.get('file_path', 'N/A')}")

                user_approval = input("\nDo you want to apply these changes? (y/n): ").lower()
                if user_approval == 'y':
                    applied_changes = []
                    backup_header_printed = False
                    for mod in modifications:
                        file_to_modify = mod.get('file_path')
                        new_content = mod.get('new_content')
                        if not file_to_modify or new_content is None:
                            print(f"Warning: Skipping invalid modification object: {mod}", file=sys.stderr)
                            continue

                        if os.path.exists(file_to_modify):
                            if not backup_header_printed:
                                print("\nBackups created:")
                                backup_header_printed = True

                            timestamp = int(time.time())
                            backup_base_dir = Path(".agent_a/backups")
                            relative_file_path = Path(file_to_modify)
                            full_backup_path = backup_base_dir / f"{relative_file_path}.{timestamp}"
                            full_backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(file_to_modify, full_backup_path)
                            
                            print(f"Applying changes to '{file_to_modify}'...")
                            with open(file_to_modify, 'w', encoding='utf-8') as f:
                                f.write(new_content)

                            applied_changes.append({
                                "file_path": file_to_modify,
                                "backup_path": str(full_backup_path)
                            })
                        else:
                            print(f"Warning: File '{file_to_modify}' not found. Cannot apply changes.", file=sys.stderr)
                    
                    if applied_changes:
                        print("All changes applied successfully.")
                        agent_a_dir = Path(".agent_a")
                        agent_a_dir.mkdir(exist_ok=True)
                        changes_file_path = agent_a_dir / "latest_changes.json"
                        
                        changelog = {"changelog": []}
                        if changes_file_path.exists() and changes_file_path.stat().st_size > 0:
                            try:
                                with open(changes_file_path, 'r', encoding='utf-8') as f:
                                    existing_data = json.load(f)
                                    if isinstance(existing_data, dict) and isinstance(existing_data.get('changelog'), list):
                                        changelog = existing_data
                                    else:
                                        print(f"Warning: '{changes_file_path}' has incorrect format. Resetting.", file=sys.stderr)
                            except (IOError, json.JSONDecodeError) as e:
                                print(f"Warning: Could not read or parse '{changes_file_path}'. Starting new changelog. Error: {e}", file=sys.stderr)

                        new_log_entry = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "summary": summary,
                            "files": applied_changes
                        }
                        changelog["changelog"].append(new_log_entry)
                        
                        try:
                            with open(changes_file_path, 'w', encoding='utf-8') as f:
                                json.dump(changelog, f, indent=2)
                            print(f"Changes logged to '{changes_file_path}'.", file=sys.stderr)
                        except IOError as e:
                            print(f"Error writing changes to {changes_file_path}: {e}", file=sys.stderr)

                else:
                    print("Modifications discarded.")
            else:
                print("Failed to get a valid modification response from the model.")
                # if debug logging
                print(f"formatted_prompt: {formatted_prompt}")

        else:
            # General/streaming mode
            chat_history = []
            if history_file:
                if keep_history and os.path.exists(history_file):
                    try:
                        with open(history_file, 'r', encoding='utf-8') as f:
                            chat_history = json.load(f)
                        print(f"Loaded chat history from '{history_file}'.", file=sys.stderr)
                    except (IOError, json.JSONDecodeError) as e:
                        print(f"Error loading chat history from file: {e}", file=sys.stderr)
                elif os.path.exists(history_file):
                    try:
                        with open(history_file, 'w', encoding='utf-8') as f:
                            json.dump([], f)
                        print(f"Cleared existing chat history in '{history_file}'.", file=sys.stderr)
                    except IOError as e:
                         print(f"Error clearing history file: {e}", file=sys.stderr)

            print(f"--- {model_name} ({mode} mode, streaming) ---")
            
            start_time = time.time()
            for text_chunk in get_response_and_update_history(
                provider, model_name, formatted_prompt, 
                chat_history, uploaded_reference_files
            ):
                print(text_chunk, end="", flush=True)
            end_time = time.time()
            elapsed_time = end_time - start_time

            print(f"\n--- {elapsed_time:.2f}s ---------------")

            if history_file:
                try:
                    with open(history_file, 'w', encoding='utf-8') as f:
                        json.dump(chat_history, f, indent=4)
                    print(f"Chat history saved to '{history_file}'.", file=sys.stderr)
                except IOError as e:
                    print(f"Error saving chat history to file: {e}", file=sys.stderr)
        
        save_file_cache(file_cache)

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
