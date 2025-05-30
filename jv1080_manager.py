"""
Modern JV-1080 SysEx Manager using YAML configuration.
This replaces the old INI-based RolandSysExManager and provides a clean, unified interface.
"""

import yaml
import logging
import time
from typing import List, Dict, Union, Optional, Any
from pathlib import Path
import mido
from mido import Message, open_output, get_output_names

class JV1080Manager:
    """
    Modern JV-1080 SysEx Manager using YAML configuration.
    Provides full control over JV-1080 parameters and presets.
    """
    
    def __init__(self, config_path: str = "roland_jv_1080_fixed.yaml"):
        """Initialize the JV-1080 Manager with YAML configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.common_info = self.config['roland_jv_1080']['sysex_common_info']
        self.parameter_groups = self.config['roland_jv_1080']['sysex_parameter_groups']
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Default delay between SysEx messages
        self.delay = 0.04
    
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _hex_to_int(self, hex_str: str) -> int:
        """Convert hex string to integer."""
        return int(hex_str, 16)
    
    def _calculate_checksum(self, data: List[int]) -> int:
        """Calculate Roland-style checksum."""
        return (0x80 - (sum(data) % 0x80)) % 0x80
    
    def build_sysex_message(self, group_name: str, parameter_name: str, value: Union[int, List[int]], device_id: str = "10") -> List[int]:
        """
        Build a complete SysEx message for a parameter.
        
        Args:
            group_name: Parameter group name (e.g., 'temp_performance_common')
            parameter_name: Parameter name (e.g., 'Performance name 1')
            value: Parameter value (int or list of ints)
            device_id: Device ID in hex format (default "10")
        
        Returns:
            Complete SysEx message as list of integers
        """
        if group_name not in self.parameter_groups:
            raise ValueError(f"Unknown parameter group: {group_name}")
        
        group = self.parameter_groups[group_name]
        
        # Find the parameter
        parameter = None
        for param in group['parameters']:
            if param['name'] == parameter_name:
                parameter = param
                break
        
        if parameter is None:
            raise ValueError(f"Unknown parameter: {parameter_name} in group {group_name}")
        
        # Build message components
        manufacturer_id = self._hex_to_int(self.common_info['manufacturer_id_hex'])
        device_id_int = self._hex_to_int(device_id)
        model_id = self._hex_to_int(self.common_info['model_id_hex'])
        command_id = self._hex_to_int(self.common_info['command_id_dt1_hex'])
        
        # Build address (Addr1, Addr2, Addr3, Addr4)
        addr_1_3 = [self._hex_to_int(addr) for addr in group['address_bytes_1_3_hex']]
        addr_4 = self._hex_to_int(parameter['offset_hex'])
        address = addr_1_3 + [addr_4]
        
        # Prepare data
        if isinstance(value, int):
            # Validate range
            if 'min' in parameter and 'max' in parameter:
                if not (parameter['min'] <= value <= parameter['max']):
                    raise ValueError(f"Value {value} out of range [{parameter['min']}-{parameter['max']}] for {parameter_name}")
            data = [value]
        else:
            data = list(value)
        
        # Calculate checksum over address + data
        checksum_data = address + data
        checksum = self._calculate_checksum(checksum_data)
        
        # Build complete message: F0 + manufacturer + device + model + command + address + data + checksum + F7
        message = [0xF0, manufacturer_id, device_id_int, model_id, command_id] + address + data + [checksum, 0xF7]
        
        return message
    
    def get_available_ports(self) -> List[str]:
        """Get list of available MIDI output ports."""
        return get_output_names()
    
    def select_midi_port(self) -> Optional[str]:
        """Interactive MIDI port selection."""
        ports = self.get_available_ports()
        if not ports:
            self.logger.error("No MIDI output ports found.")
            return None
        
        print("Available MIDI Ports:")
        for i, port in enumerate(ports):
            print(f"{i+1}: {port}")
        
        try:
            choice = int(input("Select a MIDI port (number): ")) - 1
            if 0 <= choice < len(ports):
                return ports[choice]
            else:
                print("Invalid selection.")
                return None
        except (ValueError, KeyboardInterrupt):
            return None
    
    def send_sysex(self, message: List[int], port_name: str) -> bool:
        """
        Send a SysEx message to the specified MIDI port.
        
        Args:
            message: Complete SysEx message as list of integers
            port_name: MIDI port name
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open_output(port_name) as port:
                # Strip F0 and F7 for mido (it adds them automatically)
                sysex_data = message[1:-1]
                port.send(Message('sysex', data=sysex_data))
                self.logger.info(f"Sent SysEx: {[hex(x) for x in message]}")
                time.sleep(self.delay)
                return True
        except Exception as e:
            self.logger.error(f"Error sending SysEx: {e}")
            return False
    
    def send_parameter(self, group_name: str, parameter_name: str, value: Union[int, List[int]], port_name: str, device_id: str = "10") -> bool:
        """
        Send a parameter change to the JV-1080.
        
        Args:
            group_name: Parameter group name
            parameter_name: Parameter name
            value: Parameter value
            port_name: MIDI port name
            device_id: Device ID in hex format
        
        Returns:
            True if successful, False otherwise
        """
        try:
            message = self.build_sysex_message(group_name, parameter_name, value, device_id)
            return self.send_sysex(message, port_name)
        except Exception as e:
            self.logger.error(f"Error sending parameter {parameter_name}: {e}")
            return False
    
    def get_parameter_info(self, group_name: str, parameter_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific parameter."""
        if group_name not in self.parameter_groups:
            return None
        
        group = self.parameter_groups[group_name]
        for param in group['parameters']:
            if param['name'] == parameter_name:
                return param
        return None
    
    def list_parameter_groups(self) -> List[str]:
        """Get list of all parameter groups."""
        return list(self.parameter_groups.keys())
    
    def list_parameters(self, group_name: str) -> List[str]:
        """Get list of parameters in a group."""
        if group_name not in self.parameter_groups:
            return []
        return [param['name'] for param in self.parameter_groups[group_name]['parameters']]
    
    def switch_mode(self, mode: str, port_name: str, device_id: str = "10") -> bool:
        """
        Switch JV-1080 mode.
        
        Args:
            mode: 'performance' or 'patch'
            port_name: MIDI port name
            device_id: Device ID in hex format
        
        Returns:
            True if successful, False otherwise
        """
        # Mode switching uses system common parameters
        # This would need to be added to the YAML config, but for now:
        mode_value = 1 if mode.lower() == 'performance' else 0
        
        # Build basic mode switch message (this is a simplified version)
        manufacturer_id = self._hex_to_int(self.common_info['manufacturer_id_hex'])
        device_id_int = self._hex_to_int(device_id)
        model_id = self._hex_to_int(self.common_info['model_id_hex'])
        command_id = self._hex_to_int(self.common_info['command_id_dt1_hex'])
        
        # Mode switch address (this may need adjustment based on your needs)
        address = [0x00, 0x00, 0x00, 0x00]
        data = [mode_value]
        
        checksum = self._calculate_checksum(address + data)
        message = [0xF0, manufacturer_id, device_id_int, model_id, command_id] + address + data + [checksum, 0xF7]
        
        return self.send_sysex(message, port_name)


# Example usage and helper functions
def main():
    """Example usage of JV1080Manager."""
    try:
        # Initialize manager
        jv = JV1080Manager()
        
        # Select MIDI port
        port = jv.select_midi_port()
        if not port:
            print("No MIDI port selected. Exiting.")
            return
        
        # Example: Set performance name
        success = jv.send_parameter(
            group_name='temp_performance_common',
            parameter_name='Performance name 1',
            value=65,  # ASCII 'A'
            port_name=port
        )
        
        if success:
            print("Parameter sent successfully!")
        else:
            print("Failed to send parameter.")
            
    except Exception as e:
        logging.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()
