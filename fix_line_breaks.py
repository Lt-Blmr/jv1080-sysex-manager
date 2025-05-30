#!/usr/bin/env python3
"""
Fix line break issues in the YAML file where 'bytes: N' and '- name:' are on the same line.
"""

import re

def fix_yaml_line_breaks(filepath):
    """Fix line break issues in YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all instances first
    pattern = r'(\s+bytes:\s*\d+)\s+(-\s+name:)'
    matches = re.findall(pattern, content)
    print(f"Found {len(matches)} instances to fix")
    
    # Fix pattern: bytes: N        - name: becomes bytes: N\n        - name:
    fixed_content = re.sub(pattern, r'\1\n        \2', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed line breaks in {filepath}")

if __name__ == "__main__":
    fix_yaml_line_breaks("roland_jv_1080_fixed.yaml")
