#!/usr/bin/env python3
"""
Preset Management Example
Shows how to create, save, and load presets.
"""

from preset_builder import PresetBuilder

def create_sample_preset():
    """Create a sample preset."""
    builder = PresetBuilder()
    
    # Create new preset
    preset = builder.create_new_preset(
        name="Ambient Pad",
        preset_type="performance",
        description="Lush ambient pad with reverb and chorus"
    )
    
    # Set performance name
    builder.set_performance_name("AMBIENT")
    
    # Configure EFX (Reverb)
    builder.set_efx_parameters(
        efx_type=5,  # Reverb
        params=[80, 120, 64, 100, 50, 0, 0, 0, 0, 0, 0, 0]
    )
    
    # Add some additional parameters
    builder.add_parameter('temp_performance_common', 'EFX:Output level', 110)
    builder.add_parameter('temp_performance_common', 'EFX:Chorus send level', 40)
    builder.add_parameter('temp_performance_common', 'EFX:Reverb send level', 100)
    
    return preset

def main():
    builder = PresetBuilder()
    
    # Create sample preset
    print("Creating sample preset...")
    preset = create_sample_preset()
    
    # Save to JSON
    print("Saving preset...")
    builder.save_preset(preset, "ambient_pad.json")
    
    # Export to Python
    print("Exporting to Python...")
    builder.export_preset_to_python(preset, "ambient_pad_preset.py")
    
    # Load and apply
    print("Loading preset...")
    loaded_preset = builder.load_preset("ambient_pad.json")
    
    if loaded_preset:
        port = builder.manager.select_midi_port()
        if port:
            print("Applying preset to JV-1080...")
            success, total = builder.apply_preset_to_jv1080(loaded_preset, port)
            print(f"Applied {success}/{total} parameters successfully!")
    
    print("Preset example completed!")

if __name__ == "__main__":
    main()
