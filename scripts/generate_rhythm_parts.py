#!/usr/bin/env python3
"""
Generate expansion_rhythm_part_2 through expansion_rhythm_part_64 for JV-1080 YAML configuration.
Based on the structure of expansion_rhythm_part_1, incrementing the address byte from 0x24 to 0x62.
"""

def generate_rhythm_parts():
    """Generate YAML definitions for rhythm parts 2-64."""
    
    # Base parameters from expansion_rhythm_part_1
    parameters = [
        {"name": "Tone Switch", "offset_hex": "00", "min": 0, "max": 1, "bytes": 1},
        {"name": "Wave Group Type", "offset_hex": "01", "min": 0, "max": 2, "bytes": 1},
        {"name": "Wave Group ID", "offset_hex": "02", "min": 0, "max": 127, "bytes": 1},
        {"name": "Wave Number", "offset_hex": "03", "min": 0, "max": 254, "bytes": 1},
        {"name": "Wave Gain", "offset_hex": "05", "min": 0, "max": 3, "bytes": 1},
        {"name": "Bend Range", "offset_hex": "06", "min": 0, "max": 12, "bytes": 1},
        {"name": "Mute Group", "offset_hex": "07", "min": 0, "max": 31, "bytes": 1},
        {"name": "Envelope Mode", "offset_hex": "08", "min": 0, "max": 1, "bytes": 1},
        {"name": "Volume Control Switch", "offset_hex": "09", "min": 0, "max": 1, "bytes": 1},
        {"name": "Hold-1 Control Switch", "offset_hex": "0A", "min": 0, "max": 1, "bytes": 1},
        {"name": "Pan Control Switch", "offset_hex": "0B", "min": 0, "max": 2, "bytes": 1},
        {"name": "Coarse Tune", "offset_hex": "0C", "min": 0, "max": 127, "bytes": 1},
        {"name": "Fine Tune", "offset_hex": "0D", "min": 0, "max": 100, "bytes": 1},
        {"name": "Random Pitch Depth", "offset_hex": "0E", "min": 0, "max": 30, "bytes": 1},
        {"name": "Pitch Envelope Depth", "offset_hex": "0F", "min": 0, "max": 24, "bytes": 1},
        {"name": "Pitch Envelope Velocity Sens", "offset_hex": "10", "min": -100, "max": 150, "bytes": 1},
        {"name": "Pitch Envelope Velocity Time", "offset_hex": "11", "min": -100, "max": 100, "bytes": 1},
        {"name": "Pitch Envelope Time 1", "offset_hex": "12", "min": 0, "max": 127, "bytes": 1},
        {"name": "Pitch Envelope Time 2", "offset_hex": "13", "min": 0, "max": 127, "bytes": 1},
        {"name": "Pitch Envelope Time 3", "offset_hex": "14", "min": 0, "max": 127, "bytes": 1},
        {"name": "Pitch Envelope Time 4", "offset_hex": "15", "min": 0, "max": 127, "bytes": 1},
        {"name": "Pitch Envelope Level 1", "offset_hex": "16", "min": 0, "max": 126, "bytes": 1},
        {"name": "Pitch Envelope Level 2", "offset_hex": "17", "min": 0, "max": 126, "bytes": 1},
        {"name": "Pitch Envelope Level 3", "offset_hex": "18", "min": 0, "max": 126, "bytes": 1},
        {"name": "Pitch Envelope Level 4", "offset_hex": "19", "min": 0, "max": 126, "bytes": 1},
        {"name": "Filter Type", "offset_hex": "1A", "min": 0, "max": 4, "bytes": 1},
        {"name": "Cutoff Frequency", "offset_hex": "1B", "min": 0, "max": 127, "bytes": 1},
        {"name": "Resonance", "offset_hex": "1C", "min": 0, "max": 127, "bytes": 1},
        {"name": "Resonance Velocity Sens", "offset_hex": "1D", "min": -100, "max": 150, "bytes": 1},
        {"name": "Filter Envelope Depth", "offset_hex": "1E", "min": 0, "max": 126, "bytes": 1},
        {"name": "Filter Envelope Velocity Sens", "offset_hex": "1F", "min": -100, "max": 150, "bytes": 1}
    ]
    
    # Generate YAML content for parts 2-64
    yaml_content = []
    
    for part_num in range(2, 65):  # Parts 2 through 64
        # Calculate address byte: part 1 = 0x23, part 2 = 0x24, ..., part 64 = 0x62
        address_byte = 0x23 + (part_num - 1)
        
        yaml_content.append(f"    expansion_rhythm_part_{part_num}:")
        yaml_content.append(f'      description: "Expansion Card Rhythm Note Parameters"')
        yaml_content.append(f'      default_device_id_hex: "10"')
        yaml_content.append(f'      address_bytes_1_3_hex: ["11", "09", "{address_byte:02X}"]')
        yaml_content.append(f'      parameters:')
        
        # Add all parameters
        for param in parameters:
            yaml_content.append(f'        - name: "{param["name"]}"')
            yaml_content.append(f'          offset_hex: "{param["offset_hex"]}"')
            yaml_content.append(f'          min: {param["min"]}')
            yaml_content.append(f'          max: {param["max"]}')
            yaml_content.append(f'          bytes: {param["bytes"]}')
        
        # Add spacing between parts (except for the last one)
        if part_num < 64:
            yaml_content.append("")
    
    return "\n".join(yaml_content)

def main():
    """Generate and save the rhythm parts YAML."""
    print("Generating expansion_rhythm_part_2 through expansion_rhythm_part_64...")
    
    yaml_content = generate_rhythm_parts()
    
    # Save to file
    output_file = "expansion_rhythm_parts_2_to_64.yaml"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    print(f"✅ Generated rhythm parts saved to: {output_file}")
    print(f"📊 Generated {63} rhythm part definitions (parts 2-64)")
    print(f"📏 Total lines: {len(yaml_content.splitlines())}")
    
    # Show a sample of the generated content
    lines = yaml_content.splitlines()
    print(f"\n📝 Sample (first 20 lines):")
    for line in lines[:20]:
        print(f"  {line}")
    
    print(f"\n📝 Sample (last 20 lines):")
    for line in lines[-20:]:
        print(f"  {line}")

if __name__ == "__main__":
    main()
