import time
import logging
from mido import Message, get_output_names, open_output

# Configuration
MIDI_PORT = None  # Default port will be selected dynamically
SYSEX_HEADER = [0x41, 0x10, 0x6A, 0x12]  # Roland SysEx header (excluding 0xF0)
DELAY_BETWEEN_MESSAGES = 0.10  # 100ms delay
MAX_SYSEX_LENGTH = 81  # Maximum SysEx message length for rtmidi

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_checksum(data):
    """Calculate Roland-style checksum."""
    checksum = (128 - (sum(data) % 128)) % 128
    return checksum

class RolandSysEx:
    def __init__(self, port):
        self.port = port
        self.sysex_header = [0x41, 0x10, 0x6A, 0x12]  # Roland SysEx header (excluding 0xF0)
        self.delay_between_messages = 0.10  # 100ms delay

    def calculate_checksum(self, data):
        """Calculate Roland-style checksum."""
        checksum = (128 - (sum(data) % 128)) % 128
        return checksum

    def send_sysex(self, data):
        """Send a SysEx message."""
        try:
            checksum = self.calculate_checksum(self.sysex_header + data)
            full_message = [0xF0] + self.sysex_header + data + [checksum] + [0xF7]
            logging.info(f"Sending SysEx message: {full_message}")
            self.port.send(Message('sysex', data=full_message))
            time.sleep(self.delay_between_messages)
        except Exception as e:
            logging.error(f"Error sending SysEx: {e}")

def init_midi():
    """
    Initializes the MIDI output port.
    
    Returns:
        midi_device: The initialized MIDI output port.
    """
    available_ports = get_output_names()
    if not available_ports:
        raise RuntimeError("No MIDI output ports available.")
    
    print("Available MIDI output ports:")
    for i, port in enumerate(available_ports):
        print(f"{i}: {port}")
    
    while True:
        try:
            port_index = int(input("Select MIDI output port: ").strip())
            if 0 <= port_index < len(available_ports):
                midi_device = open_output(available_ports[port_index])
                return midi_device
            else:
                logging.warning("Invalid port index. Please select a valid port.")
        except ValueError:
            logging.warning("Invalid input. Please enter a number.")
        except Exception as e:
            logging.error(f"Error opening MIDI port: {e}")
            print("Error opening MIDI port. Please try again.")

def set_adsr(roland_sysex, tone, param, value):
    """Set ADSR parameter."""
    try:
        param_map = {
            'A': (0x50, 0x51),  # Attack requires two parameters: T1 (0x50) and L1 (0x51)
            'D': (0x52, 0x53),  # Decay requires two parameters: T2 (0x52) and L2 (0x53)
            'S': (0x54,),       # Sustain
            'R': (0x55,)        # Release
        }
        if param not in param_map:
            raise ValueError("Invalid ADSR parameter type. Use A, D, S, or R.")
        
        addresses = param_map[param]
        for addr in addresses:
            address = [0x03, 0x00, 0x00, tone - 1, addr]
            data = address + [value]
            roland_sysex.send_sysex(data)
    except Exception as e:
        logging.error(f"Error setting ADSR: {e}")

def set_glide(roland_sysex, tone, glide_time):
    """Set Glide parameter."""
    try:
        logging.info(f"Setting Glide for Tone {tone} to {glide_time}")
        address = [0x03, 0x00, 0x00, tone - 1, 0x54]  # Example address for Glide
        data = address + [glide_time]
        roland_sysex.send_sysex(data)
    except Exception as e:
        logging.error(f"Error setting Glide: {e}")

def set_volume(roland_sysex, tone, volume):
    """Set Volume parameter."""
    try:
        logging.info(f"Setting Volume for Tone {tone} to {volume}")
        address = [0x03, 0x00, 0x00, tone - 1, 0x55]  # Example address for Volume
        data = address + [volume]
        roland_sysex.send_sysex(data)
    except Exception as e:
        logging.error(f"Error setting Volume: {e}")

def set_pan(roland_sysex, tone, pan_position):
    """Set Pan parameter."""
    try:
        logging.info(f"Setting Pan for Tone {tone} to {pan_position}")
        address = [0x03, 0x00, 0x00, tone - 1, 0x56]  # Example address for Pan
        data = address + [pan_position]
        roland_sysex.send_sysex(data)
    except Exception as e:
        logging.error(f"Error setting Pan: {e}")

def set_lfo(roland_sysex, param, value):
    """
    Set LFO parameter.

    Args:
        param: LFO parameter ('rate' or 'delay').
        value: Value to set (0-127).
    """
    try:
        if param not in ['rate', 'delay']:
            raise ValueError("LFO parameter must be 'rate' or 'delay'.")
        logging.info(f"Setting LFO {param} to {value}")
        address = [0x03, 0x00, 0x00, 0x00, 0x57 if param == 'rate' else 0x58]
        data = address + [value]
        roland_sysex.send_sysex(data)
    except Exception as e:
        logging.error(f"Error setting LFO: {e}")

def set_filter(roland_sysex, tone, param, value):
    """
    Set Filter parameter.

    Args:
        tone: Tone number (1-4).
        param: Filter parameter ('cutoff' or 'resonance').
        value: Value to set (0-127).
    """
    try:
        if param not in ['cutoff', 'resonance']:
            raise ValueError("Filter parameter must be 'cutoff' or 'resonance'.")
        
        logging.info(f"Setting Filter {param} for Tone {tone} to {value}")
        
        address = [0x03, 0x00, 0x00, tone - 1, 0x60 if param == 'cutoff' else 0x61]
        data = address + [value]
        roland_sysex.send_sysex(data)
    except Exception as e:
        logging.error(f"Error setting Filter: {e}")

def select_bank():
    """
    Function to select the bank.
    
    Returns:
        msb: Most Significant Byte of the bank.
        lsb: Least Significant Byte of the bank.
    """
    try:
        msb = int(input("Enter MSB (0-127): ").strip())
        lsb = int(input("Enter LSB (0-127): ").strip())
        if 0 <= msb <= 127 and 0 <= lsb <= 127:
            return msb, lsb
        else:
            raise ValueError("MSB and LSB must be between 0 and 127.")
    except ValueError as e:
        logging.error(f"Invalid input: {e}")
        return select_bank()

def send_patch_select(port, msb, lsb, program):
    """Send a patch select message."""
    try:
        message = Message('control_change', control=0, value=msb)
        port.send(message)
        message = Message('control_change', control=32, value=lsb)
        port.send(message)
        message = Message('program_change', program=program)
        port.send(message)
        logging.info(f"Patch select message sent: MSB={msb}, LSB={lsb}, Program={program}")
    except Exception as e:
        logging.error(f"Error sending patch select message: {e}")

def interactive_menu(roland_sysex):
    """Interactive menu for testing Temp Patch Mode parameters."""
    global MIDI_PORT
    patch_selected = False  # Tracks if a patch has been selected

    while True:
        if not patch_selected:
            print("\nPlease select a patch first:")
            print("1: Select Patch")
            print("2: Exit")
            choice = input("Enter your choice: ").strip()

            try:
                choice = int(choice)
                if choice == 1:
                    msb, lsb = select_bank()
                    program = int(input("Enter Program Number (0-127): ").strip())
                    if 0 <= program <= 127:
                        send_patch_select(MIDI_PORT, msb, lsb, program)
                        patch_selected = True
                    else:
                        logging.warning("Invalid Program Number. Please enter a value between 0 and 127.")
                elif choice == 2:
                    logging.info("Exiting...")
                    break
                else:
                    logging.warning("Invalid choice. Please try again.")
            except ValueError as e:
                logging.error(f"Invalid input: {e}")
        else:
            print("\nSelect a parameter to set:")
            print("1: Set ADSR")
            print("2: Set Glide")
            print("3: Set Volume")
            print("4: Set Pan")
            print("5: Set LFO")
            print("6: Set Filter")
            print("7: Exit")
            choice = input("Enter your choice: ").strip()

            try:
                choice = int(choice)
                if choice == 1:
                    tone = int(input("Enter Tone Number (1-4): ").strip())
                    if tone < 1 or tone > 4:
                        raise ValueError("Tone number must be between 1 and 4.")
                    param = input("Enter ADSR Parameter (A, D, S, R): ").strip().upper()
                    if param not in ['A', 'D', 'S', 'R']:
                        raise ValueError("ADSR parameter must be one of A, D, S, R.")
                    value = int(input("Enter Value (0-127): ").strip())
                    if value < 0 or value > 127:
                        raise ValueError("Value must be between 0 and 127.")
                    set_adsr(roland_sysex, tone, param, value)
                elif choice == 2:
                    tone = int(input("Enter Tone Number (1-4): ").strip())
                    if tone < 1 or tone > 4:
                        raise ValueError("Tone number must be between 1 and 4.")
                    glide_time = int(input("Enter Glide Time (0-127): ").strip())
                    if glide_time < 0 or glide_time > 127:
                        raise ValueError("Glide time must be between 0 and 127.")
                    set_glide(roland_sysex, tone, glide_time)
                elif choice == 3:
                    tone = int(input("Enter Tone Number (1-4): ").strip())
                    if tone < 1 or tone > 4:
                        raise ValueError("Tone number must be between 1 and 4.")
                    volume = int(input("Enter Volume Level (0-127): ").strip())
                    if volume < 0 or volume > 127:
                        raise ValueError("Volume level must be between 0 and 127.")
                    set_volume(roland_sysex, tone, volume)
                elif choice == 4:
                    tone = int(input("Enter Tone Number (1-4): ").strip())
                    if tone < 1 or tone > 4:
                        raise ValueError("Tone number must be between 1 and 4.")
                    pan_position = int(input("Enter Pan Position (0-127): ").strip())
                    if pan_position < 0 or pan_position > 127:
                        raise ValueError("Pan position must be between 0 and 127.")
                    set_pan(roland_sysex, tone, pan_position)
                elif choice == 5:
                    param = input("Enter LFO Parameter (rate/delay): ").strip().lower()
                    if param not in ['rate', 'delay']:
                        raise ValueError("LFO parameter must be 'rate' or 'delay'.")
                    value = int(input("Enter Value (0-127): ").strip())
                    if value < 0 or value > 127:
                        raise ValueError("Value must be between 0 and 127.")
                    set_lfo(roland_sysex, param, value)
                elif choice == 6:
                    tone = int(input("Enter Tone Number (1-4): ").strip())
                    param = input("Enter Filter Parameter (cutoff/resonance): ").strip().lower()
                    value = int(input("Enter Value (0-127): ").strip())
                    if value < 0 or value > 127:
                        raise ValueError("Value must be between 0 and 127.")
                    set_filter(roland_sysex, tone, param, value)
                elif choice == 7:
                    logging.info("Exiting...")
                    break
                else:
                    logging.warning("Invalid choice. Please try again.")
            except ValueError as e:
                logging.error(f"Invalid input: {e}")

def main():
    """Main function to initialize the MIDI port and test SysEx communication."""
    global MIDI_PORT

    # Step 1: Select MIDI Port
    MIDI_PORT = init_midi()
    if not MIDI_PORT:
        logging.error("No MIDI port selected. Exiting.")
        return

    # Initialize RolandSysEx
    roland_sysex = RolandSysEx(MIDI_PORT)

    # Step 2: Send a Test SysEx Message (Optional)
    try:
        # Example SysEx message (can be modified or removed for production)
        message_data = [0x00, 0x01, 0x02]
        roland_sysex.send_sysex(message_data)
        logging.info("Test SysEx message successfully sent.")
    except Exception as e:
        logging.error(f"Error during SysEx communication test: {e}")

    # Step 3: Launch Interactive Menu
    interactive_menu(roland_sysex)

if __name__ == "__main__":
    main()