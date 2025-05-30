#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate expansion_rhythm_part_2 through expansion_rhythm_part_64 for JV-1080 YAML configuration.
"""

def generate_rhythm_parts():
    """Generate YAML definitions for rhythm parts 2-64."""
    
    # Base parameters from expansion_rhythm_part_1
    parameters = [
        ("Tone Switch", "00", 0, 1, 1),
        ("Wave Group Type", "01", 0, 2, 1),
        ("Wave Group ID", "02", 0, 127, 1),
        ("Wave Number", "03", 0, 254, 1),
        ("Wave Gain", "05", 0, 3, 1),
        ("Bend Range", "06", 0, 12, 1),
        ("Mute Group", "07", 0, 31, 1),
        ("Envelope Mode", "08", 0, 1, 1),
        ("Volume Control Switch", "09", 0, 1, 1),
        ("Hold-1 Control Switch", "0A", 0, 1, 1),
        ("Pan Control Switch", "0B", 0, 2, 1),
        ("Coarse Tune", "0C", 0, 127, 1),
        ("Fine Tune", "0D", 0, 100, 1),
        ("Random Pitch Depth", "0E", 0, 30, 1),
        ("Pitch Envelope Depth", "0F", 0, 24, 1),
        ("Pitch Envelope Velocity Sens", "10", -100, 150, 1),
        ("Pitch Envelope Velocity Time", "11", -100, 100, 1),
        ("Pitch Envelope Time 1", "12", 0, 127, 1),
        ("Pitch Envelope Time 2", "13", 0, 127, 1),
        ("Pitch Envelope Time 3", "14", 0, 127, 1),
        ("Pitch Envelope Time 4", "15", 0, 127, 1),
        ("Pitch Envelope Level 1", "16", 0, 126, 1),
        ("Pitch Envelope Level 2", "17", 0, 126, 1),
        ("Pitch Envelope Level 3", "18", 0, 126, 1),
        ("Pitch Envelope Level 4", "19", 0, 126, 1),
        ("Filter Type", "1A", 0, 4, 1),
        ("Cutoff Frequency", "1B", 0, 127, 1),
        ("Resonance", "1C", 0, 127, 1),
        ("Resonance Velocity Sens", "1D", -100, 150, 1),
        ("Filter Envelope Depth", "1E", 0, 126, 1),
        ("Filter Envelope Velocity Sens", "1F", -100, 150, 1)
    ]
    
    # Generate YAML content for parts 2-64
    lines = []
    
    for part_num in range(2, 65):  # Parts 2 through 64
        # Calculate address byte: part 1 = 0x23, part 2 = 0x24, ..., part 64 = 0x62
        address_byte = 0x23 + (part_num - 1)
        
        lines.append(f"    expansion_rhythm_part_{part_num}:")
        lines.append(f'      description: "Expansion Card Rhythm Note Parameters"')
        lines.append(f'      default_device_id_hex: "10"')
        lines.append(f'      address_bytes_1_3_hex: ["11", "09", "{address_byte:02X}"]')
        lines.append(f'      parameters:')
        
        # Add all parameters
        for name, offset, min_val, max_val, bytes_val in parameters:
            lines.append(f'        - name: "{name}"')
            lines.append(f'          offset_hex: "{offset}"')
            lines.append(f'          min: {min_val}')
            lines.append(f'          max: {max_val}')
            lines.append(f'          bytes: {bytes_val}')
        
        # Add spacing between parts (except for the last one)
        if part_num < 64:
            lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    print("Generating expansion_rhythm_part_2 through expansion_rhythm_part_64...")
    
    content = generate_rhythm_parts()
    
    # Save to file
    with open("expansion_rhythm_parts_2_to_64.yaml", "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Generated rhythm parts saved to: expansion_rhythm_parts_2_to_64.yaml")
    print(f"Generated {63} rhythm part definitions (parts 2-64)")
    print(f"Total lines: {len(content.splitlines())}")
