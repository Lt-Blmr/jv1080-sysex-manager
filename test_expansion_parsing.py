#!/usr/bin/env python3
"""
Test script to verify expansion card parsing after adding 0x11 address mappings
"""

from sysex_parser import SysExParser
from pathlib import Path

def test_expansion_card_parsing():
    """Test parsing of a single expansion card file."""
    parser = SysExParser()
    
    # Test with Vintage1.syx
    file_path = "sysex_files/Vintage1.syx"
    
    print(f"Testing expansion card parsing with: {file_path}")
    print(f"Address lookup table size: {len(parser.address_lookup)}")
    
    # Show some expansion card addresses in lookup table
    expansion_addresses = [(addr, info) for addr, info in parser.address_lookup.items() 
                          if addr[0] == 0x11]
    print(f"Expansion card addresses in lookup: {len(expansion_addresses)}")
    
    if expansion_addresses:
        print("Sample expansion addresses:")
        for i, (addr, (group, param, info)) in enumerate(expansion_addresses[:10]):
            print(f"  {' '.join(f'{a:02X}' for a in addr)} -> {group}.{param}")
    
    # Parse the file
    try:
        parameters = parser.parse_sysex_file(file_path)
        print(f"\nSuccessfully parsed {len(parameters)} parameters")
        
        if parameters:
            # Show first few parameters
            print("\nFirst 10 parsed parameters:")
            for i, param in enumerate(parameters[:10]):
                print(f"  {param.group_name}.{param.parameter_name} = {param.value}")
                
            # Group by performance
            perf_groups = {}
            for param in parameters:
                if 'perf_' in param.group_name:
                    perf_num = param.group_name.split('_perf_')[1]
                    if perf_num not in perf_groups:
                        perf_groups[perf_num] = []
                    perf_groups[perf_num].append(param)
            
            print(f"\nFound parameters for {len(perf_groups)} performances")
            
            # Show first performance
            if perf_groups:
                first_perf = sorted(perf_groups.keys())[0]
                print(f"\nPerformance {first_perf} parameters:")
                for param in perf_groups[first_perf][:5]:
                    if 'name' in param.parameter_name.lower():
                        # Convert ASCII values to string for names
                        if isinstance(param.value, int):
                            char = chr(param.value) if 32 <= param.value <= 126 else '?'
                            print(f"  {param.parameter_name}: {param.value} ('{char}')")
                        else:
                            print(f"  {param.parameter_name}: {param.value}")
                    else:
                        print(f"  {param.parameter_name}: {param.value}")
        
    except Exception as e:
        print(f"Error parsing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_expansion_card_parsing()
    except Exception as e:
        print(f"Script error: {e}")
        import traceback
        traceback.print_exc()
