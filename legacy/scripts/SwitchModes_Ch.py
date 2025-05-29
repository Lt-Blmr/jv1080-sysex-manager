import time
from mido import Message, open_output, get_output_names

# MIDI Configuration
SYSEX_HEADER = [0x41, 0x10, 0x6A, 0x12]  # Roland SysEx header
DELAY_BETWEEN_MESSAGES = 0.04  # 40ms delay

# Helper function to calculate Roland checksum
def calculate_checksum(data):
    checksum = (0x80 - (sum(data) % 0x80)) % 0x80
    return checksum if checksum != 0 else 0x80

# Helper function to send SysEx messages
def send_sysex(message_data, midi_port):
    try:
        with open_output(midi_port) as port:
            port.send(Message('sysex', data=message_data))
            print(f"Sent SysEx: {message_data}")
            time.sleep(DELAY_BETWEEN_MESSAGES)  # Add delay
    except Exception as e:
        print(f"Error sending SysEx: {e}")

# Helper function to get valid integer input
def get_valid_integer(prompt, min_value, max_value):
    while True:
        try:
            value = int(input(prompt).strip())
            if min_value <= value <= max_value:
                return value
            else:
                print(f"Please enter a value between {min_value} and {max_value}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# Helper function to select a MIDI port
def select_midi_port():
    available_ports = get_output_names()
    if not available_ports:
        raise ValueError("No MIDI ports available.")
    
    print("Available MIDI ports:")
    for i, port in enumerate(available_ports):
        print(f"{i + 1}: {port}")
    
    port_index = get_valid_integer("Select a MIDI port: ", 1, len(available_ports)) - 1
    return available_ports[port_index]

# Function to switch to Performance Mode
def switch_to_performance_mode(midi_port):
    """
    Sends SysEx message to switch the JV-1080 to Performance Mode.
    :param midi_port: Selected MIDI port.
    """
    address = [0x00, 0x00, 0x00, 0x00]  # Address for Performance Mode
    data_byte = 0x01  # Data value for Performance Mode
    message = SYSEX_HEADER + address + [data_byte]
    message.append(calculate_checksum(address + [data_byte]))
    send_sysex(message, midi_port)

# Function to switch to Patch Mode
def switch_to_patch_mode(midi_port):
    """
    Sends SysEx message to switch the JV-1080 to Patch Mode.
    :param midi_port: Selected MIDI port.
    """
    address = [0x00, 0x00, 0x00, 0x00]  # Address for Patch Mode
    data_byte = 0x00  # Data value for Patch Mode
    message = SYSEX_HEADER + address + [data_byte]
    message.append(calculate_checksum(address + [data_byte]))
    send_sysex(message, midi_port)

# Interactive Menu
def interactive_menu():
    midi_port = select_midi_port()
    print(f"Using selected MIDI Port: {midi_port}")
    
    while True:
        print("\nSelect a mode to switch:")
        print("1: Performance Mode")
        print("2: Patch Mode")
        print("3: Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            print("Switching to Performance Mode...")
            switch_to_performance_mode(midi_port)

        elif choice == "2":
            print("Switching to Patch Mode...")
            switch_to_patch_mode(midi_port)

        elif choice == "3":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

# Run the interactive menu
if __name__ == "__main__":
    interactive_menu()