#!/usr/bin/env python3
"""
Fix orphaned parameter properties in YAML file.
Finds properties that are missing their parent '- name:' entry.
"""

import re
import shutil
from datetime import datetime

def fix_orphaned_properties(filename):
    """Fix orphaned parameter properties that are missing '- name:' entries."""
    
    # Create backup
    backup_filename = f"{filename}_backup_orphan_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    shutil.copy2(filename, backup_filename)
    print(f"Created backup: {backup_filename}")
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    fixes_applied = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts with properties but has no preceding '- name:' entry
        if re.match(r'^          offset_hex: ', line):
            # Check if the previous entry is properly structured
            # Look back to find the last parameter entry
            found_proper_structure = False
            j = i - 1
            
            # Look back through recent lines
            while j >= max(0, i - 10):
                prev_line = lines[j].strip()
                if prev_line.startswith('- name:'):
                    # Found a proper parameter entry recently
                    found_proper_structure = True
                    break
                elif prev_line.startswith('bytes:') and j < i - 1:
                    # Found another parameter's bytes entry, this might be orphaned
                    break
                j -= 1
            
            # If we didn't find proper structure, this is likely orphaned
            if not found_proper_structure or j < i - 5:
                # This looks like orphaned properties
                # Try to determine what parameter this should be
                offset_match = re.search(r'offset_hex: "([^"]+)"', line)
                if offset_match:
                    offset_hex = offset_match.group(1)
                    
                    # Generate a placeholder name based on offset
                    param_name = f"Parameter_{offset_hex}"
                    
                    # Add the missing name entry
                    fixed_lines.append(f"        - name: \"{param_name}\"\n")
                    fixes_applied += 1
                    print(f"Fixed orphaned properties at line {i+1} with offset {offset_hex}")
        
        fixed_lines.append(line)
        i += 1
    
    # Write the fixed content
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"Applied {fixes_applied} fixes for orphaned properties")
    return fixes_applied

if __name__ == "__main__":
    filename = "roland_jv_1080_fixed.yaml"
    fixes = fix_orphaned_properties(filename)
    print(f"Orphaned property fixes completed: {fixes} fixes applied")
