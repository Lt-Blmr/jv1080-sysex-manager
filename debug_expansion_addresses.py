#!/usr/bin/env python3
"""
Debug script to examine expansion card SysEx addresses
"""

import sys
from pathlib import Path

def extract_sysex_messages(data: bytes):
    """Extract individual SysEx messages from binary data."""
    messages = []
    current_message = []
    in_sysex = False
    
    for byte in data:
        if byte == 0xF0:  # Start of SysEx
            if in_sysex and current_message:
                print("Warning: F0 found before F7")
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
    
    return messages

def analyze_expansion_addresses(file_path):
    """Analyze the first few SysEx messages to understand address structure."""
    print(f"\nAnalyzing: {file_path}")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    messages = extract_sysex_messages(data)
    print(f"Total messages found: {len(messages)}")
    
    # Analyze first 10 messages
    unique_addresses = set()
    for i, msg in enumerate(messages[:10]):
        if len(msg) >= 10:
            # F0 41 10 6A 12 [addr1] [addr2] [addr3] [addr4] [data...] [checksum] F7
            #  0  1  2  3  4     5      6      7      8      9...
            addr = tuple(msg[5:9])
            unique_addresses.add(addr)
            
            print(f"Message {i:3d}: {' '.join(f'{b:02X}' for b in msg[:15])}... "
                  f"Addr: {' '.join(f'{a:02X}' for a in addr)} "
                  f"Data: {msg[9]:02X}")
    
    print(f"\nUnique addresses in first 10 messages: {len(unique_addresses)}")
    for addr in sorted(unique_addresses):
        print(f"  {' '.join(f'{a:02X}' for a in addr)}")
    
    return unique_addresses

if __name__ == "__main__":
    # Analyze expansion card files
    expansion_files = [
        "sysex_files/Vintage1.syx",
        "sysex_files/Techno1.syx"
    ]
    
    all_addresses = set()
    try:
        for file_path in expansion_files:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                addresses = analyze_expansion_addresses(file_path)
                all_addresses.update(addresses)
            else:
                print(f"File not found: {file_path}")
        
        print(f"\n=== SUMMARY ===")
        print(f"All unique addresses found: {len(all_addresses)}")
        for addr in sorted(all_addresses):
            print(f"  {' '.join(f'{a:02X}' for a in addr)}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
