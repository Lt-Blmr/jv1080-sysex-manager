#!/usr/bin/env python3
"""
Append expansion_rhythm_part_5 through expansion_rhythm_part_64 to the existing YAML file.
"""

def generate_remaining_rhythm_parts():
    """Generate YAML content for rhythm parts 5-64."""
    
    # Base parameters template
    param_template = """        - name: "{name}"
          offset_hex: "{offset}"
          min: {min_val}
          max: {max_val}
          bytes: {bytes_val}"""
    
    # All parameters with their specifications
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
    
    # Generate content for parts 5-64
    content_lines = []
    
    for part_num in range(5, 65):  # Parts 5 through 64
        # Calculate address byte: part 1 = 0x23, part 5 = 0x27, ..., part 64 = 0x62
        address_byte = 0x23 + (part_num - 1)
        
        # Add part header
        content_lines.append(f"")
        content_lines.append(f"    expansion_rhythm_part_{part_num}:")
        content_lines.append(f'      description: "Expansion Card Rhythm Note Parameters"')
        content_lines.append(f'      default_device_id_hex: "10"')
        content_lines.append(f'      address_bytes_1_3_hex: ["11", "09", "{address_byte:02X}"]')
        content_lines.append(f'      parameters:')
        
        # Add all parameters
        for name, offset, min_val, max_val, bytes_val in parameters:
            content_lines.append(param_template.format(
                name=name, offset=offset, min_val=min_val, max_val=max_val, bytes_val=bytes_val
            ))
    
    return "\n".join(content_lines)

def main():
    """Append the remaining rhythm parts to the YAML file."""
    yaml_file = "roland_jv_1080_fixed.yaml"
    
    print(f"Generating expansion_rhythm_part_5 through expansion_rhythm_part_64...")
    content = generate_remaining_rhythm_parts()
    
    # Append to the existing file
    with open(yaml_file, "a", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Appended {60} rhythm part definitions (parts 5-64) to {yaml_file}")
    print(f"📏 Added {len(content.splitlines())} lines")
    
    # Verify file size
    with open(yaml_file, "r", encoding="utf-8") as f:
        total_lines = len(f.readlines())
    
    print(f"📊 Total lines in {yaml_file}: {total_lines}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
