#!/usr/bin/env python3
"""
Comprehensive YAML fixer for roland_jv_1080_fixed.yaml
Fixes indentation, quotes, and structural issues.
"""

import re
import yaml

def fix_yaml_comprehensively(filepath):
    """Fix all systematic YAML issues."""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Starting comprehensive YAML fixes...")
    
    # 1. Fix line breaks where bytes: N and - name: are on same line
    pattern1 = r'(\s+bytes:\s*\d+)\s+(-\s+name:)'
    matches1 = len(re.findall(pattern1, content))
    print(f"Fixing {matches1} line break issues...")
    content = re.sub(pattern1, r'\1\n        \2', content)
    
    # 2. Fix indentation for offset_hex, min, max, bytes that should be under parameters
    # Pattern: lines that start with offset_hex, min, max, bytes but aren't properly indented
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this line should be indented as a parameter property
        if (stripped.startswith('offset_hex:') or 
            stripped.startswith('min:') or 
            stripped.startswith('max:') or 
            stripped.startswith('bytes:')):
            
            # Check if previous line was a - name: entry
            if i > 0:
                prev_line = lines[i-1].strip()
                if prev_line.startswith('- name:') or any(lines[j].strip().startswith('- name:') for j in range(max(0, i-5), i)):
                    # This should be indented to 10 spaces (under the - name: item)
                    if not line.startswith('          '):
                        line = '          ' + stripped
                        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # 3. Fix missing quotes around names
    # Pattern: - name: Text without quotes
    pattern3 = r'(-\s+name:\s+)([^"\n]+?)(\n|\s+offset_hex:)'
    
    def fix_name_quotes(match):
        prefix = match.group(1)
        name_text = match.group(2).strip()
        suffix = match.group(3)
        
        # If it doesn't start and end with quotes, add them
        if not (name_text.startswith('"') and name_text.endswith('"')):
            # Remove any existing quotes that might be malformed
            name_text = name_text.replace('"', '')
            name_text = f'"{name_text}"'
        
        return prefix + name_text + suffix
    
    matches3 = len(re.findall(pattern3, content))
    print(f"Fixing {matches3} missing quote issues...")
    content = re.sub(pattern3, fix_name_quotes, content)
    
    # 4. Fix malformed quoted names like "Pitch" Bend Range Up
    pattern4 = r'("[\w\s]+?")(\s+[\w\s]+?)(?=\n|\s+offset_hex:)'
    
    def fix_malformed_quotes(match):
        quoted_part = match.group(1)
        unquoted_part = match.group(2).strip()
        
        # Combine and properly quote
        full_name = quoted_part[1:-1] + ' ' + unquoted_part  # Remove quotes and combine
        return f'"{full_name}"'
    
    matches4 = len(re.findall(pattern4, content))
    print(f"Fixing {matches4} malformed quote issues...")
    content = re.sub(pattern4, fix_malformed_quotes, content)
    
    # 5. Ensure consistent spacing and structure
    # Fix cases where parameters are not properly indented under a list item
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # If this is a parameter property line that's not properly indented
        if (line.strip().startswith(('offset_hex:', 'min:', 'max:', 'bytes:')) and 
            not line.startswith('          ')):
            
            # Look backwards to find the most recent - name: line
            found_name = False
            for j in range(i-1, max(0, i-10), -1):
                if lines[j].strip().startswith('- name:'):
                    found_name = True
                    break
            
            if found_name:
                # Ensure proper indentation (10 spaces)
                line = '          ' + line.strip()
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Write the fixed content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed all systematic YAML issues")
    
    # Try to validate the YAML
    try:
        yaml.safe_load(content)
        print("✅ YAML is now valid!")
        return True
    except yaml.YAMLError as e:
        print(f"⚠️ YAML still has issues: {e}")
        return False

if __name__ == "__main__":
    fix_yaml_comprehensively("roland_jv_1080_fixed.yaml")
