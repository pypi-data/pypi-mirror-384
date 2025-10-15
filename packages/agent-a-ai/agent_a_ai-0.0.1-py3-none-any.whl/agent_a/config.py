
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
import sys
from pathlib import Path
from  agent_a.prompts import PromptManager


def find_by_user_tag(config, tag_name):
    """
    Searches for a user tag and returns its configuration.
    Supports both legacy list format and new dict format.
    
    Args:
        config (dict): The configuration dictionary
        tag_name (str): The name of the tag to search for
    
    Returns:
        dict with 'ai' and optional 'mode' keys, or None if not found
    """
    user_tags = config.get('user_tags', {})
    
    if isinstance(user_tags, dict):
        tag_config = user_tags.get(tag_name)
        if tag_config:
            # If it's a string, convert to dict format
            if isinstance(tag_config, dict):
                return {
                    'ai': tag_config.get('ai'),
                    'mode': tag_config.get('mode')
                }
            
    return None


def load_raw_config():
    """
    Loads and merges configurations from user and project files.
    Returns the raw, merged configuration dictionary.
    """
    config = {
        "default_user_tag": "quick",
        "user_tags": {},
        "modes": [],
        "additional_context": "",
        "additional_references": [],
        "workflows": []
    }

    # --- Load user config ---
    user_config_path = Path.home() / ".agent_a/user_agent_a.json"
    if user_config_path.is_file():
        print(f"--- Loading user config from {user_config_path} ---", file=sys.stderr)
        try:
            with user_config_path.open('r', encoding='utf-8') as f:
                user_data = json.load(f)
                
                # Load values, checking type
                if isinstance(user_data.get("default_user_tag"), str):
                    config["default_user_tag"] = user_data.get("default_user_tag")
                if "user_tags" in user_data:
                    config["user_tags"] = user_data.get("user_tags")

                if isinstance(user_data.get("modes"), list):
                    user_modes = user_data.get("modes")
                    user_base_path = user_config_path.parent
                    for mode in user_modes:
                        if "prompts" in mode and isinstance(mode.get("prompts"), list):
                            for prompt in mode["prompts"]:
                                if isinstance(prompt, dict):
                                    prompt["_source_path"] = str(user_base_path)
                    config["modes"] = user_modes

                if isinstance(user_data.get("additional_context"), str):
                    config["additional_context"] = user_data.get("additional_context")
                if isinstance(user_data.get("additional_references"), list):
                    config["additional_references"] = user_data.get("additional_references")
                if isinstance(user_data.get("workflows"), list):
                    config["workflows"] = user_data.get("workflows")

        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Could not read or parse user config file at '{user_config_path}'. Error: {e}", file=sys.stderr)

    # --- Load project config (and override user settings) ---
    project_config_path = Path("./.agent_a/agent_a.json")
    if project_config_path.is_file():
        print(f"--- Loading project config from {project_config_path} ---", file=sys.stderr)
        try:
            with project_config_path.open('r', encoding='utf-8') as f:
                project_data = json.load(f)
                
                # Override if present and correct type
                if isinstance(project_data.get("default_user_tag"), str):
                    config["default_user_tag"] = project_data.get("default_user_tag")
                
                # Merge user_tags dictionary
                if "user_tags" in project_data and isinstance(project_data.get("user_tags"), dict):
                    config["user_tags"].update(project_data.get("user_tags"))

                # Merge modes list by name
                if isinstance(project_data.get("modes"), list):
                    project_modes = project_data.get("modes")
                    project_base_path = project_config_path.parent
                    
                    modes_dict = {m['name']: m for m in config['modes'] if m.get('name')}
                    for mode in project_modes:
                        if "prompts" in mode and isinstance(mode.get("prompts"), list):
                            for prompt in mode["prompts"]:
                                if isinstance(prompt, dict):
                                    prompt["_source_path"] = str(project_base_path)
                        if mode.get('name'):
                            modes_dict[mode['name']] = mode
                    config["modes"] = list(modes_dict.values())

                if isinstance(project_data.get("additional_context"), str):
                    config["additional_context"] = project_data.get("additional_context")
                if isinstance(project_data.get("additional_references"), list):
                    config["additional_references"] = project_data.get("additional_references")
                
                # Merge workflows list by name
                if isinstance(project_data.get("workflows"), list):
                    project_workflows = project_data.get("workflows")
                    workflows_dict = {w['name']: w for w in config['workflows'] if w.get('name')}
                    for workflow in project_workflows:
                        if workflow.get('name'):
                            workflows_dict[workflow['name']] = workflow
                    config["workflows"] = list(workflows_dict.values())
        
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Could not read or parse project config file at '{project_config_path}'. Error: {e}", file=sys.stderr)

    return config


def load_config(raw_config, user_tag, ai_str, mode_str):
    """
    Resolves the final AI and mode settings based on raw config, user tags, and CLI flags.
    
    Args:
        raw_config: The merged configuration dictionary from load_raw_config()
        user_tag: User tag name (from -u flag or workflow)
        ai_str: AI string (from -a flag)
        mode_str: Mode string (from -mo flag)
    
    Returns:
        tuple: (resolved_ai, resolved_mode, additional_context, 
                additional_references, prompt_manager)
    """
    # --- Resolve AI and Mode ---
    # Resolution order:
    # 1. Command line flags (-a and -mo) take highest precedence
    # 2. User tag provides defaults if flags not specified
    # 3. default_user_tag if no user tag specified
    
    resolved_ai = None
    resolved_mode = None
    
    # Determine which tag to use
    effective_tag = user_tag if user_tag else raw_config["default_user_tag"]
    
    # Look up the tag
    if effective_tag:
        tag_config = find_by_user_tag(raw_config, effective_tag)
        if tag_config:
            resolved_ai = tag_config.get('ai')
            resolved_mode = tag_config.get('mode')
        else:
            # Allow run to continue if CLI flags provide AI/mode, just warn
            print(f"Warning: Unknown user tag '{effective_tag}'", file=sys.stderr)

    # Override with command line flags if provided
    if ai_str:
        resolved_ai = ai_str
    
    if mode_str:
        resolved_mode = mode_str
    
    # Final fallback if still not set
    if not resolved_ai:
        print("Error: No AI model specified. Use -a, -u, or set a default_user_tag.", 
              file=sys.stderr)
        sys.exit(1)
    
    if not resolved_mode:
        resolved_mode = 'general'  # Hard-coded fallback
    
    # Create PromptManager with the full configuration
    prompt_manager = PromptManager(raw_config)
    
    return (
        resolved_ai,
        resolved_mode,
        raw_config.get('additional_context', ''),
        raw_config.get('additional_references', []),
        prompt_manager
    )
