import logging
import time
from mido import Message, open_output, get_output_names
from RolandSysExManager import RolandSysExManager

# Configuration
INI_FILE = "Roland_JV1080.ini"

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    try:
        roland_sysex = RolandSysExManager(INI_FILE)
        midi_port = roland_sysex.select_midi_port()
        if not midi_port:
            return

        interactive_menu(roland_sysex, midi_port)

    except Exception as e:
        logging.error(f"Error in main: {e}")

def set_patch(msb, lsb, program, midi_port, roland_sysex):
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
    except Exception as e:
        logging.error(f"Error setting patch: {e}")

def interactive_menu(roland_sysex, midi_port):
    while True:
        print("\nInteractive Menu:")
        print("1: Select Patch")
        print("2: Set ADSR (Not Implemented)")
        print("3: Exit")
        choice = input("Enter choice: ").strip()

        try:
            if choice == "1":
                msb = int(input("Enter MSB (0-127): ").strip())
                lsb = int(input("Enter LSB (0-127): ").strip())
                program = int(input("Enter Program Number (0-127): ").strip())
                set_patch(msb, lsb, program, midi_port, roland_sysex)
            elif choice == "2":
                print("ADSR setting is not implemented in this script.")
            elif choice == "3":
                logging.info("Exiting...")
                break
            else:
                logging.warning("Invalid choice. Please try again.")
        except ValueError as e:
            logging.error(f"Invalid input: {e}")

if __name__ == "__main__":
    main()