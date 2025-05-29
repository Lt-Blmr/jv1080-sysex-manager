#!/usr/bin/env python3
"""
Modern JV-1080 Basic Usage Example
Demonstrates the new YAML-based architecture with comprehensive error handling.
"""

import logging
from pathlib import Path
from jv1080_manager import JV1080Manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Demonstrate basic JV-1080 operations with modern Python practices."""
    try:
        # Initialize JV-1080 manager with YAML configuration
        jv = JV1080Manager()
        logger.info("JV-1080 Manager initialized successfully")
        
        # List available MIDI ports
        available_ports = jv.get_available_ports()
        logger.info(f"Available MIDI ports: {available_ports}")
        
        if not available_ports:
            logger.error("No MIDI ports available")
            return
        
        # For this example, we'll use the first available port
        # In a real application, you might want to use jv.select_midi_port() for interactive selection
        port = available_ports[0]
        logger.info(f"Using MIDI port: {port}")
        
        # Switch to Performance mode
        logger.info("Switching to Performance mode...")
        if jv.switch_mode("performance", port):
            logger.info("Successfully switched to Performance mode")
        else:
            logger.error("Failed to switch to Performance mode")
            return
        
        # Set performance name using modern string handling
        logger.info("Setting performance name...")
        performance_name = "MOD DEMO"
        if jv.set_performance_name(performance_name, port):
            logger.info(f"Performance name set to: {performance_name}")
        else:
            logger.warning("Failed to set performance name")
        
        # Configure EFX with parameter validation
        logger.info("Configuring EFX parameters...")
        efx_configs = [
            ('EFX:Type', 5, 'Setting EFX to Reverb'),
            ('EFX:Parameter 1', 64, 'Setting reverb room size'),
            ('EFX:Parameter 2', 100, 'Setting reverb level'),
            ('EFX:Parameter 3', 80, 'Setting reverb feedback')
        ]
        
        for param_name, value, description in efx_configs:
            logger.info(description)
            try:
                if jv.send_parameter('temp_performance_common', param_name, value, port):
                    logger.info(f"✓ {param_name} = {value}")
                else:
                    logger.warning(f"✗ Failed to set {param_name}")
            except ValueError as e:
                logger.error(f"Parameter validation error for {param_name}: {e}")
        
        # Demonstrate parameter listing
        logger.info("Available parameters in temp_performance_common:")
        params = jv.list_parameters('temp_performance_common')
        for i, param in enumerate(params[:5]):  # Show first 5 parameters
            logger.info(f"  {i+1}. {param}")
        logger.info(f"  ... and {len(params)-5} more parameters")
        
        logger.info("Modern basic example completed successfully! 🎹")
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
