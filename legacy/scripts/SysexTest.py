import configparser
import mido
import time
import mido.backends.rtmidi  # Required for Windows

class RolandSysExManager:
    def __init__(self, ini_file):
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)
        self.device_id = int(self.config['Global']['DeviceID'])
        self.sysex_header = [int(byte, 16) for byte in self.config['Global']['SysExHeader'].replace("{DeviceID}", f"{self.device_id:02X}").split()]
        self.sysex_footer = [int(byte, 16) for byte in self.config['Global']['SysExFooter'].split()]
        self.delay = float(self.config['Global'].get('Delay', '0.04'))  # Add delay
        self.current_values = self.load_defaults()

    def load_defaults(self):
        defaults = {}
        for section in self.config.sections():
            for key in self.config[section]:
                if key.endswith("Default"):
                    parameter = key.replace(" Default", "")
                    value = int(self.config[section][key])
                    defaults[parameter] = value
        return defaults

    def get_cc(self, section, parameter):
        return self.config[section].get(f"{parameter} CC")

    def get_address(self, section, parameter):
        return self.config[section].get(f"{parameter} Address")

    def calculate_checksum(self, data_bytes):
        return (128 - sum(data_bytes) % 128) & 0x7F

    def build_sysex_message(self, address, value):
        try:
            address_bytes = [int(byte, 16) for byte in address.split()]
            address_nibbles = []
            for byte in address_bytes:
                address_nibbles.extend([(byte >> 4) & 0x0F, byte & 0x0F])

            checksum_data = address_nibbles + [value]
            checksum = self.calculate_checksum(checksum_data)

            return self.sysex_header + address_nibbles + [value, checksum] + self.sysex_footer
        except ValueError:
            raise ValueError(f"Invalid address or value: {address}, {value}")
        except Exception as e:
            raise RuntimeError(f"Error building SysEx message: {e}")

    def send_sysex(self, address, value, midi_port):
        try:
            sysex_message = self.build_sysex_message(address, value)
            midi_port.send(mido.Message('sysex', data=sysex_message))
            print(f"Sent SysEx: {sysex_message}")
            time.sleep(self.delay)  # Use the class's delay
        except mido.PortClosedError:
            print("Error: MIDI port is closed. Please check the connection.")