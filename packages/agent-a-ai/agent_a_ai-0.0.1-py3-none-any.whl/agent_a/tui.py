
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

import curses
import sys
import glob
from collections import defaultdict
from pathlib import Path
from agent_a.utils import (
    calculate_file_size,
    estimate_tokens,
    format_file_size,
    format_token_count
)

def run_file_selector(manifest, workflow_def):
    """Public entry point to run the TUI file selector."""
    if sys.platform == "win32":
        print("Error: The 'bundle select' TUI is not supported on Windows.", file=sys.stderr)
        sys.exit(1)
    
    tui = _TUI(manifest, workflow_def)
    final_state = curses.wrapper(tui.main)
    
    if final_state and final_state.get('dirty'):
        return _save_state_to_manifest(final_state, manifest)
    return None

def _is_glob_pattern(path_str):
    return "*" in path_str or "?" in path_str or "[" in path_str

def _load_initial_state(manifest, workflow_def):
    """Transforms manifest data into a TUI-friendly grid state."""
    bundle_path = manifest.get('bundle_path', '.')
    rows = []
    
    permissions = defaultdict(dict)
    for file_entry in manifest.get('files', []):
        path = file_entry['path']
        perms_str = file_entry.get('permissions', '')
        perms = dict(p.split('=') for p in perms_str.replace(' ', '').split(',') if '=' in p)
        for step, perm in perms.items():
            if step in [s['name'] for s in workflow_def.get('steps', [])]:
                permissions[path][step] = perm

    sorted_files = sorted(manifest.get('files', []), key=lambda x: x['path'])

    max_path_width = len("File Path")  # Initialize with header length

    for file_entry in sorted_files:
        path_pattern = file_entry['path']
        is_pattern = _is_glob_pattern(path_pattern)
        
        # Account for indentation and prefixes like "[+] "
        if is_pattern:
            # Level 0, pattern: "[+] path" -> 4 chars + len
            display_len = 4 + len(path_pattern)
        else:
            # Level 0, file: " path" -> 1 char + len
            display_len = 1 + len(path_pattern)
        max_path_width = max(max_path_width, display_len)

        row = {
            'path': path_pattern,
            'is_pattern': is_pattern,
            'is_expanded': False,
            'level': 0,
            'children': [],
        }

        if is_pattern:
            # Resolve {BUNDLE_PATH} before glob expansion
            full_pattern = path_pattern.replace('{BUNDLE_PATH}', bundle_path)
            try:
                matched_files = sorted(glob.glob(full_pattern, recursive=True))
                for f_path in matched_files:
                    if Path(f_path).is_file():
                        # Level 1, child: "   path" -> 3 chars + len
                        child_len = 3 + len(f_path)
                        max_path_width = max(max_path_width, child_len)

                        child_row = {
                            'path': f_path,
                            'is_pattern': False,
                            'level': 1,
                            'parent_path': path_pattern,
                        }
                        row['children'].append(child_row)
            except Exception:
                pass
        
        rows.append(row)

    # Calculate file sizes - resolve {BUNDLE_PATH} before calculating
    file_sizes = {}
    for row in rows:
        if row['is_pattern']:
            pattern_total = 0
            for child in row['children']:
                # Children already have resolved paths from glob expansion
                child_size = calculate_file_size(child['path'])
                file_sizes[child['path']] = child_size
                pattern_total += child_size
            file_sizes[row['path']] = pattern_total
        else:
            # Resolve {BUNDLE_PATH} for individual files
            resolved_path = row['path'].replace('{BUNDLE_PATH}', bundle_path)
            file_sizes[row['path']] = calculate_file_size(resolved_path)

    # Calculate step totals - only count top-level files (not expanded children)
    step_totals = {}
    for step_def in workflow_def.get('steps', []):
        step_name = step_def['name']
        step_bytes = 0
        
        for row in rows:
            path = row['path']
            # Only count if this file has permission for this step
            if step_name in permissions[path]:
                perm = permissions[path][step_name]
                # Only count files with 'r' or 'e' permission
                if perm in ['r', 'e']:
                    step_bytes += file_sizes.get(path, 0)
        
        step_tokens = estimate_tokens(step_bytes)
        step_totals[step_name] = (step_bytes, step_tokens)

    state = {
        "rows": rows,
        "visible_rows": [],
        "steps": [step['name'] for step in workflow_def.get('steps', [])],
        "permissions": permissions,
        "file_sizes": file_sizes,
        "step_totals": step_totals,
        "bundle_path": bundle_path,
        "cursor_x": 0,
        "cursor_y": 0,
        "scroll_y": 0,
        "max_path_width": max_path_width,
        "dirty": False
    }
    return state

def _save_state_to_manifest(state, original_manifest):
    """Converts the final TUI state back into the manifest format."""
    file_map = {f['path']: f for f in original_manifest.get('files', [])}
    
    for path, perms_dict in state['permissions'].items():
        if not perms_dict:
            if path in file_map:
                file_map[path]['permissions'] = ''
            continue

        new_perms_list = [f"{step}={perm}" for step, perm in sorted(perms_dict.items())]
        new_perms_str = ','.join(new_perms_list)

        if path in file_map:
            file_map[path]['permissions'] = new_perms_str
        else:
            original_manifest.setdefault('files', []).append({
                'path': path,
                'permissions': new_perms_str,
            })

    return original_manifest

class _TUI:
    def __init__(self, manifest, workflow_def):
        self.initial_manifest = manifest
        self.initial_workflow = workflow_def
        self.state = None

    def main(self, stdscr):
        self.state = _load_initial_state(self.initial_manifest, self.initial_workflow)
        self._rebuild_visible_rows()
        
        curses.curs_set(0)
        stdscr.keypad(True)
        
        while True:
            self._draw(stdscr)
            key = stdscr.getch()

            if key == ord('q'):
                return self.state
            
            self._handle_input(key, stdscr)

    def _rebuild_visible_rows(self):
        visible = []
        for row in self.state['rows']:
            visible.append(row)
            if row.get('is_pattern') and row.get('is_expanded'):
                visible.extend(row.get('children', []))
        self.state['visible_rows'] = visible

    def _handle_input(self, key, stdscr):
        max_y, max_x = stdscr.getmaxyx()
        num_visible_rows = len(self.state['visible_rows'])
        num_steps = len(self.state['steps'])
        cy, cx = self.state['cursor_y'], self.state['cursor_x']

        if key in [curses.KEY_UP, ord('k')]:
            self.state['cursor_y'] = max(0, cy - 1)
        elif key in [curses.KEY_DOWN, ord('j')]:
            self.state['cursor_y'] = min(num_visible_rows - 1, cy + 1) if num_visible_rows > 0 else 0
        elif key in [curses.KEY_LEFT, ord('h')]:
            self.state['cursor_x'] = max(0, cx - 1)
        elif key in [curses.KEY_RIGHT, ord('l')]:
            self.state['cursor_x'] = min(num_steps - 1, cx + 1) if num_steps > 0 else 0
        elif key == ord('r'):
            self._toggle_perm('r')
        elif key == ord('e'):
            self._toggle_perm('e')
        elif key == ord(' '):
            self._toggle_perm(None)
        elif key in [curses.KEY_ENTER, 10, 13]:
            if num_visible_rows > 0 and cy < num_visible_rows:
                current_row_data = self.state['visible_rows'][cy]
                if current_row_data.get('is_pattern'):
                    for r in self.state['rows']:
                        if r['path'] == current_row_data['path']:
                            r['is_expanded'] = not r['is_expanded']
                            break
                    self._rebuild_visible_rows()
                    self.state['cursor_y'] = min(cy, len(self.state['visible_rows']) - 1)

        header_height = 6
        visible_height = max_y - header_height
        if self.state['cursor_y'] < self.state['scroll_y']:
            self.state['scroll_y'] = self.state['cursor_y']
        if self.state['cursor_y'] >= self.state['scroll_y'] + visible_height:
            self.state['scroll_y'] = self.state['cursor_y'] - visible_height + 1

    def _toggle_perm(self, new_perm):
        if not self.state['visible_rows'] or not self.state['steps']:
            return
            
        row_data = self.state['visible_rows'][self.state['cursor_y']]
        path = row_data['path']
        step = self.state['steps'][self.state['cursor_x']]
        
        effective_perm = self.state['permissions'][path].get(step)
        if effective_perm is None and 'parent_path' in row_data:
            parent_path = row_data['parent_path']
            effective_perm = self.state['permissions'][parent_path].get(step)

        if effective_perm == new_perm:
            self.state['permissions'][path].pop(step, None)
            if not self.state['permissions'][path]:
                del self.state['permissions'][path]
        else:
            self.state['permissions'][path][step] = new_perm
        self.state['dirty'] = True
        self._recalculate_step_totals()

    def _recalculate_step_totals(self):
        """Recalculates size and token totals for each step header."""
        step_totals = {}
        permissions = self.state['permissions']
        file_sizes = self.state['file_sizes']
        
        for step_name in self.state['steps']:
            step_bytes = 0
            for row in self.state['rows']:
                if row['is_pattern']:
                    parent_path = row['path']
                    parent_perm = permissions[parent_path].get(step_name)

                    for child in row['children']:
                        child_path = child['path']
                        child_perm = permissions[child_path].get(step_name)
                        
                        effective_perm = child_perm if child_perm is not None else parent_perm
                        
                        if effective_perm in ['r', 'e']:
                            step_bytes += file_sizes.get(child_path, 0)
                else:
                    path = row['path']
                    perm = permissions[path].get(step_name)
                    if perm in ['r', 'e']:
                        step_bytes += file_sizes.get(path, 0)

            step_tokens = estimate_tokens(step_bytes)
            step_totals[step_name] = (step_bytes, step_tokens)
        
        self.state['step_totals'] = step_totals

    def _draw(self, stdscr):
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        # Dynamically calculate file column width
        min_width = 25
        # Cap width at 70% of terminal width to leave space for other columns
        max_allowed_width = int(max_x * 0.7)
        calculated_width = self.state.get("max_path_width", min_width)
        file_col_width = max(min_width, min(calculated_width, max_allowed_width))

        size_col_width = 8
        token_col_width = 8
        step_col_width = 15

        stdscr.addstr(0, 0, "BUNDLE FILE SELECTOR"[:max_x-1])
        help_keys = "Keys: q)uit, r)ead, e)dit, <space> clear, <enter> expand, arrows/hjkl navigation"
        stdscr.addstr(1, 0, help_keys[:max_x-1])

        # Build header row with separate Size and Tokens columns
        header = "File Path".ljust(file_col_width) + " |"
        header += "Size".rjust(size_col_width) + "|"
        header += "Tokens".rjust(token_col_width) + "|"
        
        # Build step headers with totals
        step_headers = []
        for step in self.state['steps']:
            step_bytes, step_tokens = self.state['step_totals'].get(step, (0, 0))
            size_str = format_file_size(step_bytes)
            token_str = format_token_count(step_tokens)
            totals_str = f"({size_str}/{token_str})"
            step_headers.append((step, totals_str))
            header += step.center(step_col_width) + "|"
        
        stdscr.addstr(3, 0, header[:max_x-1])
        
        # Second header line with step totals
        header_line2 = " " * file_col_width + " |"
        header_line2 += " " * size_col_width + "|"
        header_line2 += " " * token_col_width + "|"
        for step, totals_str in step_headers:
            header_line2 += totals_str.center(step_col_width) + "|"
        stdscr.addstr(4, 0, header_line2[:max_x-1])
        
        stdscr.addstr(5, 0, "-" * (max_x - 1))

        header_height = 6
        for i in range(max_y - header_height):
            row_idx = self.state['scroll_y'] + i
            if row_idx >= len(self.state['visible_rows']):
                break
            
            row_data = self.state['visible_rows'][row_idx]
            path = row_data['path']
            level = row_data.get('level', 0)
            prefix = ""
            if row_data.get('is_pattern'):
                prefix = "[-]" if row_data.get('is_expanded') else "[+]"
            
            disp_path = f"{'  ' * level}{prefix} {path}"
            disp_path = disp_path.ljust(file_col_width)
            if len(disp_path) > file_col_width:
                 disp_path = disp_path[:file_col_width-3] + "..."

            try:
                stdscr.addstr(i + header_height, 0, disp_path + " |")
            except curses.error:
                pass

            # Display size column (right-justified)
            file_size = self.state['file_sizes'].get(path, 0)
            size_disp = format_file_size(file_size).rjust(size_col_width)
            
            try:
                stdscr.addstr(i + header_height, file_col_width + 2, size_disp + "|")
            except curses.error:
                pass

            # Display tokens column (right-justified)
            tokens = estimate_tokens(file_size)
            token_disp = format_token_count(tokens).rjust(token_col_width)
            
            try:
                stdscr.addstr(i + header_height, file_col_width + 2 + size_col_width + 1, token_disp + "|")
            except curses.error:
                pass

            row_len = file_col_width + 2 + size_col_width + 1 + token_col_width + 1
            for j, step in enumerate(self.state['steps']):
                perm = self.state['permissions'][path].get(step)
                is_inherited = False
                if perm is None and 'parent_path' in row_data:
                    parent = row_data['parent_path']
                    if parent in self.state['permissions']:
                        perm = self.state['permissions'][parent].get(step)
                        is_inherited = True
                
                perm_char = perm or ' '
                perm_disp = f"({perm_char})" if is_inherited else f"[{perm_char}]"
                
                is_cursor = (row_idx == self.state['cursor_y'] and j == self.state['cursor_x'])
                attr = curses.A_REVERSE if is_cursor else curses.A_NORMAL

                cell = perm_disp.center(step_col_width)
                try:
                    if row_len + len(cell) < max_x:
                        stdscr.addstr(i + header_height, row_len, cell, attr)
                    if row_len + len(cell) + 1 < max_x:
                        stdscr.addstr(i + header_height, row_len + len(cell), "|")
                except curses.error:
                    pass
                row_len += len(cell) + 1
              
        stdscr.refresh()
