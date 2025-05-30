#!/usr/bin/env python3

from sysex_parser import SysExParser
import yaml

# Load the YAML and check if performance part definitions are present
with open('roland_jv_1080_fixed.yaml', 'r') as f:
    config = yaml.safe_load(f)

groups = config['sysex_parameter_groups']
print('Available expansion performance part groups:')
perf_parts = [k for k in groups.keys() if 'performance_part' in k]
print(f"Found {len(perf_parts)} performance part groups")
for key in sorted(perf_parts):
    param_count = len(groups[key].get("parameters", []))
    print(f"  {key}: {param_count} parameters")

# Test the parser method
print("\nTesting parser method:")
parser = SysExParser('roland_jv_1080_fixed.yaml')
for part_num in [1, 2, 3, 4]:
    part_defs = parser._get_part_parameter_definitions(part_num)
    print(f"Part {part_num} definitions: {len(part_defs)} parameters")
    if part_defs:
        param_names = list(part_defs.keys())[:3]
        print(f"  Sample parameters: {param_names}")
