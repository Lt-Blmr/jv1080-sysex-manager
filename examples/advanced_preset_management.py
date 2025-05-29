#!/usr/bin/env python3
"""
Advanced Preset Management Example
Demonstrates parsing SysEx files, building presets, and exporting configurations.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any

from jv1080_manager import JV1080Manager
from sysex_parser import SysExParser
from preset_builder import PresetBuilder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demonstrate_sysex_parsing():
    """Demonstrate parsing existing SysEx files."""
    logger.info("=== SysEx File Parsing Demo ===")
    
    parser = SysExParser()
    sysex_dir = Path("sysex_files")
    
    if not sysex_dir.exists():
        logger.warning(f"SysEx directory {sysex_dir} not found, skipping parsing demo")
        return
    
    # Find .syx files
    syx_files = list(sysex_dir.glob("*.syx"))
    if not syx_files:
        logger.warning("No .syx files found in sysex_files directory")
        return
    
    for syx_file in syx_files[:3]:  # Process first 3 files
        logger.info(f"Parsing: {syx_file.name}")
        try:
            parameters = parser.parse_sysex_file(str(syx_file))
            logger.info(f"  Found {len(parameters)} parameters")
            
            # Show first few parameters
            for i, (param_name, value) in enumerate(list(parameters.items())[:3]):
                logger.info(f"    {param_name}: {value}")
            
        except Exception as e:
            logger.error(f"  Error parsing {syx_file.name}: {e}")

def demonstrate_preset_building():
    """Demonstrate building custom presets."""
    logger.info("=== Preset Building Demo ===")
    
    builder = PresetBuilder()
    
    # Create a new performance preset
    logger.info("Creating new performance preset...")
    preset = builder.create_new_preset("DEMO LEAD", "performance")
    
    if not preset:
        logger.error("Failed to create preset")
        return
    
    # Set performance name
    logger.info("Setting performance name...")
    success = builder.set_performance_name("LEAD SYNTH")
    if success:
        logger.info("✓ Performance name set")
    
    # Add EFX parameters
    logger.info("Configuring EFX...")
    builder.add_parameter("temp_performance_common", "EFX:Type", 5)  # Reverb
    builder.add_parameter("temp_performance_common", "EFX:Parameter 1", 70)
    builder.add_parameter("temp_performance_common", "EFX:Parameter 2", 85)
    
    logger.info(f"Preset now has {len(preset.parameters)} parameters")
    
    # Save preset to file
    preset_file = Path("presets") / "demo_lead.json"
    preset_file.parent.mkdir(exist_ok=True)
    
    try:
        builder.save_preset(preset, str(preset_file))
        logger.info(f"✓ Preset saved to {preset_file}")
    except Exception as e:
        logger.error(f"Failed to save preset: {e}")
    
    return preset

def demonstrate_preset_application(preset):
    """Demonstrate applying a preset to the JV-1080."""
    logger.info("=== Preset Application Demo ===")
    
    if not preset:
        logger.warning("No preset to apply")
        return
    
    builder = PresetBuilder()
    
    # Get available ports
    available_ports = builder.manager.get_available_ports()
    if not available_ports:
        logger.warning("No MIDI ports available for preset application")
        return
    
    port = available_ports[0]
    logger.info(f"Applying preset to MIDI port: {port}")
    
    try:
        success = builder.apply_preset_to_jv1080(preset, port)
        if success:
            logger.info("✓ Preset applied successfully")
        else:
            logger.warning("Preset application had some issues")
    except Exception as e:
        logger.error(f"Error applying preset: {e}")

def demonstrate_configuration_export():
    """Demonstrate exporting preset as Python configuration."""
    logger.info("=== Configuration Export Demo ===")
    
    builder = PresetBuilder()
    
    # Create a sample configuration
    config = {
        "preset_name": "EXPORTED_DEMO",
        "type": "performance",
        "parameters": {
            "temp_performance_common": {
                "EFX:Type": 5,
                "EFX:Parameter 1": 64,
                "EFX:Parameter 2": 100,
                "Performance name 1": ord('D'),
                "Performance name 2": ord('E'),
                "Performance name 3": ord('M'),
                "Performance name 4": ord('O'),
            }
        },
        "metadata": {
            "created_by": "JV-1080 Modern Manager",
            "description": "Demo preset for testing export functionality"
        }
    }
    
    # Export to Python file
    export_dir = Path("presets") / "exported"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    export_file = export_dir / "demo_config.py"
    
    try:
        with open(export_file, 'w') as f:
            f.write('#!/usr/bin/env python3\n')
            f.write('"""\nExported JV-1080 Preset Configuration\n"""\n\n')
            f.write(f'PRESET_CONFIG = {json.dumps(config, indent=4)}\n')
        
        logger.info(f"✓ Configuration exported to {export_file}")
    except Exception as e:
        logger.error(f"Failed to export configuration: {e}")

def main():
    """Run the complete preset management demonstration."""
    logger.info("🎹 JV-1080 Advanced Preset Management Demo")
    logger.info("=" * 50)
    
    try:
        # Parse existing SysEx files
        demonstrate_sysex_parsing()
        
        print()  # Add spacing
        
        # Build custom presets
        preset = demonstrate_preset_building()
        
        print()  # Add spacing
        
        # Apply preset to hardware
        demonstrate_preset_application(preset)
        
        print()  # Add spacing
        
        # Export configurations
        demonstrate_configuration_export()
        
        logger.info("=" * 50)
        logger.info("🎉 Advanced demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    main()
