import yaml
import sys

print("Starting YAML verification...")

try:
    with open('roland_jv_1080_fixed.yaml', 'r', encoding='utf-8') as f:
        print("File opened successfully")
        config = yaml.safe_load(f)
        print("YAML parsed successfully!")
        
        groups = config.get('sysex_parameter_groups', {})
        print(f"Found {len(groups)} parameter groups")
        
        # Check for performance parts
        perf_parts = [k for k in groups.keys() if 'performance_part' in k]
        print(f"Performance part groups: {len(perf_parts)}")
        for part in sorted(perf_parts):
            params = len(groups[part].get('parameters', []))
            print(f"  {part}: {params} parameters")
            
except yaml.YAMLError as e:
    print(f"YAML Error: {e}")
    if hasattr(e, 'problem_mark'):
        mark = e.problem_mark
        print(f"Line {mark.line + 1}, Column {mark.column + 1}")
except Exception as e:
    print(f"Error: {e}")
    
print("Verification complete.")
