import os
import time
import logging
from mido import Message, open_output, get_output_names
import configparser
from RolandSysExManager import RolandSysExManager

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Path to the INI file
INI_FILE = "config/Global.ini"

def main():
    try:
        roland_sysex = RolandSysExManager(INI_FILE)
        midi_port = roland_sysex.select_midi_port()
        if not midi_port:
            return

        interactive_menu(roland_sysex, midi_port)

    except FileNotFoundError as e:
        print(f"Error: Configuration file not found: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# Functions for Monosynth Parameters
def set_waveform(roland_sysex, tone_number, waveform_id, midi_port):
    """Set the waveform for a given tone in the Temp Patch Mode."""
    try:
        section = "Temp Patch Tone1"  # Adjust if needed
        parameter = "Wave number"    # Adjust if needed
        roland_sysex.send_sysex(section, parameter, waveform_id, midi_port)
    except Exception as e:
        logging.error(f"Error in set_waveform: {e}")

def set_adsr(roland_sysex, tone_number, param_type, value, midi_port):
    """Set ADSR envelope parameters for a tone."""
    try:
        param_map = {'A': 'AttackTime', 'D': 'DecayTime', 'S': 'SustainLevel', 'R': 'ReleaseTime'}
        if param_type not in param_map:
            raise ValueError("Invalid ADSR parameter type. Use A, D, S, or R.")

        section = "Temp Patch Tone1"  # Adjust if needed
        parameter = param_map[param_type]
        roland_sysex.send_sysex(section, parameter, value, midi_port)
    except Exception as e:
        logging.error(f"Error in set_adsr: {e}")

def switch_mode(roland_sysex, mode, midi_port):
    """Switch the JV-1080 between modes."""
    try:
        section = "System Common"  # Adjust if needed
        parameter = "EFXSwitch"    # Adjust if needed
        roland_sysex.send_sysex(section, parameter, mode, midi_port)
    except Exception as e:
        logging.error(f"Error switching mode: {e}")

# Interactive Menu
def interactive_menu(roland_sysex, midi_port):
    while True:
        print("\nSelect a parameter to test:")
        print("1: Set Waveform")
        print("2: Set ADSR")
        print("3: Switch Mode")
        print("4: Exit")

        choice = input("Enter your choice: ").strip()

        try:
            if choice == "1":
                tone = int(input("Enter Tone Number (1-4): ").strip())
                waveform = int(input("Enter Waveform ID (0-127): ").strip())
                set_waveform(roland_sysex, tone, waveform, midi_port)

            elif choice == "2":
                tone = int(input("Enter Tone Number (1-4): ").strip())
                param = input("Enter ADSR Parameter (A, D, S, R): ").strip().upper()
                value = int(input("Enter Value (0-127): ").strip())
                set_adsr(roland_sysex, tone, param, value, midi_port)

            elif choice == "3":
                print("Modes:")
                print("0: PATCH Mode")
                print("1: PERFORM Mode")
                print("2: GM1 Mode")
                print("3: GM2 Mode")
                print("4: GS Mode")
                mode = int(input("Enter mode (0-4): ").strip())
                switch_mode(roland_sysex, mode, midi_port)

            elif choice == "4":
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            print("Returning to main menu...")

if __name__ == "__main__":
    main()