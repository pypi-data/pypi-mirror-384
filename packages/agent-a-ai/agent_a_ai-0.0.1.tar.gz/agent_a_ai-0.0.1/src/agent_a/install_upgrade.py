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
import hashlib
import shutil
from pathlib import Path

try:
    from importlib import resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

USER_DIR = Path.home() / ".agent_a"
PROMPTS_DIR = USER_DIR / "prompts"
MANIFEST_PATH = PROMPTS_DIR / ".manifest.json"
PACKAGE_NAME = "agent_a"
CONFIG_FILENAME = "user_agent_a.json"

def _get_file_hash(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def _get_package_resource_hash(ref):
    h = hashlib.sha256()
    h.update(ref.read_bytes())
    return h.hexdigest()

def _load_manifest():
    if not MANIFEST_PATH.exists():
        return {}
    try:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _save_manifest(manifest_data):
    try:
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)
    except IOError as e:
        print(f"Error: Could not write to manifest: {e}", file=sys.stderr)

def _plan_first_time_install():
    plan = []
    plan.append({'action': 'CREATE_DIR', 'path': USER_DIR})
    plan.append({'action': 'CREATE_DIR', 'path': PROMPTS_DIR})

    config_src_ref = pkg_resources.files('agent_a').joinpath('files', CONFIG_FILENAME)
    config_dest = USER_DIR / CONFIG_FILENAME
    plan.append({
        'action': 'COPY_FILE',
        'source': config_src_ref,
        'dest': config_dest,
        'reason': 'Default configuration file'
    })

    manifest = {}
    prompt_files = pkg_resources.files('agent_a').joinpath('files', 'prompts').iterdir()
    for prompt_ref in prompt_files:
        # Skip Python files and __pycache__ directories
        if prompt_ref.is_file() and not prompt_ref.name.endswith('.py') and not prompt_ref.name.endswith('.pyc'):
            dest_path = PROMPTS_DIR / prompt_ref.name
            plan.append({
                'action': 'COPY_FILE',
                'source': prompt_ref,
                'dest': dest_path,
                'reason': f"Default prompt: {prompt_ref.name}"
            })
            manifest[prompt_ref.name] = _get_package_resource_hash(prompt_ref)

    plan.append({'action': 'CREATE_MANIFEST', 'data': manifest})
    return plan

def _plan_prompt_upgrades():
    plan = []
    manifest = _load_manifest()
    if not manifest:
        return []

    prompt_files = pkg_resources.files('agent_a').joinpath('files', 'prompts').iterdir()
    for prompt_ref in prompt_files:
        # Skip Python files, pyc files, and directories
        if not prompt_ref.is_file() or prompt_ref.name.endswith('.py') or prompt_ref.name.endswith('.pyc'):
            continue

        prompt_name = prompt_ref.name
        dest_path = PROMPTS_DIR / prompt_name
        package_hash = _get_package_resource_hash(prompt_ref)

        if not dest_path.exists():
            plan.append({
                'action': 'COPY_FILE',
                'source': prompt_ref,
                'dest': dest_path,
                'reason': f"New prompt available: {prompt_name}"
            })
            plan.append({
                'action': 'UPDATE_MANIFEST',
                'file': prompt_name,
                'hash': package_hash
            })
        elif prompt_name in manifest:
            disk_hash = _get_file_hash(dest_path)
            manifest_hash = manifest[prompt_name]

            is_modified_by_user = (disk_hash != manifest_hash)
            is_updated_in_package = (package_hash != manifest_hash)

            if not is_modified_by_user and is_updated_in_package:
                plan.append({
                    'action': 'COPY_FILE',
                    'source': prompt_ref,
                    'dest': dest_path,
                    'reason': f"Stock prompt updated: {prompt_name}"
                })
                plan.append({
                    'action': 'UPDATE_MANIFEST',
                    'file': prompt_name,
                    'hash': package_hash
                })
    return plan

def _display_plan_and_get_approval(plan):
    print("Agent A needs to initialize or update its configuration.")
    print("The following changes will be made:")
    for item in plan:
        action = item['action']
        if action == 'CREATE_DIR':
            print(f"  - Create directory: {item['path']}")
        elif action == 'COPY_FILE':
            print(f"  - Install/Update file: {item['dest']}")
            print(f"    Reason: {item['reason']}")
    print("\nNo user-modified files will be overwritten.")
    try:
        approval = input("Do you want to proceed? [Y/n]: ").lower().strip()
        return approval in ('', 'y', 'yes')
    except (EOFError, KeyboardInterrupt):
        return False

def _execute_plan(plan):
    print("Applying changes...")
    manifest_updates = {}
    manifest_to_create = None

    for item in plan:
        try:
            action = item['action']
            if action == 'CREATE_DIR':
                os.makedirs(item['path'], exist_ok=True)
            elif action == 'COPY_FILE':
                with pkg_resources.as_file(item['source']) as src_path:
                    shutil.copy2(src_path, item['dest'])
            elif action == 'CREATE_MANIFEST':
                manifest_to_create = item['data']
            elif action == 'UPDATE_MANIFEST':
                manifest_updates[item['file']] = item['hash']
        except Exception as e:
            print(f"Error applying change {item}: {e}", file=sys.stderr)
            print("Aborting operation.", file=sys.stderr)
            return

    if manifest_to_create is not None:
        _save_manifest(manifest_to_create)
    elif manifest_updates:
        manifest = _load_manifest()
        manifest.update(manifest_updates)
        _save_manifest(manifest)
    print("Done.")

def check_and_run():
    if not USER_DIR.exists():
        plan = _plan_first_time_install()
    else:
        plan = _plan_prompt_upgrades()

    if not plan:
        return

    if _display_plan_and_get_approval(plan):
        _execute_plan(plan)
    else:
        print("Operation cancelled by user.", file=sys.stderr)
        sys.exit(1)