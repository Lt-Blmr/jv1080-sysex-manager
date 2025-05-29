#!/usr/bin/env python3
"""
System Integration Example
Demonstrates how all components work together in a real-world scenario.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any

from jv1080_manager import JV1080Manager
from sysex_parser import SysExParser
from preset_builder import PresetBuilder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JV1080Session:
    """Integrated session manager for JV-1080 operations."""
    
    def __init__(self):
        self.manager = JV1080Manager()
        self.parser = SysExParser()
        self.builder = PresetBuilder()
        self.current_port = None
        
    def initialize_session(self) -> bool:
        """Initialize a session with the JV-1080."""
        logger.info("Initializing JV-1080 session...")
        
        # Get available ports
        ports = self.manager.get_available_ports()
        if not ports:
            logger.error("No MIDI ports available")
            return False
        
        # Use first available port (in real app, user would select)
        self.current_port = ports[0]
        logger.info(f"Using MIDI port: {self.current_port}")
        
        # Test connection
        if self.manager.switch_mode("performance", self.current_port):
            logger.info("✓ Connection established")
            return True
        else:
            logger.error("✗ Failed to establish connection")
            return False
    
    def create_layered_performance(self) -> bool:
        """Create a complex layered performance."""
        logger.info("Creating layered performance...")
        
        if not self.current_port:
            logger.error("No active session")
            return False
        
        # Create new preset
        preset = self.builder.create_new_preset("LAYER DEMO", "performance")
        if not preset:
            return False
        
        # Set performance name
        self.builder.set_performance_name("LAYER DEMO")
        
        # Configure multiple parts for layering
        layer_configs = [
            {
                "part": 1,
                "patch": "A001",  # Piano patch
                "volume": 100,
                "pan": 64,  # Center
                "note_range": (21, 108)  # Full range
            },
            {
                "part": 2, 
                "patch": "A017",  # String patch
                "volume": 80,
                "pan": 44,  # Left
                "note_range": (36, 96)  # Mid range
            },
            {
                "part": 3,
                "patch": "A033",  # Pad patch
                "volume": 60,
                "pan": 84,  # Right  
                "note_range": (48, 84)  # Upper mid range
            }
        ]
        
        # Apply configurations
        for config in layer_configs:
            logger.info(f"Configuring Part {config['part']}...")
            # In a real implementation, you'd set part-specific parameters here
            # This is simplified for the example
        
        # Set global EFX
        self.builder.add_parameter("temp_performance_common", "EFX:Type", 5)  # Reverb
        self.builder.add_parameter("temp_performance_common", "EFX:Parameter 1", 80)
        self.builder.add_parameter("temp_performance_common", "EFX:Parameter 2", 90)
        
        # Apply to hardware
        success = self.builder.apply_preset_to_jv1080(preset, self.current_port)
        if success:
            logger.info("✓ Layered performance created and applied")
            
            # Save for later use
            preset_file = Path("presets") / "layered_demo.json"
            preset_file.parent.mkdir(exist_ok=True)
            self.builder.save_preset(preset, str(preset_file))
            logger.info(f"✓ Preset saved to {preset_file}")
        
        return success
    
    def backup_current_settings(self) -> bool:
        """Create a backup of current JV-1080 settings."""
        logger.info("Creating backup of current settings...")
        
        if not self.current_port:
            logger.error("No active session")
            return False
        
        # In a real implementation, you would:
        # 1. Request current parameters via SysEx
        # 2. Parse the responses
        # 3. Save to backup file
        
        # For this example, we'll create a simulated backup
        backup_data = {
            "timestamp": time.strftime("%Y%m%d_%H%M%S"),
            "mode": "performance",
            "current_performance": "USER_BACKUP",
            "parameters": {
                "temp_performance_common": {
                    "EFX:Type": 0,  # Off
                    "EFX:Parameter 1": 64,
                    "EFX:Parameter 2": 64,
                }
            }
        }
        
        backup_dir = Path("presets") / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"backup_{backup_data['timestamp']}.json"
        
        try:
            import json
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"✓ Backup saved to {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")
            return False
    
    def batch_preset_processing(self) -> bool:
        """Process multiple presets in batch."""
        logger.info("Starting batch preset processing...")
        
        sysex_dir = Path("sysex_files")
        if not sysex_dir.exists():
            logger.warning("No sysex_files directory found")
            return False
        
        syx_files = list(sysex_dir.glob("*.syx"))
        if not syx_files:
            logger.warning("No .syx files found")
            return False
        
        processed_dir = Path("presets") / "batch_processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        
        for syx_file in syx_files[:5]:  # Process first 5 files
            logger.info(f"Processing: {syx_file.name}")
            
            try:
                # Parse SysEx file
                parameters = self.parser.parse_sysex_file(str(syx_file))
                
                # Create preset from parameters
                preset_name = syx_file.stem.upper()
                preset = self.parser.create_preset_from_parameters(parameters, preset_name)
                
                if preset:
                    # Save as JSON
                    json_file = processed_dir / f"{syx_file.stem}.json"
                    self.builder.save_preset(preset, str(json_file))
                    
                    # Export as Python config
                    py_file = processed_dir / f"{syx_file.stem}_config.py"
                    self.parser.export_preset_to_python(preset, str(py_file))
                    
                    logger.info(f"  ✓ Processed and exported")
                    success_count += 1
                else:
                    logger.warning(f"  ✗ Failed to create preset")
                    
            except Exception as e:
                logger.error(f"  ✗ Error processing {syx_file.name}: {e}")
        
        logger.info(f"Batch processing complete: {success_count} files processed successfully")
        return success_count > 0

def main():
    """Run the complete system integration demonstration."""
    logger.info("🎹 JV-1080 System Integration Demo")
    logger.info("=" * 50)
    
    session = JV1080Session()
    
    try:
        # Initialize session
        if not session.initialize_session():
            logger.error("Failed to initialize session")
            return
        
        print()  # Add spacing
        
        # Create backup
        session.backup_current_settings()
        
        print()  # Add spacing
        
        # Create complex performance
        session.create_layered_performance()
        
        print()  # Add spacing
        
        # Batch process existing files
        session.batch_preset_processing()
        
        logger.info("=" * 50)
        logger.info("🎉 System integration demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    main()
