#!/usr/bin/env python3
"""
Basic JV-1080 Usage Example
Demonstrates fundamental operations with the JV-1080.
"""

from jv1080_manager import JV1080Manager

def main():
    # Initialize JV-1080 manager
    jv = JV1080Manager()
    
    # Select MIDI port interactively
    port = jv.select_midi_port()
    if not port:
        print("No MIDI port selected. Exiting.")
        return
    
    print(f"Using MIDI port: {port}")
    
    # Switch to Performance mode
    print("Switching to Performance mode...")
    jv.switch_mode("performance", port)
    
    # Set performance name to "BASIC EX"
    print("Setting performance name...")
    performance_name = "BASIC EX"
    for i, char in enumerate(performance_name.ljust(12)[:12]):
        param_name = f"Performance name {i+1}"
        jv.send_parameter('temp_performance_common', param_name, ord(char), port)
    
    # Set some EFX parameters
    print("Setting EFX parameters...")
    jv.send_parameter('temp_performance_common', 'EFX:Type', 5, port)  # Reverb
    jv.send_parameter('temp_performance_common', 'EFX:Parameter 1', 64, port)
    jv.send_parameter('temp_performance_common', 'EFX:Parameter 2', 100, port)
    
    print("Basic example completed successfully!")

if __name__ == "__main__":
    main()
