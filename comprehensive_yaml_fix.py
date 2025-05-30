#!/usr/bin/env python3
"""
Comprehensive YAML Fixer for Roland JV-1080 Configuration
Fixes common YAML issues including negative number quoting and formatting
"""

import re
import yaml
from pathlib import Path

def fix_yaml_file(input_file):
    """Fix YAML formatting issues"""
    
    # Create backup
    backup_file = input_file.with_suffix('.yaml.backup')
    print(f"Creating backup: {backup_file}")
    backup_file.write_text(input_file.read_text(encoding='utf-8'), encoding='utf-8')
    
    # Read content
    content = input_file.read_text(encoding='utf-8')
    
    print("Fixing YAML formatting issues...")
    
    # Fix 1: Ensure negative numbers are properly quoted
    print("  - Quoting negative numbers...")
    content = re.sub(r'min:\s*(-\d+)', r'min: "\1"', content)
    content = re.sub(r'max:\s*(-\d+)', r'max: "\1"', content)
    
    # Fix 2: Ensure consistent spacing around colons
    print("  - Fixing colon spacing...")
    content = re.sub(r'(\w+):\s*"', r'\1: "', content)
    content = re.sub(r'(\w+):\s*(\d+)', r'\1: \2', content)
    
    # Fix 3: Fix any line break issues (concatenated lines)
    print("  - Fixing line break issues...")
    content = re.sub(r'bytes:\s*1\s*-\s*name:', 'bytes: 1\n        - name:', content)
    content = re.sub(r'bytes:\s*1\s*#', 'bytes: 1\n        #', content)
    
    # Fix 4: Ensure proper indentation (replace tabs with spaces)
    print("  - Normalizing indentation...")
    content = content.replace('\t', '  ')
    
    # Fix 5: Remove any trailing whitespace
    print("  - Removing trailing whitespace...")
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)
    
    # Fix 6: Ensure proper YAML structure (add quotes around description values if missing)
    print("  - Ensuring proper string quoting...")
    content = re.sub(r'description:\s*([^"\n][^:\n]*?)(?=\n)', r'description: "\1"', content)
    
    # Write fixed content
    print(f"Writing fixed content to: {input_file}")
    input_file.write_text(content, encoding='utf-8')
    
    # Validate YAML
    print("Validating YAML syntax...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print("✅ YAML syntax is valid!")
        return True
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        
        # Restore from backup if validation fails
        print(f"Restoring from backup: {backup_file}")
        input_file.write_text(backup_file.read_text(encoding='utf-8'), encoding='utf-8')
        return False

def main():
    yaml_file = Path("roland_jv_1080_fixed.yaml")
    
    if not yaml_file.exists():
        print(f"Error: {yaml_file} not found!")
        return
    
    print(f"Processing: {yaml_file}")
    success = fix_yaml_file(yaml_file)
    
    if success:
        print("\n🎉 YAML file successfully fixed and validated!")
    else:
        print("\n❌ Failed to fix YAML file - restored from backup")

if __name__ == "__main__":
    main()
