import logging
from RolandSysExManager import RolandSysExManager  # Import the class

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Main function for testing SysEx parsing."""
    print("SysEx Parser")

    # Initialize RolandSysExManager (you might need to adjust INI_FILE)
    roland_sysex = RolandSysExManager("Roland_JV1080.ini") 

    choice = input("Enter '1' to parse from file or '2' to input manually: ").strip()
    if choice == '1':
        file_path = input("Enter the path to the SysEx file: ").strip()
        # Implement file reading logic here (if needed)
        # Example:
        # try:
        #     with open(file_path, "rb") as f:
        #         sysex_message = list(f.read())
        # except FileNotFoundError:
        #     print(f"File not found: {file_path}")
        #     return
        print("File parsing not implemented.")
        return

    elif choice == '2':
        sysex_string = input("Enter the SysEx message as space-separated hex values: ").strip()
        try:
            sysex_message = [int(x, 16) for x in sysex_string.split()]
        except ValueError:
            print("Invalid hex values.")
            return
    else:
        print("Invalid choice.")
        return

    # Example usage of RolandSysExManager methods (adapt as needed)
    # In this example, we're assuming you want to parse the address from a raw SysEx message
    # and then use the checksum calculation from RolandSysExManager.
    try:
        address = sysex_message[4:8]  # Extract address (example)
        data_byte = sysex_message[8:-1]  # Exclude checksum and F7
        calculated_checksum = roland_sysex.calculate_checksum(address + data_byte)
        print(f"Calculated Checksum: {calculated_checksum}")
        # Further parsing logic based on your needs...
    except Exception as e:
        logging.error(f"Error processing SysEx: {e}")

if __name__ == "__main__":
    main()