import time
import logging
from mido import Message, open_output, get_output_names
from RolandSysExManager import RolandSysExManager

# Configuration
INI_FILE = "config/Global.ini"  # Path to INI file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        roland_sysex = RolandSysExManager(INI_FILE)  # Create the manager
        midi_port = roland_sysex.select_midi_port()
        if not midi_port:
            return  # Exit if no port selected

        interactive_menu(roland_sysex, midi_port)
    except Exception as e:
        logging.error(f"Error in main: {e}")

# Functions to switch modes
def switch_mode(roland_sysex, mode, midi_port):
    """
    Sends SysEx message to switch the JV-1080 to the specified mode.
    :param midi_port: Selected MIDI port.
    :param mode: 0 for Patch, 1 for Performance
    """
    try:
        if mode not in [0, 1]:
            raise ValueError("Invalid mode. Use 0 for Patch or 1 for Performance.")

        section = "System Common"  # Adjust if needed
        parameter = "EFXSwitch"    # Adjust if needed
        value = mode
        roland_sysex.send_sysex(section, parameter, value, midi_port)
        logging.info(f"Switched to mode: {'Performance' if mode == 1 else 'Patch'}")
    except Exception as e:
        logging.error(f"Error switching mode: {e}")

# Interactive Menu
def interactive_menu(roland_sysex, midi_port):
    """Interactive menu for mode switching."""
    while True:
        print("\nSelect a mode to switch:")
        print("1: Performance Mode")
        print("2: Patch Mode")
        print("3: Exit")

        choice = input("Enter your choice: ").strip()

        try:
            choice = int(choice)
            if choice == 1:
                print("Switching to Performance Mode...")
                switch_mode(roland_sysex, 1, midi_port)

            elif choice == 2:
                print("Switching to Patch Mode...")
                switch_mode(roland_sysex, 0, midi_port)

            elif choice == 3:
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

        except ValueError:
            print("Invalid input. Please enter 1, 2, or 3.")

# Run the interactive menu
if __name__ == "__main__":
    main()