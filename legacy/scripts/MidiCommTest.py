from mido import Message, open_output, get_output_names
import logging
from RolandSysExManager import RolandSysExManager

# Configuration
INI_FILE = "config/Global.ini"

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        roland_sysex = RolandSysExManager(INI_FILE)
        midi_port = roland_sysex.select_midi_port()
        if not midi_port:
            return

        # Example: Sending a System Common Parameter
        section = "System Common"
        parameter = "EFXSwitch"
        value = 1  # Or 0, depending on what you want to send
        roland_sysex.send_sysex(section, parameter, value, midi_port)

        print("SysEx message sent.")
    except ValueError as e:
        logging.error(f"ValueError: {e}")
    except IOError as e:
        logging.error(f"IOError: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()