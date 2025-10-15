
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

import re
from typing import Optional, Dict, Any, Set
from pathlib import Path

class PromptManager:
    """
    Manages prompt templates for different modes and AI providers.
    Handles template selection based on AI string pattern matching.
    Also supports file-based template inclusion for modular prompts.
    """
    MAX_RECURSION_DEPTH = 10
    # Regex to find valid placeholders for file inclusion.
    # It must not match placeholders with format specifiers like {var:format}.
    # This regex matches keys with letters, numbers, underscore, and hyphen.
    PLACEHOLDER_REGEX = re.compile(r'{([a-zA-Z0-9_-]+)}')
    
    def __init__(self, config: dict):
        """
        Initialize the PromptManager with configuration.
        
        Args:
            config: Configuration dictionary containing modes and other settings
        """
        self.config = config
        self.modes = {m['name']: m for m in config.get('modes', [])}
        self.default_mode = config.get('default_mode', 'general')
        
        self._file_cache = {}
        # The search order is project-level first, then user-level, allowing
        # project-specific prompts to override user defaults.
        self.prompt_search_paths = [
            Path("./.agent_a/prompts"),
            Path.home() / ".agent_a/prompts",
        ]
    
    def get_mode_config(self, mode: str) -> Optional[dict]:
        """
        Get the configuration for a specific mode.
        
        Args:
            mode: Mode name (e.g., 'general', 'coding', 'design')
        
        Returns:
            Mode configuration dict or None if not found
        """
        return self.modes.get(mode or self.default_mode)
    
    def validate_mode_requirements(self, mode: str, has_editable: bool) -> bool:
        """
        Validate that mode requirements are met.
        
        Args:
            mode: Mode name to validate
            has_editable: Whether editable files are provided
        
        Returns:
            True if requirements are met, False otherwise
        """
        mode_config = self.get_mode_config(mode)
        if not mode_config:
            return False
        
        requires_editable = mode_config.get('requires_editable_files', False)
        if requires_editable and not has_editable:
            return False
        
        return True
    
    def get_prompt_template_details(self, mode: str, ai_string: str) -> Optional[Dict[str, Any]]:
        """
        Get the best matching prompt configuration object for a mode and AI string.
        
        Args:
            mode: Mode name (e.g., 'general', 'coding')
            ai_string: Full AI string (e.g., 'claude:anthropic:claude-sonnet-4-5')
        
        Returns:
            The prompt configuration dict or None if not found.
        """
        mode_config = self.get_mode_config(mode)
        if not mode_config:
            return None
        
        prompts = mode_config.get('prompts', [])
        
        # Try to find best matching prompt config object
        best_match_obj = None
        best_score = -1
        
        for prompt_config in prompts:
            ai_pattern = prompt_config.get('ai', 'default')
            score = self._match_ai_pattern(ai_string, ai_pattern)
            if score > best_score:
                best_score = score
                best_match_obj = prompt_config
        
        return best_match_obj

    def get_prompt_template(self, mode: str, ai_string: str) -> Optional[str]:
        """
        Get the best matching prompt template for a mode and AI string.
        Handles loading templates from files via 'template_file'.
        
        Args:
            mode: Mode name (e.g., 'general', 'coding')
            ai_string: Full AI string (e.g., 'claude:anthropic:claude-sonnet-4-5')
        
        Returns:
            Prompt template string or None if not found
        """
        best_match_obj = self.get_prompt_template_details(mode, ai_string)
        
        if not best_match_obj:
            return None

        # --- Validation and template resolution ---
        has_template = 'template' in best_match_obj
        has_template_file = 'template_file' in best_match_obj

        if has_template and has_template_file:
            raise ValueError(f"Prompt configuration for mode '{mode}' cannot contain both 'template' and 'template_file'.")
        
        if not has_template and not has_template_file:
            raise ValueError(f"Prompt configuration for mode '{mode}' must contain either 'template' or 'template_file'.")
        
        if has_template:
            return best_match_obj.get('template')

        if has_template_file:
            relative_path = best_match_obj.get('template_file')
            source_path_str = best_match_obj.get('_source_path')

            if not source_path_str:
                raise ValueError(f"'_source_path' is missing for prompt with 'template_file'. Configuration loading error.")

            base_path = Path(source_path_str)
            template_path = base_path / relative_path

            if not template_path.is_file():
                raise FileNotFoundError(f"Template file not found at resolved path: {template_path}")
            
            try:
                with template_path.open('r', encoding='utf-8') as f:
                    return f.read()
            except IOError as e:
                raise IOError(f"Error reading template file at '{template_path}': {e}")

        return None # Should not be reached
    
    def _match_ai_pattern(self, ai_string: str, pattern: str) -> int:
        """
        Match an AI string against a pattern and return a score.
        Higher scores indicate better matches.
        
        Scoring:
        - Exact match: 100
        - Wildcard matches with specific parts: 10-30
        - Default pattern: 1
        - No match: 0
        
        Args:
            ai_string: Full AI string (e.g., 'claude:anthropic:claude-sonnet-4-5')
            pattern: Pattern to match (e.g., 'claude:*:*', 'default')
        
        Returns:
            Match score (higher is better)
        """
        # Exact match: highest score
        if ai_string == pattern:
            return 100
        
        # Default pattern: lowest score (but still matches)
        if pattern == 'default':
            return 1
        
        # Wildcard matching
        pattern_parts = pattern.split(':')
        ai_parts = ai_string.split(':')
        
        # Must have same number of parts
        if len(pattern_parts) != len(ai_parts):
            return 0
        
        score = 10
        for p, a in zip(pattern_parts, ai_parts):
            if p == '*':
                # Wildcard matches anything, add small score
                score += 1
            elif p == a:
                # Exact part match, add larger score
                score += 10
            else:
                # Part doesn't match, pattern doesn't match
                return 0
        
        return score
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """
        Format a prompt template with provided variables.
        
        This method supports file-based includes. Placeholders like {key} will
        be replaced by the content of `key.txt` found in the configured prompt
        search paths.
        
        Args:
            template: Prompt template string with {variable} placeholders.
            **kwargs: Variables to substitute in the template.
        
        Returns:
            Formatted prompt string.
        """
        # Provide defaults for common variables
        defaults = {
            'prompt': '',
            'context': '',
            'reference_files': 'None',
            'editable_files': 'None',
            'plain_text_guide': '',
            'model_name': '',
            'router': '',
            'provider': ''
        }
        
        # Merge defaults with provided kwargs
        variables = {**defaults, **kwargs}
        
        # The visited set is used to detect circular dependencies
        return self._resolve_and_format(template, variables, set())

    def _resolve_and_format(self, text: str, variables: Dict[str, Any], visited: Set[str]) -> str:
        """
        Recursively resolve file-based placeholders and format the text.
        
        Args:
            text: The template string to process.
            variables: A dictionary of already known variables.
            visited: A set of keys visited in the current resolution path to detect
                     circular dependencies.
        
        Returns:
            The fully resolved and formatted string.
            
        Raises:
            RecursionError: If max recursion depth is exceeded or a circular
                            dependency is detected.
            ValueError: If a required template file is not found or a variable
                        is missing after resolution.
            IOError: If a prompt file cannot be read.
        """
        if len(visited) > self.MAX_RECURSION_DEPTH:
            raise RecursionError(
                f"Maximum recursion depth of {self.MAX_RECURSION_DEPTH} exceeded. "
                f"Check for circular dependencies in your prompt files. "
                f"Path: {' -> '.join(visited)}"
            )

        # Find all unique placeholders that could be file includes
        placeholders = sorted(list(set(self.PLACEHOLDER_REGEX.findall(text))))

        for key in placeholders:
            if key in variables:
                continue  # Already provided, skip file resolution

            if key in visited:
                raise RecursionError(
                    f"Circular dependency detected: '{key}' is already in the "
                    f"resolution path. Path: {' -> '.join(visited)} -> {key}"
                )

            # Try to load content from file
            if key in self._file_cache:
                content = self._file_cache[key]
            else:
                found_path = None
                for search_path in self.prompt_search_paths:
                    file_path = search_path / f"{key}.txt"
                    if file_path.is_file():
                        found_path = file_path
                        break
                
                if not found_path:
                    # Not a file-based template, will be handled by final format()
                    continue
                    
                try:
                    content = found_path.read_text(encoding='utf-8')
                    self._file_cache[key] = content
                except IOError as e:
                    raise IOError(f"Error reading prompt file at '{found_path}': {e}")
            
            # Recursively resolve nested placeholders in the loaded content
            new_visited = visited.copy()
            new_visited.add(key)
            resolved_content = self._resolve_and_format(content, variables, new_visited)
            variables[key] = resolved_content
        
        try:
            return text.format(**variables)
        except KeyError as e:
            # A placeholder was found that was not in kwargs and was not a
            # resolvable file. This is the final error point.
            key_name = e.args[0]
            searched = [str(p) for p in self.prompt_search_paths]
            raise ValueError(
                f"Template variable '{key_name}' was not provided and a "
                f"corresponding prompt file '{key_name}.txt' was not found in "
                f"search paths: {', '.join(searched)}"
            )
