#!/usr/bin/env python3
"""
Test script for bulk data parsing of expansion card SysEx files.
"""

from sysex_parser import SysExParser
from pathlib import Path

def test_bulk_parsing():
    """Test the new bulk data parsing functionality."""
    
    # Initialize parser
    parser = SysExParser('roland_jv_1080.yaml')
    
    # Test with Vintage1.syx
    sysex_file = Path('sysex_files/Vintage1.syx')
    
    if not sysex_file.exists():
        print(f"Error: {sysex_file} not found")
        return
    
    print(f"Testing bulk data parsing with {sysex_file}")
    print("=" * 60)
    
    # Parse the file
    parameters = parser.parse_sysex_file(sysex_file)
    
    print(f"Total parameters parsed: {len(parameters)}")
    
    # Group by performance slot
    perf_slots = {}
    for param in parameters:
        # Extract performance slot from group name
        if 'perf_' in param.group_name:
            slot_part = param.group_name.split('perf_')[1]
            slot_num = int(slot_part.split('_')[0]) if '_' in slot_part else int(slot_part[:2])
            
            if slot_num not in perf_slots:
                perf_slots[slot_num] = {
                    'common': [],
                    'part_1': [],
                    'part_2': [],
                    'part_3': [],
                    'part_4': []
                }
            
            if 'common' in param.group_name:
                perf_slots[slot_num]['common'].append(param)
            elif 'part_1' in param.group_name:
                perf_slots[slot_num]['part_1'].append(param)
            elif 'part_2' in param.group_name:
                perf_slots[slot_num]['part_2'].append(param)
            elif 'part_3' in param.group_name:
                perf_slots[slot_num]['part_3'].append(param)
            elif 'part_4' in param.group_name:
                perf_slots[slot_num]['part_4'].append(param)
    
    print(f"Performance slots found: {sorted(perf_slots.keys())}")
    
    # Show details for first few performances
    for slot in sorted(perf_slots.keys())[:3]:  # Show first 3 performances
        print(f"\n--- Performance Slot {slot} ---")
        
        # Show performance name
        common_params = perf_slots[slot]['common']
        name_param = next((p for p in common_params if 'name' in p.parameter_name.lower()), None)
        if name_param:
            if isinstance(name_param.value, list):
                # Convert byte list to string
                name = ''.join(chr(b) if 32 <= b <= 126 else ' ' for b in name_param.value).strip()
                print(f"  Name: '{name}'")
            else:
                print(f"  Name: {name_param.value}")
        
        # Show parameter counts
        print(f"  Common parameters: {len(common_params)}")
        print(f"  Part 1 parameters: {len(perf_slots[slot]['part_1'])}")
        print(f"  Part 2 parameters: {len(perf_slots[slot]['part_2'])}")
        print(f"  Part 3 parameters: {len(perf_slots[slot]['part_3'])}")
        print(f"  Part 4 parameters: {len(perf_slots[slot]['part_4'])}")
        
        # Show a few sample parameters
        if common_params:
            print("  Sample common parameters:")
            for param in common_params[:5]:  # First 5 common params
                print(f"    {param.parameter_name}: {param.value}")
        
        if perf_slots[slot]['part_1']:
            print("  Sample part 1 parameters:")
            for param in perf_slots[slot]['part_1'][:3]:  # First 3 part params
                print(f"    {param.parameter_name}: {param.value}")
    
    # Overall statistics
    print(f"\n--- Summary ---")
    total_performances = len(perf_slots)
    total_common = sum(len(slot['common']) for slot in perf_slots.values())
    total_part_params = sum(
        len(slot['part_1']) + len(slot['part_2']) + len(slot['part_3']) + len(slot['part_4'])
        for slot in perf_slots.values()
    )
    
    print(f"Total performances: {total_performances}")
    print(f"Total common parameters: {total_common}")
    print(f"Total part parameters: {total_part_params}")
    print(f"Average parameters per performance: {(total_common + total_part_params) / total_performances:.1f}")

if __name__ == "__main__":
    test_bulk_parsing()
