"""
Script to generate Expansion Card YAML sections for patch parts and rhythm parts in roland_jv_1080_fixed.yaml.
Usage: python scripts/generate_expansion_yaml.py > generated_expansion_parts.yaml
"""
import yaml

def to_hex(n): return f"{n:02X}"

# Definitions for patch-part parameters offsets 0x05-0x1F
patch_part_params = [
    (0x05, "Expression", 0, 127),
    (0x06, "Pitch Bend Range Up", 0, 12),
    (0x07, "Pitch Bend Range Down", 0, 48),
    (0x08, "Key Assign Mode", 0, 1),
    (0x09, "Solo Legato", 0, 1),
    (0x0A, "Portamento Switch", 0, 1),
    (0x0B, "Portamento Time", 0, 127),
    (0x0C, "Portamento Start", 0, 1),
    (0x0D, "Filter Cutoff Frequency", 0, 127),
    (0x0E, "Filter Resonance", 0, 127),
    (0x0F, "Filter Envelope Depth", 0, 126),
    (0x10, "Filter Envelope Time 1", 0, 127),
    (0x11, "Filter Envelope Time 2", 0, 127),
    (0x12, "Filter Envelope Time 3", 0, 127),
    (0x13, "Filter Envelope Time 4", 0, 127),
    (0x14, "Filter Envelope Level 1", 0, 126),
    (0x15, "Filter Envelope Level 2", 0, 126),
    (0x16, "LFO Waveform", 0, 7),
    (0x17, "LFO Rate", 0, 127),
    (0x18, "LFO Delay Time", 0, 127),
    (0x19, "LFO Depth", 0, 126),
    (0x1A, "Chorus Send Level", 0, 127),
    (0x1B, "Reverb Send Level", 0, 127),
    (0x1C, "Volume", 0, 127),
    (0x1D, "Pan", 0, 127),
    (0x1E, "Priority", 0, 1),
    (0x1F, "Pan Key Follow", 0, 14),
]

# Function to render parameters block

def make_params(address3_hex):
    params = []
    # offsets 00-04 are bank, program, level, pan
    for name, off, mn, mx in [
        ("Bank MSB", 0x00, 0, 127),
        ("Bank LSB", 0x01, 0, 127),
        ("Program Change", 0x02, 0, 127),
        ("Level", 0x03, 0, 127),
        ("Pan", 0x04, 1, 127),
    ]:
        params.append({"name": name, "offset_hex": to_hex(off), "min": mn, "max": mx, "bytes": 1})
    for off, name, mn, mx in [(p[0], p[1], p[2], p[3]) for p in patch_part_params]:
        params.append({"name": name, "offset_hex": to_hex(off), "min": mn, "max": mx, "bytes": 1})
    return params

# Generate patch parts
output = {'expansion_patch_parts': {}}
for part in range(1,5):
    addr3 = 0x20 + 0x02*part  # 0x22,24,26,28
    key = f"expansion_patch_part_{part}"
    output['expansion_patch_parts'][key] = {
        'description': f"Expansion Card Patch Part {part} Parameters",
        'default_device_id_hex': "10",
        'address_bytes_1_3_hex': ["11","00", to_hex(addr3)],
        'parameters': make_params(to_hex(addr3))
    }

# Generate rhythm parts 1-64 based on part 1 template offsets
rhythm_params = [  # list of definitions from existing part 1 block
    # list offset and same param definitions for part 1
]
# just skeleton demonstration
output['expansion_rhythm_parts'] = {f'expansion_rhythm_part_{i}': {'address_bytes_1_3_hex': ["11","09", to_hex(0x22+i)], 'parameters': '...same as part 1...'} for i in range(1,65)}

print(yaml.dump(output, sort_keys=False))
