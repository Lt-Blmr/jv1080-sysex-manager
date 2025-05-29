#!/usr/bin/env python3
"""
Analyze the structure of expansion card SysEx messages to understand bulk data format
"""

def analyze_sysex_structure():
    """Analyze the raw structure of expansion card SysEx messages."""
    
    file_path = "sysex_files/Vintage1.syx"
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Extract first few messages
    messages = []
    current_message = []
    in_sysex = False
    
    for byte in data:
        if byte == 0xF0:
            if current_message:
                messages.append(current_message)
            current_message = [byte]
            in_sysex = True
        elif byte == 0xF7:
            if in_sysex:
                current_message.append(byte)
                messages.append(current_message)
                current_message = []
                in_sysex = False
        elif in_sysex:
            current_message.append(byte)
    
    print(f"Total messages: {len(messages)}")
    
    # Analyze first few messages in detail
    for i in range(min(5, len(messages))):
        msg = messages[i]
        print(f"\n--- Message {i} ---")
        print(f"Length: {len(msg)} bytes")
        print(f"Header: {' '.join(f'{b:02X}' for b in msg[:10])}")
        
        if len(msg) >= 10:
            # F0 41 10 6A 12 [addr1] [addr2] [addr3] [addr4] [data...]
            addr = msg[5:9]
            data_section = msg[9:-2]  # Exclude checksum and F7
            checksum = msg[-2]
            
            print(f"Address: {' '.join(f'{a:02X}' for a in addr)}")
            print(f"Data length: {len(data_section)} bytes")
            print(f"Checksum: {checksum:02X}")
            
            # For performance name messages (address ending in 00 00), show as text
            if addr[2] == 0x00 and addr[3] == 0x00:
                # First 12 bytes are typically the performance name
                name_bytes = data_section[:12]
                name_text = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in name_bytes)
                print(f"Performance name: '{name_text}'")
                print(f"First 20 data bytes: {' '.join(f'{b:02X}' for b in data_section[:20])}")
            else:
                print(f"First 20 data bytes: {' '.join(f'{b:02X}' for b in data_section[:20])}")

if __name__ == "__main__":
    try:
        analyze_sysex_structure()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
