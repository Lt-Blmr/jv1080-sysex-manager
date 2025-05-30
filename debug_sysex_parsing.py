#!/usr/bin/env python3
"""
Debug SysEx Parsing Script
Analyzes the structure of expansion card SysEx files to understand why we're only getting performance names.
"""

import logging
from pathlib import Path
from sysex_parser import SysExParser

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_sysex_messages(file_path: str):
    """Analyze raw SysEx messages in a file."""
    print(f"=== Analyzing {file_path} ===")
    
    # Read binary data
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Extract SysEx messages manually
    messages = []
    current_message = []
    in_sysex = False
    
    for byte in data:
        if byte == 0xF0:  # Start of SysEx
            if in_sysex and current_message:
                print(f"Warning: Malformed SysEx - F0 found before F7")
            current_message = [byte]
            in_sysex = True
        elif byte == 0xF7:  # End of SysEx
            if in_sysex:
                current_message.append(byte)
                messages.append(current_message)
                current_message = []
                in_sysex = False
        elif in_sysex:
            current_message.append(byte)
    
    print(f"Found {len(messages)} SysEx messages")
    
    # Analyze first few messages
    roland_messages = []
    for i, msg in enumerate(messages[:10]):
        print(f"\nMessage {i}: {len(msg)} bytes")
        hex_msg = " ".join(f"{b:02X}" for b in msg)
        print(f"  Hex: {hex_msg}")
        
        if len(msg) >= 6:
            manufacturer = msg[1]
            device_id = msg[2] 
            model = msg[3]
            command = msg[4]
            
            print(f"  Manufacturer: {manufacturer:02X} ({'Roland' if manufacturer == 0x41 else 'Unknown'})")
            print(f"  Device ID: {device_id:02X}")
            print(f"  Model: {model:02X} ({'JV-1080' if model == 0x6A else 'Unknown'})")
            print(f"  Command: {command:02X} ({'DT1' if command == 0x12 else 'Other'})")
            
            if len(msg) >= 10:
                address = msg[5:9]
                data_bytes = msg[9:-2]  # Exclude checksum and F7
                
                print(f"  Address: {' '.join(f'{b:02X}' for b in address)}")
                print(f"  Data: {len(data_bytes)} bytes - {' '.join(f'{b:02X}' for b in data_bytes[:8])}{'...' if len(data_bytes) > 8 else ''}")
                
                # Check if this is expansion card space (0x11)
                if address[0] == 0x11:
                    perf_slot = address[1]
                    part_type = address[2]
                    offset = address[3]
                    print(f"    Expansion Card - Performance: {perf_slot}, Part Type: {part_type:02X}, Offset: {offset:02X}")
                    roland_messages.append((i, address, data_bytes))
    
    print(f"\n=== Summary ===")
    print(f"Total messages: {len(messages)}")
    expansion_msgs = [msg for msg in messages if len(msg) >= 9 and msg[5] == 0x11]
    print(f"Expansion card messages (0x11 address space): {len(expansion_msgs)}")
    
    # Analyze part types in expansion messages
    if expansion_msgs:
        part_types = {}
        for msg in expansion_msgs:
            if len(msg) >= 8:
                part_type = msg[7]  # address[2]
                part_types[part_type] = part_types.get(part_type, 0) + 1
        
        print("\nPart types found:")
        for part_type, count in sorted(part_types.items()):
            description = {
                0x00: "Performance Common",
                0x10: "Performance Part 1", 0x12: "Performance Part 2", 
                0x14: "Performance Part 3", 0x16: "Performance Part 4",
                0x20: "Patch Common",
                0x22: "Patch Part 1", 0x24: "Patch Part 2", 
                0x26: "Patch Part 3", 0x28: "Patch Part 4",
                0x60: "Rhythm Common"
            }.get(part_type, f"Unknown (0x{part_type:02X})")
            
            # Check for rhythm parts (0x24-0x62 range we generated)
            if 0x24 <= part_type <= 0x62:
                rhythm_part_num = part_type - 0x23
                description = f"Rhythm Part {rhythm_part_num}"
            
            print(f"  0x{part_type:02X}: {description} ({count} messages)")

def main():
    """Main analysis function."""
    sysex_dir = Path("sysex_files")
    
    # Test with both Vintage and Techno files
    test_files = ["Vintage1.syx", "Techno1.syx"]
    
    for filename in test_files:
        file_path = sysex_dir / filename
        if file_path.exists():
            analyze_sysex_messages(str(file_path))
            print("\n" + "="*60 + "\n")
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()
