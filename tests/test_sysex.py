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

import pytest
import mido
from RolandSysExManager import RolandSysExManager

# Test basic import and initialization of the manager
def test_manager_initialization(tmp_path):
    # Create a dummy INI file for testing
    ini_content = """
[Global]
DeviceID = 17
SysExHeader = 41 10 6A 12
SysExFooter = F7
Delay = 0.04

[TestSection]
TestParameter Address = 00 00 00 01
TestParameter DataBytes = 1
TestParameter DataNybblize = 0
"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    ini_file_path = config_dir / "test_config.ini"
    ini_file_path.write_text(ini_content)
    
    try:
        manager = RolandSysExManager(ini_path=str(ini_file_path))
        assert manager is not None
        # Add a check to ensure the config was actually loaded
        assert manager.config.has_section("Global"), "Test INI file's [Global] section not loaded"
        assert manager.device_id == "17" 
        assert manager.sysex_header == [0x41, 0x10, 0x6A, 0x12]
        assert manager.sysex_footer == [0xF7]
        assert manager.delay == 0.04
    except Exception as e:
        pytest.fail(f"RolandSysExManager initialization or basic assertions failed: {e}")

# Test SysEx message building
def test_build_sysex_message(tmp_path):
    ini_content = """
[Global]
DeviceID = 17
SysExHeader = 41 10 6A 12
SysExFooter = F7
Delay = 0.04

[Temp Patch Tone1]
CutoffFrequency Address = 00 00 00 51
CutoffFrequency DataBytes = 1
CutoffFrequency DataNybblize = 0
"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    ini_file_path = config_dir / "test_config.ini"
    ini_file_path.write_text(ini_content)

    manager = RolandSysExManager(ini_path=str(ini_file_path))
    assert manager.config.has_section("Temp Patch Tone1"), "Test INI file's [Temp Patch Tone1] section not loaded"

    message = manager.build_sysex_message("Temp Patch Tone1", "CutoffFrequency", 127) 
    
    assert isinstance(message, list)
    # Expected structure: [0xF0] + header + address + data + [checksum] + footer
    assert message[0] == 0xF0 
    assert message[1:5] == [0x41, 0x10, 0x6A, 0x12] # manager.sysex_header
    assert message[5:9] == [0x00, 0x00, 0x00, 0x51] # Address
    assert message[9] == 0x7F # Value
    # Checksum for address=[0,0,0,81], data=[127] is 48 (0x30)
    assert message[10] == 0x30 # Checksum
    assert message[11:] == [0xF7] # manager.sysex_footer

# Test mido import and basic functionality
# This test might fail in environments without a proper MIDI setup (e.g., CI runners)
@pytest.mark.skipif(not mido.get_output_names(), reason="No MIDI output ports found, skipping port test")
def test_mido_ports():
    try:
        ports = mido.get_output_names()
        assert isinstance(ports, list) 
    except Exception as e:
        pytest.fail(f"mido.get_output_names() failed: {e}")