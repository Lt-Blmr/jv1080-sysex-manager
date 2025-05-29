import time
import logging
from mido import Message, get_output_names, open_output
from RolandSysExManager import RolandSysExManager

# Configuration
INI_FILE = "Roland_JV1080.ini"  # Path to INI file

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        roland_sysex = RolandSysExManager(INI_FILE)  # Create the manager
        midi_port = roland_sysex.select_midi_port()
        if not midi_port:
            return  # Exit if no port selected

        interactive_menu(roland_sysex, midi_port)
    except Exception as e:
        logging.error(f"Error in main: {e}")

def send_patch_select(roland_sysex, msb, lsb, program, midi_port):
    """Set the patch by sending Bank Select (MSB, LSB) and Program Change messages."""
    try:
        with open_output(midi_port) as port:
            logging.info(f"Setting Bank Select MSB: {msb}, LSB: {lsb}")
            port.send(Message('control_change', control=0, value=msb))  # MSB
            time.sleep(roland_sysex.delay)
            port.send(Message('control_change', control=32, value=lsb))  # LSB
            time.sleep(roland_sysex.delay)

            logging.info(f"Setting Program Change: {program}")
            port.send(Message('program_change', program=program))  # Program Change
            time.sleep(roland_sysex.delay)

            logging.info(f"Patch set to Bank {msb}-{lsb}, Program {program}")
    except Exception as e:
        logging.error(f"Error in set_patch: {e}")

# Interactive Menu
def interactive_menu(roland_sysex, midi_port):
    """Interactive menu for testing MIDI implementation."""
    while True:
        print("\nSelect a parameter to test:")
        print("1: Set Patch")
        print("2: Exit")

        try:
            choice = int(input("Enter your choice: "))
            if choice == 1:
                msb = int(input("Enter Bank Select MSB: ").strip())
                lsb = int(input("Enter Bank Select LSB: ").strip())
                program = int(input("Enter Program Change (0-127): ").strip())
                send_patch_select(roland_sysex, msb, lsb, program, midi_port)
            elif choice == 2:
                logging.info("Exiting...")
                break
            else:
                logging.warning("Invalid choice. Please try again.")
        except ValueError as e:
            logging.error(f"Invalid input: {e}")

if __name__ == "__main__":
    main()