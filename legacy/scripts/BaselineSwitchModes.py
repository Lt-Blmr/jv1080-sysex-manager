import time
import os
import logging
import signal
import sys
from mido import Message, open_output, get_output_names
from typing import List

# MIDI Configuration
SYSEX_HEADER = [0x41, 0x10, 0x6A, 0x12]  # Roland SysEx header
DELAY_BETWEEN_MESSAGES = 0.04  # 40ms delay

logging.basicConfig(level=logging.ERROR)

# Helper function to calculate Roland checksum
def calculate_checksum(data: List[int]) -> int:
    checksum = (0x80 - (sum(data) % 0x80)) % 0x80
    return checksum if checksum != 0 else 0x80

DEBUG_MODE = True

# Function to select MIDI port
def select_midi_port() -> str:
    available_ports = get_output_names()
    if not available_ports:
        print("No MIDI output ports available.")
        sys.exit(1)
    
    print("Available MIDI Ports:")
    for i, port in enumerate(available_ports):
        print(f"{i + 1}: {port}")
    
    while True:
        try:
            choice = int(input("Select a MIDI port by number: ")) - 1
            if 0 <= choice < len(available_ports):
                return available_ports[choice]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# Function to send SysEx message to Roland JV-1080
def send_sysex_to_roland_1080(address: List[int], data: List[int], midi_port: str) -> None:
    """
    Send a SysEx message to a Roland JV-1080 with the correct checksum.
    :param address: Address block for the SysEx message.
    :param data: Data bytes for the SysEx message.
    :param midi_port: The MIDI port to send the message to.
    """
    # Construct the SysEx message
    message = SYSEX_HEADER + address + data
    
    # Calculate the checksum
    checksum = calculate_checksum(address + data)
    message.append(checksum)
    message.append(0xF7)  # End of SysEx message

    if DEBUG_MODE:
        print(f"Debug: SysEx message to send: {message}")
        return

    try:
        with open_output(midi_port) as port:
            port.send(Message('sysex', data=message))
            print(f"Sent SysEx: {message}")
            time.sleep(DELAY_BETWEEN_MESSAGES)  # Add delay between messages
    except Exception as e:
        logging.error(f"Error sending SysEx: {e}")

# Default Address
DEFAULT_ADDRESS = [0x00, 0x00, 0x00, 0x00]

# Send Performance Mode SysEx
def switch_to_performance_mode(midi_port: str):
    send_sysex_to_roland_1080(DEFAULT_ADDRESS, [0x01], midi_port)

# Send Patch Mode SysEx
def switch_to_patch_mode(midi_port: str):
    send_sysex_to_roland_1080(DEFAULT_ADDRESS, [0x00], midi_port)

# Signal handler for graceful exit
def signal_handler(sig, frame):
    print("\nExiting gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Main Function for Testing
if __name__ == "__main__":
    midi_port = select_midi_port()
    print(f"Using MIDI Port: {midi_port}")
    print("Switching to Performance Mode...")
    switch_to_performance_mode(midi_port)
    time.sleep(1)  # Wait before switching back
    print("Switching to Patch Mode...")
    switch_to_patch_mode(midi_port)