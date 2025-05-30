#!/usr/bin/env python3
"""
YAML Verification Script for roland_jv_1080_fixed.yaml
Checks for syntax errors and provides detailed error reporting.
"""

import yaml
import sys
from pathlib import Path

def verify_yaml_file(filepath):
    """
    Verify YAML file syntax and report errors with line numbers.
    
    Args:
        filepath: Path to the YAML file to verify
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Try to parse the YAML
        config = yaml.safe_load(content)
        print(f"✅ YAML file '{filepath}' is valid!")
        
        # Basic structure validation
        if not isinstance(config, dict):
            return False, "Root element must be a dictionary"
            
        # Check for required top-level keys
        required_keys = ['jv1080_config', 'sysex_parameter_groups']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            return False, f"Missing required top-level keys: {missing_keys}"
            
        # Count parameter groups
        groups = config.get('sysex_parameter_groups', {})
        print(f"📊 Found {len(groups)} parameter groups:")
        
        # Categorize groups
        categories = {
            'temp_': 0,
            'expansion_performance_': 0,
            'expansion_patch_': 0,
            'expansion_rhythm_': 0,
            'other': 0
        }
        
        for group_name in groups.keys():
            categorized = False
            for prefix in categories.keys():
                if prefix != 'other' and group_name.startswith(prefix):
                    categories[prefix] += 1
                    categorized = True
                    break
            if not categorized:
                categories['other'] += 1
                
        for category, count in categories.items():
            if count > 0:
                print(f"  - {category.replace('_', ' ').title().strip()}: {count}")
                
        return True, "YAML file is valid"
        
    except yaml.YAMLError as e:
        error_msg = f"YAML Syntax Error: {str(e)}"
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            error_msg += f"\n  Line {mark.line + 1}, Column {mark.column + 1}"
            
            # Try to show the problematic line
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if mark.line < len(lines):
                    problem_line = lines[mark.line].rstrip()
                    error_msg += f"\n  Problem line: {problem_line}"
                    error_msg += f"\n  Problem area: {' ' * mark.column}^"
            except:
                pass
                
        return False, error_msg
        
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def find_common_yaml_issues(filepath):
    """
    Scan for common YAML issues that might not be caught by the parser.
    """
    print("\n🔍 Scanning for common YAML issues...")
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            line_stripped = line.rstrip()
            
            # Check for tabs (should use spaces)
            if '\t' in line:
                issues.append(f"Line {i}: Contains tab characters (use spaces instead)")
                
            # Check for trailing spaces after colons
            if line_stripped.endswith(':'):
                next_line_idx = i
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    if next_line and not next_line.startswith('-') and not next_line.startswith('#'):
                        # Check indentation
                        current_indent = len(line) - len(line.lstrip())
                        next_indent = len(lines[next_line_idx]) - len(lines[next_line_idx].lstrip())
                        if next_indent <= current_indent:
                            issues.append(f"Line {i}: Possible indentation issue after '{line_stripped}'")
            
            # Check for missing spaces after colons
            if ':' in line and not line.strip().startswith('#'):
                colon_pos = line.find(':')
                if colon_pos != -1 and colon_pos < len(line) - 1:
                    char_after_colon = line[colon_pos + 1]
                    if char_after_colon not in [' ', '\n', '\r']:
                        issues.append(f"Line {i}: Missing space after colon")
                        
            # Check for inconsistent list formatting
            if line.strip().startswith('-'):
                if not line.strip().startswith('- ') and len(line.strip()) > 1:
                    issues.append(f"Line {i}: Missing space after list marker '-'")
                    
        if issues:
            print("⚠️  Found potential issues:")
            for issue in issues[:10]:  # Show first 10 issues
                print(f"  {issue}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more issues")
        else:
            print("✅ No common YAML issues found")
            
    except Exception as e:
        print(f"❌ Error scanning file: {e}")

def main():
    """Main verification function."""
    yaml_file = Path("roland_jv_1080_fixed.yaml")
    
    if not yaml_file.exists():
        print(f"❌ File '{yaml_file}' not found!")
        return 1
        
    print(f"🔍 Verifying YAML file: {yaml_file}")
    print("=" * 60)
    
    # Verify YAML syntax
    is_valid, message = verify_yaml_file(yaml_file)
    
    if is_valid:
        print(f"✅ {message}")
        
        # Look for common issues
        find_common_yaml_issues(yaml_file)
        
        print("\n🎉 YAML verification completed successfully!")
        return 0
    else:
        print(f"❌ {message}")
        
        # Still check for common issues to help with debugging
        find_common_yaml_issues(yaml_file)
        
        print("\n💡 Tips for fixing YAML errors:")
        print("  - Ensure proper indentation (use spaces, not tabs)")
        print("  - Check for missing spaces after colons (:)")
        print("  - Verify that lists use proper formatting (- item)")
        print("  - Make sure quotes are properly closed")
        print("  - Check for special characters that need escaping")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
