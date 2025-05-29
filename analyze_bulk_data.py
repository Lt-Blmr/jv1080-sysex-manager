#!/usr/bin/env python3
"""
Analyze bulk data structure in expansion card SysEx files.
"""

def analyze_message(msg_bytes, message_num):
    """Analyze a single SysEx message structure."""
    print(f"\n=== Message {message_num} Analysis ===")
    print(f"Total length: {len(msg_bytes)} bytes")
    
    # Extract components
    header = msg_bytes[:5]  # F0 41 10 6A 12
    address = msg_bytes[5:9]
    data = msg_bytes[9:-2]
    checksum = msg_bytes[-2]
    end = msg_bytes[-1]
    
    print(f"Header: {[hex(x) for x in header]}")
    print(f"Address: {[hex(x) for x in address]} - {address}")
    print(f"Data length: {len(data)} bytes")
    print(f"Checksum: {hex(checksum)}")
    print(f"End: {hex(end)}")
    
    # Address breakdown
    addr_space, perf_slot, part_type, offset = address
    print(f"  Address space: {hex(addr_space)} ({'expansion card' if addr_space == 0x11 else 'internal'})")
    print(f"  Performance slot: {hex(perf_slot)} ({perf_slot})")
    print(f"  Part type: {hex(part_type)} ({'common' if part_type == 0x00 else f'part {(part_type-0x10)//2+1}' if part_type >= 0x10 else 'unknown'})")
    print(f"  Offset: {hex(offset)} ({offset})")
    
    # Data analysis
    if part_type == 0x00:  # Common parameters (performance name area)
        # First 12 bytes should be performance name
        name_bytes = data[:12]
        name = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in name_bytes)
        print(f"  Performance name: '{name.strip()}'")
        print(f"  Name bytes: {[hex(x) for x in name_bytes]}")
        
        # Rest are common parameters
        if len(data) > 12:
            print(f"  Common parameters: {len(data)-12} bytes")
            print(f"  First 16 param bytes: {[hex(x) for x in data[12:28]]}")
    
    elif part_type in [0x10, 0x12, 0x14, 0x16]:  # Part parameters
        part_num = (part_type - 0x10) // 2 + 1
        print(f"  Part {part_num} parameters: {len(data)} bytes")
        print(f"  First 16 bytes: {[hex(x) for x in data[:16]]}")
        print(f"  Last 16 bytes: {[hex(x) for x in data[-16:]]}")
    
    return {
        'address': address,
        'data_length': len(data),
        'address_space': addr_space,
        'performance_slot': perf_slot,
        'part_type': part_type,
        'offset': offset,
        'data': data
    }

def main():
    with open('sysex_files/Vintage1.syx', 'rb') as f:
        data = f.read()
    
    # Extract first 10 messages
    pos = 0
    messages = []
    while pos < len(data) and len(messages) < 10:
        if data[pos] == 0xF0:
            start = pos
            pos += 1
            while pos < len(data) and data[pos] != 0xF7:
                pos += 1
            if pos < len(data):
                pos += 1  # Include F7
                messages.append(data[start:pos])
        else:
            pos += 1
    
    print(f"Analyzing first {len(messages)} messages from Vintage1.syx")
    
    message_info = []
    for i, msg in enumerate(messages):
        msg_bytes = list(msg)
        info = analyze_message(msg_bytes, i+1)
        message_info.append(info)
    
    # Summary
    print("\n=== SUMMARY ===")
    print("Message patterns found:")
    for info in message_info:
        addr = info['address']
        print(f"  {[hex(x) for x in addr]} -> {info['data_length']} bytes")
    
    # Group by performance slot
    perf_slots = {}
    for info in message_info:
        slot = info['performance_slot']
        if slot not in perf_slots:
            perf_slots[slot] = []
        perf_slots[slot].append(info)
    
    print(f"\nPerformance slots found: {sorted(perf_slots.keys())}")
    for slot in sorted(perf_slots.keys()):
        messages = perf_slots[slot]
        print(f"  Slot {slot}: {len(messages)} messages")
        for msg in messages:
            part_type = msg['part_type']
            if part_type == 0x00:
                part_name = "common"
            elif part_type in [0x10, 0x12, 0x14, 0x16]:
                part_name = f"part_{(part_type-0x10)//2+1}"
            else:
                part_name = f"unknown_{hex(part_type)}"
            print(f"    {part_name}: {msg['data_length']} bytes")

if __name__ == "__main__":
    main()
