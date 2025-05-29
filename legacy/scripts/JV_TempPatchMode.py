import time
import logging
from mido import Message, get_output_names, open_output
from RolandSysExManager import RolandSysExManager  # Import the class

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

def set_adsr(roland_sysex, tone_number, param_type, value, midi_port):
    """Set ADSR envelope parameters for a tone."""
    param_map = {'A': 'AttackTime', 'D': 'DecayTime', 'S': 'SustainLevel', 'R': 'ReleaseTime'}
    if param_type not in param_map:
        raise ValueError("Invalid ADSR parameter type. Use A, D, S, or R.")

    try:
        section = "Temp Patch Tone1"  # Or appropriate section
        parameter = param_map[param_type]
        roland_sysex.send_sysex(section, parameter, value, midi_port)
    except Exception as e:
        logging.error(f"Error setting ADSR: {e}")

def set_filter(roland_sysex, tone_number, param_type, value, midi_port):
    """Set filter parameters (cutoff/resonance) for a tone."""
    param_map = {'cutoff': 'CutoffFrequency', 'resonance': 'Resonance'}
    if param_type not in param_map:
        raise ValueError("Invalid filter parameter type. Use 'cutoff' or 'resonance'.")

    try:
        section = "Temp Patch Tone1"
        parameter = param_map[param_type]
        roland_sysex.send_sysex(section, parameter, value, midi_port)
    except Exception as e:
        logging.error(f"Error setting filter: {e}")

def set_glide(roland_sysex, tone_number, glide_time, midi_port):
    """Set glide (portamento) time for a tone."""
    try:
        section = "Temp Patch Tone1"
        parameter = "PortamentoTime"
        roland_sysex.send_sysex(section, parameter, glide_time, midi_port)
    except Exception as e:
        logging.error(f"Error setting glide time: {e}")

def set_volume(roland_sysex, tone_number, volume, midi_port):
    """Set the volume for a given tone."""
    try:
        section = "Temp Patch Tone1"
        parameter = "AmplitudeLevel"
        roland_sysex.send_sysex(section, parameter, volume, midi_port)
    except Exception as e:
        logging.error(f"Error setting volume: {e}")

def set_pan(roland_sysex, tone_number, pan_position, midi_port):
    """Set the pan position for a given tone."""
    try:
        section = "Temp Patch Tone1"
        parameter = "Pan"
        roland_sysex.send_sysex(section, parameter, pan_position, midi_port)
    except Exception as e:
        logging.error(f"Error setting pan: {e}")

def set_lfo(roland_sysex, param_type, value, midi_port):
    """Set LFO parameters for modulation."""
    param_map = {'rate': 'LFO 1 rate', 'delay': 'LFO 1 delay time'}
    if param_type not in param_map:
        raise ValueError("Invalid LFO parameter type. Use 'rate' or 'delay'.")

    try:
        section = "Temp Patch Tone1"
        parameter = param_map[param_type]
        roland_sysex.send_sysex(section, parameter, value, midi_port)
    except Exception as e:
        logging.error(f"Error setting LFO: {e}")

def send_patch_select(roland_sysex, msb, lsb, program, midi_port):
    """Send Bank Select and Program Change to select a patch."""
    try:
        # Assuming these are sent as CC messages, not SysEx
        with open_output(midi_port) as port:
            port.send(Message('control_change', control=0, value=msb))  # MSB
            time.sleep(roland_sysex.delay)
            port.send(Message('control_change', control=32, value=lsb))  # LSB
            time.sleep(roland_sysex.delay)
            port.send(Message('program_change', program=program))  # Program Change
            time.sleep(roland_sysex.delay)
        logging.info(f"Patch select message sent: MSB={msb}, LSB={lsb}, Program={program}")
    except Exception as e:
        logging.error(f"Error sending patch select message: {e}")

def interactive_menu(roland_sysex, midi_port):
    """Interactive menu for testing Temp Patch Mode parameters."""
    patch_selected = False  # Tracks if a patch has been selected

    while True:
        if not patch_selected:
            print("\nPlease select a patch first:")
            print("1: Select Patch")
            print("2: Exit")
        else:
            print("\nSelect a parameter to test:")
            print("1: Set Filter (Cutoff/Resonance)")
            print("2: Set ADSR Envelope")
            print("3: Set Glide Time")
            print("4: Set Volume")
            print("5: Set Pan")
            print("6: Set LFO (Rate/Delay)")
            print("7: Exit")

        try:
            choice = int(input("Enter your choice: "))
            if choice == 1 and not patch_selected:
                msb = int(input("Enter Bank Select MSB: ").strip())
                lsb = int(input("Enter Bank Select LSB: ").strip())
                program = int(input("Enter Program Change (0-127): ").strip())
                send_patch_select(roland_sysex, msb, lsb, program, midi_port)
                patch_selected = True
            elif choice == 1 and patch_selected:
                print("Patch already selected. Restart the program to change.")
            elif choice == 2 and patch_selected:
                tone = int(input("Enter Tone Number (1-4): ").strip())
                param = input("Enter Filter Parameter (cutoff/resonance): ").strip().lower()
                value = int(input("Enter Value (0-127): ").strip())
                set_filter(roland_sysex, tone, param, value, midi_port)
            elif choice == 3 and patch_selected:
                tone = int(input("Enter Tone Number (1-4): ").strip())
                param = input("Enter ADSR Parameter (A, D, S, R): ").strip().upper()
                value = int(input("Enter Value (0-127): ").strip())
                set_adsr(roland_sysex, tone, param, value, midi_port)
            elif choice == 4 and patch_selected:
                tone = int(input("Enter Tone Number (1-4): ").strip())
                glide_time = int(input("Enter Glide Time (0-127): ").strip())
                set_glide(roland_sysex, tone, glide_time, midi_port)
            elif choice == 5 and patch_selected:
                tone = int(input("Enter Tone Number (1-4): ").strip())
                volume = int(input("Enter Volume Level (0-127): ").strip())
                set_volume(roland_sysex, tone, volume, midi_port)
            elif choice == 6 and patch_selected:
                tone = int(input("Enter Tone Number (1-4): ").strip())
                pan_position = int(input("Enter Pan Position (0-127): ").strip())
                set_pan(roland_sysex, tone, pan_position, midi_port)
            elif choice == 7 and patch_selected:
                param = input("Enter LFO Parameter (rate/delay): ").strip().lower()
                if param not in ['rate', 'delay']:
                    raise ValueError("LFO parameter must be 'rate' or 'delay'.")
                value = int(input("Enter Value (0-127): ").strip())
                set_lfo(roland_sysex, param, value, midi_port)
            elif choice == 8:
                logging.info("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError as e:
            logging.error(f"Invalid input: {e}")

if __name__ == "__main__":
    main()