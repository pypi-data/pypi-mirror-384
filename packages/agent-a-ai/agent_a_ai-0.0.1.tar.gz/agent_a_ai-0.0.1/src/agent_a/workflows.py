
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

import json
import os
import sys
import glob
from pathlib import Path
from agent_a.tui import run_file_selector, _is_glob_pattern
from agent_a.utils import (
    format_file_size,
    format_token_count,
    calculate_file_size,
    estimate_tokens
)
from agent_a.prompts import PromptManager
from agent_a.config import find_by_user_tag

WORKFLOW_STATE_PATH = ".agent_a/workflow_state.json"
BUNDLES_DIR = "bundles/"

class WorkflowManager:
    """Manages context bundles, workflows, and state."""

    def __init__(self, raw_config):
        self.raw_config = raw_config
        self.workflows = raw_config.get('workflows', [])
        self.state = self._load_state()

    def _load_state(self):
        """Loads the global workflow session state."""
        state_path = Path(WORKFLOW_STATE_PATH)
        if not state_path.exists():
            return {"active_bundle_path": None}
        try:
            with state_path.open('r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            print(f"Warning: Could not read workflow state from {WORKFLOW_STATE_PATH}", file=sys.stderr)
            return {"active_bundle_path": None}

    def _save_state(self):
        """Saves the global workflow session state."""
        try:
            path = Path(WORKFLOW_STATE_PATH)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('w') as f:
                json.dump(self.state, f, indent=2)
        except IOError:
            print(f"Warning: Could not save workflow state to {WORKFLOW_STATE_PATH}", file=sys.stderr)

    def _load_bundle_manifest(self, bundle_path):
        """Loads a manifest.json from a bundle directory."""
        manifest_path = Path(bundle_path) / "manifest.json"
        if not manifest_path.exists():
            print(f"Error: Manifest file not found in '{bundle_path}'", file=sys.stderr)
            return None
        try:
            with manifest_path.open('r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            print(f"Error: Could not read or parse manifest in '{bundle_path}'", file=sys.stderr)
            return None

    def _save_bundle_manifest(self, bundle_path, manifest_data):
        """Saves a manifest.json to a bundle directory."""
        manifest_path = Path(bundle_path) / "manifest.json"
        try:
            with manifest_path.open('w') as f:
                json.dump(manifest_data, f, indent=2)
        except IOError:
            print(f"Error: Could not save manifest to '{manifest_path}'", file=sys.stderr)

    def _get_active_bundle_path(self):
        """Gets the active bundle path from state."""
        return self.state.get("active_bundle_path")

    def _get_workflow_def(self, workflow_name):
        """Finds a workflow definition by name."""
        for wf in self.workflows:
            if wf.get('name') == workflow_name:
                return wf
        return None

    def _calculate_step_totals(self, file_list, bundle_path):
        """
        Calculates total size and token count for a list of file paths.
        
        Args:
            file_list: List of file path strings (may include glob patterns)
            bundle_path: Bundle directory path for resolving {BUNDLE_PATH}
            
        Returns:
            Tuple of (total_bytes, total_tokens)
        """
        total_bytes = 0
        counted_files = set()  # Track files we've already counted
        
        for path in file_list:
            resolved_path = path.replace('{BUNDLE_PATH}', bundle_path)
            
            if _is_glob_pattern(resolved_path):
                try:
                    matched_files = glob.glob(resolved_path, recursive=True)
                    for matched_file in matched_files:
                        if Path(matched_file).is_file() and matched_file not in counted_files:
                            total_bytes += calculate_file_size(matched_file)
                            counted_files.add(matched_file)
                except Exception:
                    pass
            else:
                if Path(resolved_path).is_file() and resolved_path not in counted_files:
                    total_bytes += calculate_file_size(resolved_path)
                    counted_files.add(resolved_path)
        
        total_tokens = estimate_tokens(total_bytes)
        return (total_bytes, total_tokens)

    def handle_command(self, args):
        """Dispatches workflow subcommands."""
        subcommand = args.get('subcommand')

        if subcommand == 'status':
            self.show_status()
        elif subcommand == 'new':
            self.new_bundle(args['bundle_name'], args['workflow_name'])
        elif subcommand == 'set':
            self.set_active_bundle(args['bundle_name'])
        elif subcommand == 'next':
            self.next_step()
        elif subcommand == 'prev':
            self.prev_step()
        elif subcommand == 'exit':
            self.exit_workflow()
        elif subcommand == 'select':
            self.select_files()
        elif subcommand == 'add_file':
            self.add_file(args['path'], args['perms'])
        elif subcommand == 'list_workflows':
            self.list_workflows()
        elif subcommand == 'list_bundles':
            self.list_bundles()
        else:
            command = args.get('command', '')
            print(f"Unknown command: {command} {subcommand}", file=sys.stderr)
    
    def _process_auto_creates_for_step(self, manifest, workflow_def):
        """Checks for and creates files defined in the current step's auto_creates."""
        current_step_name = manifest['current_step']
        step_obj = next((s for s in workflow_def.get('steps', []) if s['name'] == current_step_name), None)

        if not step_obj or 'auto_creates' not in step_obj:
            return

        manifest_changed = False
        bundle_path = manifest['bundle_path']
        manifest_paths = {f['path'] for f in manifest.get('files', [])}

        for item in step_obj.get('auto_creates', []):
            path_template = item.get("path")
            if not path_template:
                continue

            resolved_path_str = path_template.replace("{BUNDLE_PATH}", bundle_path)
            resolved_path = Path(resolved_path_str)

            if not resolved_path.exists():
                try:
                    resolved_path.parent.mkdir(parents=True, exist_ok=True)
                    resolved_path.touch()
                    print(f"  - Auto-created file: {resolved_path_str}")
                except OSError as e:
                    print(f"  - Error auto-creating file '{resolved_path_str}': {e}", file=sys.stderr)
                    continue

            if path_template not in manifest_paths:
                manifest.setdefault('files', []).append(item)
                manifest_paths.add(path_template)
                manifest_changed = True
                print(f"  - Added '{path_template}' to manifest.")

        if manifest_changed:
            self._save_bundle_manifest(bundle_path, manifest)

    def new_bundle(self, bundle_name, workflow_name):
        """Creates a new bundle directory and manifest."""
        bundle_path = Path(BUNDLES_DIR) / bundle_name
        if bundle_path.exists():
            print(f"Error: Bundle '{bundle_name}' already exists at '{bundle_path}'", file=sys.stderr)
            return

        workflow_def = self._get_workflow_def(workflow_name)
        if not workflow_def:
            print(f"Error: Workflow '{workflow_name}' not found in configuration.", file=sys.stderr)
            return

        try:
            bundle_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error creating bundle directory: {e}", file=sys.stderr)
            return

        first_step = workflow_def['steps'][0]['name']
        manifest = {
            "bundle_name": bundle_name,
            "bundle_path": str(bundle_path),
            "workflow_name": workflow_name,
            "current_step": first_step,
            "files": []
        }

        print(f"Created bundle '{bundle_name}' at '{bundle_path}'.")
        
        self._save_bundle_manifest(str(bundle_path), manifest)
        self.set_active_bundle(bundle_name, is_new=True)

    def set_active_bundle(self, bundle_name, is_new=False):
        """Sets a bundle as the active session."""
        bundle_path_str = str(Path(BUNDLES_DIR) / bundle_name)
        if not Path(bundle_path_str).is_dir():
            print(f"Error: Bundle '{bundle_name}' not found at '{bundle_path_str}'.", file=sys.stderr)
            return

        manifest = self._load_bundle_manifest(bundle_path_str)
        if not manifest:
            return
            
        workflow_def = self._get_workflow_def(manifest['workflow_name'])
        if not workflow_def:
            print(f"Error: Workflow '{manifest['workflow_name']}' for this bundle not found.", file=sys.stderr)
            return
        
        self.state['active_bundle_path'] = bundle_path_str
        self._save_state()
        self._save_bundle_manifest(bundle_path_str, manifest)

        print(f"\nSet '{bundle_name}' as the active bundle.")
        
        self._process_auto_creates_for_step(manifest, workflow_def)

        self.show_status()

    def show_status(self):
        """Displays the current workflow session status."""
        bundle_path = self._get_active_bundle_path()
        if not bundle_path:
            print("No active workflow session.")
            return

        manifest = self._load_bundle_manifest(bundle_path)
        if not manifest:
            return

        workflow_def = self._get_workflow_def(manifest['workflow_name'])
        if not workflow_def:
            print(f"Error: Workflow '{manifest['workflow_name']}' not found for active bundle.", file=sys.stderr)
            return

        steps = [step['name'] for step in workflow_def['steps']]
        current_step_name = manifest['current_step']
        
        try:
            current_index = steps.index(current_step_name)
        except ValueError:
            print(f"Error: Current step '{current_step_name}' not found in workflow definition.", file=sys.stderr)
            return

        current_step_info = workflow_def['steps'][current_index]
        user_tag = current_step_info.get('user_tag', 'N/A')

        ref_files, edit_files = self._get_files_for_current_step(manifest)

        # Calculate totals for current step - only include files with 'r' or 'e'
        all_step_file_paths = []
        for file_entry in manifest.get('files', []):
            permissions_str = file_entry.get('permissions', '')
            perms = dict(p.split('=') for p in permissions_str.replace(' ', '').split(',') if '=' in p)
            if current_step_name in perms:
                perm = perms[current_step_name]
                if perm in ['r', 'e']:
                    all_step_file_paths.append(file_entry['path'])
        
        total_bytes, total_tokens = self._calculate_step_totals(
            all_step_file_paths,
            manifest['bundle_path']
        )
        
        formatted_size = format_file_size(total_bytes)
        formatted_tokens = format_token_count(total_tokens)

        print()
        print(f"--- Bundle: {manifest['bundle_name']} ({manifest['workflow_name']}) ---")
        print()
        
        print(f"   >> {current_step_name} << ")
        
        print("\n  Reference Files for this step:")
        if ref_files:
            for f in ref_files:
                print(f"    - {f}")
        else:
            print("    - None")
        
        print("\n  Editable Files for this step:")
        if edit_files:
            for f in edit_files:
                print(f"    - {f}")
        else:
            print("    - None")

        # New section for prompt info
        prompt_source_info = "  Prompt: Not available"
        tag_config = find_by_user_tag(self.raw_config, user_tag)
        if tag_config:
            ai_str = tag_config.get('ai')
            mode_str = tag_config.get('mode', 'general')

            if ai_str:
                prompt_manager = PromptManager(self.raw_config)
                prompt_details = prompt_manager.get_prompt_template_details(mode_str, ai_str)
                if prompt_details:
                    if 'template_file' in prompt_details:
                        relative_path = prompt_details['template_file']
                        source_path_str = prompt_details.get('_source_path')
                        if source_path_str:
                            full_path = Path(source_path_str) / relative_path
                            prompt_source_info = f"  Prompt file: {full_path}"
                        else:
                            prompt_source_info = f"  Prompt file: {relative_path}"
                    elif 'template' in prompt_details:
                        prompt_source_info = f"  Prompt: {prompt_details['template']}"
                    else:
                        prompt_source_info = "  Prompt: source not specified in config"
                else:
                    prompt_source_info = f"  Prompt: no template for mode '{mode_str}'"
            else:
                prompt_source_info = "  Prompt: AI not set for user tag"
        else:
            prompt_source_info = "  Prompt: user tag not found"

        auto_prompt = current_step_info.get('auto_prompt')

        print()
        print(prompt_source_info)
        if auto_prompt:
            print(f"  Auto prompt: {auto_prompt}")
        else:
            print("  Auto prompt isn't set")

        print(f"\n-----------------------  ({formatted_size}, ~{formatted_tokens} tokens)\n")

    def _get_files_for_current_step(self, manifest):
        """Parses manifest to get file lists for the current step."""
        ref_files, edit_files = set(), set()
        current_step = manifest['current_step']
        bundle_path = manifest['bundle_path']

        for file_entry in manifest.get('files', []):
            permissions_str = file_entry.get('permissions', '')
            perms = dict(p.split('=') for p in permissions_str.replace(' ', '').split(',') if '=' in p)

            perm = perms.get(current_step)
            if perm:
                path_pattern = file_entry['path'].replace('{BUNDLE_PATH}', bundle_path)
                matched_files = glob.glob(path_pattern, recursive=True)

                for file_path in matched_files:
                    if Path(file_path).is_file():
                        if perm == 'r':
                            ref_files.add(file_path)
                        elif perm == 'e':
                            edit_files.add(file_path)

        return sorted(list(ref_files)), sorted(list(edit_files))

    def _move_step(self, direction):
        """Helper to move to the next or previous step."""
        bundle_path = self._get_active_bundle_path()
        if not bundle_path:
            print("No active workflow session.", file=sys.stderr)
            return

        manifest = self._load_bundle_manifest(bundle_path)
        if not manifest: return

        workflow_def = self._get_workflow_def(manifest['workflow_name'])
        if not workflow_def: return
        
        steps = [step['name'] for step in workflow_def['steps']]
        try:
            current_index = steps.index(manifest['current_step'])
        except ValueError:
            print("Error: Current step is invalid.", file=sys.stderr)
            return

        new_index = current_index + direction
        if 0 <= new_index < len(steps):
            manifest['current_step'] = steps[new_index]
            self._save_bundle_manifest(bundle_path, manifest)
            self._process_auto_creates_for_step(manifest, workflow_def)
            self.show_status()
        else:
            print("Already at the first/last step.", file=sys.stderr)

    def next_step(self):
        self._move_step(1)

    def prev_step(self):
        self._move_step(-1)

    def exit_workflow(self):
        """Exits the current workflow session."""
        self.state['active_bundle_path'] = None
        self._save_state()
        print("Exited workflow session.")

    def select_files(self):
        """Opens a TUI to manage file permissions for the active bundle."""
        bundle_path = self._get_active_bundle_path()
        if not bundle_path:
            print("No active workflow session. Use 'a bundle set <name>' first.", file=sys.stderr)
            return

        manifest = self._load_bundle_manifest(bundle_path)
        if not manifest: return

        workflow_def = self._get_workflow_def(manifest['workflow_name'])
        if not workflow_def:
            print(f"Error: Workflow '{manifest['workflow_name']}' not found for active bundle.", file=sys.stderr)
            return
        
        updated_manifest = run_file_selector(manifest, workflow_def)
        
        if updated_manifest:
            # You might want to create a backup before saving
            self._save_bundle_manifest(bundle_path, updated_manifest)
            print("Permissions updated in manifest.json.")
        else:
            print("No changes were made.")

    def add_file(self, file_path, perms_str):
        """Adds a file entry to the active bundle's manifest."""
        bundle_path = self._get_active_bundle_path()
        if not bundle_path:
            print("No active workflow session. Cannot add file.", file=sys.stderr)
            return

        manifest = self._load_bundle_manifest(bundle_path)
        if not manifest: return

        # Check for duplicates
        for f in manifest['files']:
            if f['path'] == file_path:
                print(f"File pattern '{file_path}' already in manifest. Updating permissions.", file=sys.stderr)
                f['permissions'] = perms_str
                self._save_bundle_manifest(bundle_path, manifest)
                print("Permissions updated.")
                return

        manifest['files'].append({"path": file_path, "permissions": perms_str})
        self._save_bundle_manifest(bundle_path, manifest)
        print(f"Added pattern '{file_path}' to bundle '{manifest['bundle_name']}'.")

        # Provide feedback on how many files the pattern matches
        path_pattern = file_path.replace('{BUNDLE_PATH}', bundle_path)
        matched_files = glob.glob(path_pattern, recursive=True)
        num_files = len([f for f in matched_files if Path(f).is_file()])
        print(f"The pattern currently matches {num_files} file(s).")

    def list_workflows(self):
        """Lists all available workflows from config."""
        print("Available Workflows:")
        if not self.workflows:
            print("No workflows defined in configuration files.")
            return
        for wf in self.workflows:
            print(f"  - {wf.get('name', 'N/A')}: {wf.get('description', 'No description')}")
        

    def list_bundles(self):
        """Lists all bundles in the bundles/ directory."""
        print("--- Available Bundles ---")
        bundles_path = Path(BUNDLES_DIR)
        if not bundles_path.exists() or not bundles_path.is_dir():
            print(f"No '{BUNDLES_DIR}' directory found.")
            return
        
        bundles = sorted([d.name for d in bundles_path.iterdir() if d.is_dir()])
        if not bundles:
            print("No bundles found.")
        else:
            for bundle in bundles:
                print(f"  - {bundle}")
        print("-------------------------")

    def get_workflow_context(self):
        """
        If a workflow is active, returns its context.
        Otherwise, returns None.
        """
        bundle_path = self._get_active_bundle_path()
        if not bundle_path:
            return None

        manifest = self._load_bundle_manifest(bundle_path)
        if not manifest: return None

        workflow_def = self._get_workflow_def(manifest['workflow_name'])
        if not workflow_def: return None
        
        current_step_name = manifest['current_step']
        current_step_obj = next((s for s in workflow_def['steps'] if s['name'] == current_step_name), None)
        if not current_step_obj: return None
            
        user_tag = current_step_obj.get('user_tag')
        auto_prompt = current_step_obj.get('auto_prompt')
        ref_files, edit_files = self._get_files_for_current_step(manifest)
        
        display_status = f"Workflow: {manifest['workflow_name']} | Step: {current_step_name} ({user_tag})"

        return {
            "user_tag": user_tag,
            "reference_files": ref_files,
            "editable_files": edit_files,
            "display_status": display_status,
            "current_step_name": current_step_name,
            "auto_prompt": auto_prompt,
        }
