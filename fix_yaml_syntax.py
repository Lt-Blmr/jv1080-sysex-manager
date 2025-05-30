#!/usr/bin/env python3
"""
YAML Syntax Fixer for JV-1080 Configuration File
Fixes the specific syntax error at line 419 and validates the entire YAML structure.
"""

import yaml
import re
import sys
from pathlib import Path

def fix_yaml_syntax_errors(yaml_file_path):
    """
    Fix known YAML syntax errors in the JV-1080 configuration file.
    """
    print(f"🔧 Fixing YAML syntax errors in: {yaml_file_path}")
    
    # Read the file
    with open(yaml_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
      # Create backup
    backup_path = str(yaml_file_path).replace('.yaml', '_backup.yaml')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📦 Created backup: {backup_path}")
    
    # Split into lines for processing
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines, 1):
        # Fix the specific error at line 419: "bytes: 1        - name: "Chorus Level""
        if 'bytes: 1        - name:' in line:
            # Split this malformed line into two properly formatted lines
            parts = line.split('        - name:')
            if len(parts) == 2:
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(parts[0])  # "bytes: 1"
                fixed_lines.append(' ' * (indent - 8) + '- name:' + parts[1])  # Proper indentation for list item
                print(f"🔧 Fixed malformed line {i}: Split into two lines")
                continue
        
        # Fix any other similar issues where parameters are concatenated
        if re.search(r'bytes:\s*\d+\s+- name:', line):
            parts = re.split(r'(\s+- name:)', line)
            if len(parts) >= 3:
                indent = len(line) - len(line.lstrip())
                # First part: the "bytes: X" portion
                fixed_lines.append(parts[0])
                # Second part: the "- name:" portion with proper indentation
                remaining = ''.join(parts[1:])
                fixed_lines.append(' ' * (indent - 8) + remaining.strip())
                print(f"🔧 Fixed concatenated parameters at line {i}")
                continue
        
        # Fix missing quotes around parameter names
        if re.search(r'- name:\s+[^"\']\w+', line):
            fixed_line = re.sub(r'(- name:\s+)([^"\']\w+)', r'\1"\2"', line)
            if fixed_line != line:
                fixed_lines.append(fixed_line)
                print(f"🔧 Added quotes to parameter name at line {i}")
                continue
        
        # Fix indentation issues (ensure consistent 2-space indentation)
        if line.strip():
            # Count leading spaces
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 2 != 0 and leading_spaces > 0:
                # Fix odd indentation by adding one space
                line = ' ' + line
                print(f"🔧 Fixed indentation at line {i}")
        
        fixed_lines.append(line)
    
    # Join the fixed lines
    fixed_content = '\n'.join(fixed_lines)
    
    # Write the fixed content back
    with open(yaml_file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"✅ Fixed YAML syntax and saved to: {yaml_file_path}")
    return fixed_content

def validate_yaml_structure(yaml_file_path):
    """
    Validate the YAML structure and report any issues.
    """
    print(f"\n🔍 Validating YAML structure: {yaml_file_path}")
    
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        print("✅ YAML syntax is valid!")
        
        # Validate required sections
        required_sections = [
            'expansion_patch_common',
            'expansion_patch_part_1',
            'expansion_patch_part_2', 
            'expansion_patch_part_3',
            'expansion_patch_part_4',
            'expansion_performance_part_1',
            'expansion_performance_part_2',
            'expansion_performance_part_3',
            'expansion_performance_part_4'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in yaml_data:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️  Missing sections: {missing_sections}")
        else:
            print("✅ All required sections present!")
        
        # Validate rhythm parts (should have parts 2-64)
        rhythm_parts = [key for key in yaml_data.keys() if key.startswith('expansion_rhythm_part_')]
        expected_rhythm_parts = [f'expansion_rhythm_part_{i}' for i in range(2, 65)]
        
        missing_rhythm = [part for part in expected_rhythm_parts if part not in rhythm_parts]
        if missing_rhythm:
            print(f"⚠️  Missing rhythm parts: {len(missing_rhythm)} parts")
        else:
            print(f"✅ All 63 rhythm parts present (parts 2-64)!")
        
        # Validate parameter structure
        parameter_errors = []
        for section_name, section_data in yaml_data.items():
            if 'parameters' in section_data:
                for i, param in enumerate(section_data['parameters']):
                    if not isinstance(param, dict):
                        parameter_errors.append(f"{section_name}[{i}]: Parameter is not a dictionary")
                        continue
                    
                    required_param_fields = ['name', 'offset_hex', 'min', 'max', 'bytes']
                    for field in required_param_fields:
                        if field not in param:
                            parameter_errors.append(f"{section_name}[{i}]: Missing '{field}' field")
        
        if parameter_errors:
            print(f"⚠️  Parameter structure errors: {len(parameter_errors)}")
            for error in parameter_errors[:5]:  # Show first 5 errors
                print(f"    - {error}")
            if len(parameter_errors) > 5:
                print(f"    ... and {len(parameter_errors) - 5} more errors")
        else:
            print("✅ Parameter structure is valid!")
        
        return yaml_data, len(parameter_errors) == 0 and len(missing_sections) == 0
        
    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error: {e}")
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            print(f"   Error location: line {mark.line + 1}, column {mark.column + 1}")
        return None, False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None, False

def main():
    """
    Main function to fix and validate the YAML file.
    """
    yaml_file = Path("roland_jv_1080_fixed.yaml")
    
    if not yaml_file.exists():
        print(f"❌ YAML file not found: {yaml_file}")
        sys.exit(1)
    
    print("🚀 JV-1080 YAML Syntax Fixer and Validator")
    print("=" * 50)
    
    # Step 1: Fix syntax errors
    try:
        fixed_content = fix_yaml_syntax_errors(yaml_file)
    except Exception as e:
        print(f"❌ Error fixing YAML syntax: {e}")
        sys.exit(1)
    
    # Step 2: Validate structure
    yaml_data, is_valid = validate_yaml_structure(yaml_file)
    
    if is_valid:
        print("\n🎉 YAML file is now valid and ready to use!")
        
        # Summary statistics
        if yaml_data:
            total_sections = len(yaml_data)
            total_parameters = sum(len(section.get('parameters', [])) for section in yaml_data.values())
            print(f"\n📊 Summary:")
            print(f"   - Total sections: {total_sections}")
            print(f"   - Total parameters: {total_parameters}")
            print(f"   - File size: {yaml_file.stat().st_size:,} bytes")
    else:
        print("\n❌ YAML file still has issues that need manual review.")
        sys.exit(1)

if __name__ == "__main__":
    main()
