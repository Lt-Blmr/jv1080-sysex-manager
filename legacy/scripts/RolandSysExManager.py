import configparser
import logging
import time
from typing import List, Union
from mido import Message, open_output, get_output_names

class RolandSysExManager:
    def __init__(self, ini_path="Roland JV1080.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(ini_path)
        self.device_id = self.config.get("Global", "DeviceID", fallback="10")
        self.sysex_header = [int(x, 16) for x in self.config.get("Global", "SysExHeader", fallback="41 10 6A 12").split()]
        self.sysex_footer = [int(x, 16) for x in self.config.get("Global", "SysExFooter", fallback="F7").split()]
        self.delay = float(self.config.get("Global", "Delay", fallback="0.04"))
        logging.basicConfig(level=logging.INFO)

    def _parse_address(self, address_str: str) -> List[int]:
        return [int(x, 16) for x in address_str.strip().split()]

    def _get_format(self, section: str) -> List[int]:
        fmt = self.config.get(section, "MessageFormat", fallback="")
        return [int(x, 16) for x in fmt.strip().split()]

    def _calculate_checksum(self, data: List[int]) -> int:
        return (0x80 - (sum(data) % 0x80)) % 0x80

    def _nybblize(self, value: int) -> List[int]:
        msb = (value >> 7) & 0x7F
        lsb = value & 0x7F
        return [msb, lsb]

    def build_sysex_message(self, section: str, parameter: str, value: Union[int, List[int]]) -> List[int]:
        address_str = self.config.get(section, f"{parameter} Address")
        address = self._parse_address(address_str)

        data_bytes = int(self.config.get(section, f"{parameter} DataBytes", fallback="1"))
        nybblize = int(self.config.get(section, f"{parameter} DataNybblize", fallback="0"))

        if isinstance(value, int):
            data = self._nybblize(value) if nybblize and data_bytes == 2 else [value]
        else:
            data = value  # pre-formatted list if passed directly

        checksum = self._calculate_checksum(address + data)
        return [0xF0] + self.sysex_header + address + data + [checksum] + self.sysex_footer

    def select_midi_port(self) -> str:
        ports = get_output_names()
        if not ports:
            raise RuntimeError("No MIDI output ports found.")
        print("Available MIDI Ports:")
        for i, port in enumerate(ports):
            print(f"{i+1}: {port}")
        choice = int(input("Select a MIDI port: ")) - 1
        return ports[choice]

    def send_sysex(self, section: str, parameter: str, value: Union[int, List[int]], midi_port: str):
        message = self.build_sysex_message(section, parameter, value)
        try:
            with open_output(midi_port) as port:
                port.send(Message('sysex', data=message[1:-1]))  # strip 0xF0 and 0xF7 for mido
                print(f"Sent: {message}")
                time.sleep(self.delay)
        except Exception as e:
            logging.error(f"Error sending SysEx: {e}")