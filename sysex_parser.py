"""
SysEx File Parser for JV-1080
Parses existing .syx files and creates Python-based presets using YAML configuration.
"""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import struct
from dataclasses import dataclass
from jv1080_manager import JV1080Manager

@dataclass
class ParsedParameter:
    """Represents a parsed SysEx parameter."""
    group_name: str
    parameter_name: str
    value: Union[int, List[int]]
    address: List[int]
    raw_message: List[int]

@dataclass
class ParsedPreset:
    """Represents a complete parsed preset."""
    name: str
    preset_type: str  # 'performance', 'patch', etc.
    parameters: List[ParsedParameter]
    source_file: Optional[str] = None

class SysExParser:
    """
    Parses SysEx files and extracts JV-1080 parameters using YAML configuration.
    """
    
    def __init__(self, config_path: str = "roland_jv_1080_fixed.yaml"):
        """Initialize parser with YAML configuration."""
        self.manager = JV1080Manager(config_path)
        self.config = self.manager.config
        self.common_info = self.manager.common_info
        self.parameter_groups = self.manager.parameter_groups
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
          # Build address lookup table for faster parsing
        self._build_address_lookup()
    
    def _build_address_lookup(self):
        """Build lookup table: address -> (group_name, parameter_name, parameter_info)"""
        self.address_lookup = {}
        
        for group_name, group_info in self.parameter_groups.items():
            base_addr = [int(addr, 16) for addr in group_info['address_bytes_1_3_hex']]
            
            # Handle expansion card performance banks (0x11 address space)
            if base_addr[0] == 0x11 and group_name.startswith('expansion_performance'):
                # Generate addresses for multiple performance slots (64 performances typical for expansion cards)
                for performance_slot in range(64):
                    # Calculate performance address: 11 PP XX YY where PP is performance slot
                    perf_addr = base_addr.copy()
                    perf_addr[1] = performance_slot  # Performance slot number
                    
                    for param in group_info['parameters']:
                        addr_4 = int(param['offset_hex'], 16)
                        full_address = tuple(perf_addr + [addr_4])
                        # Include performance slot in group name for identification
                        perf_group_name = f"{group_name}_perf_{performance_slot:02d}"
                        self.address_lookup[full_address] = (perf_group_name, param['name'], param)
            else:
                # Standard address mapping for non-expansion card parameters
                for param in group_info['parameters']:
                    addr_4 = int(param['offset_hex'], 16)
                    full_address = tuple(base_addr + [addr_4])
                    self.address_lookup[full_address] = (group_name, param['name'], param)
    
    def _hex_to_int(self, hex_str: str) -> int:
        """Convert hex string to integer."""
        return int(hex_str, 16)
    
    def _validate_roland_header(self, message: List[int]) -> bool:
        """Validate that message has correct Roland JV-1080 header."""
        if len(message) < 6:
            return False
        
        expected_manufacturer = self._hex_to_int(self.common_info['manufacturer_id_hex'])
        expected_model = self._hex_to_int(self.common_info['model_id_hex'])
        expected_command = self._hex_to_int(self.common_info['command_id_dt1_hex'])
        
        return (message[0] == 0xF0 and
                message[1] == expected_manufacturer and
                message[3] == expected_model and
                message[4] == expected_command)
    
    def _extract_sysex_messages(self, data: bytes) -> List[List[int]]:
        """Extract individual SysEx messages from binary data."""
        messages = []
        current_message = []
        in_sysex = False
        
        for byte in data:
            if byte == 0xF0:  # Start of SysEx
                if in_sysex and current_message:
                    # Malformed: new SysEx before previous ended
                    self.logger.warning("Malformed SysEx: F0 found before F7")
                current_message = [byte]
                in_sysex = True
            elif byte == 0xF7:  # End of SysEx
                if in_sysex:
                    current_message.append(byte)
                    messages.append(current_message)
                    current_message = []
                    in_sysex = False
                else:
                    self.logger.warning("Malformed SysEx: F7 found without F0")
            elif in_sysex:
                current_message.append(byte)
        
        if in_sysex and current_message:
            self.logger.warning("Malformed SysEx: Missing F7 at end of data")
        
        return messages
    
    def _verify_checksum(self, message: List[int]) -> bool:
        """Verify Roland checksum."""
        if len(message) < 8:  # Minimum: F0 + header(4) + addr(4) + data(1) + checksum + F7
            return False
        
        # Extract address and data (everything between header and checksum)
        checksum_data = message[5:-2]  # Skip F0+header and checksum+F7
        calculated = (0x80 - (sum(checksum_data) % 0x80)) % 0x80
        received = message[-2]
        
        return calculated == received
    
    def parse_sysex_message(self, message: List[int]) -> Optional[ParsedParameter]:
        """Parse a single SysEx message into a parameter."""
        if not self._validate_roland_header(message):
            self.logger.debug("Invalid Roland header, skipping message")
            return None
        
        if not self._verify_checksum(message):
            self.logger.warning(f"Invalid checksum in message: {[hex(x) for x in message]}")
            return None
        
        if len(message) < 10:  # Minimum valid message length
            self.logger.debug("Message too short")
            return None
        
        # Extract address (4 bytes after command)
        address = tuple(message[5:9])
        
        # Extract data (between address and checksum)
        data_bytes = message[9:-2]
        
        # Look up parameter info
        if address in self.address_lookup:
            group_name, param_name, param_info = self.address_lookup[address]
            
            # Convert data based on parameter info
            if len(data_bytes) == 1:
                value = data_bytes[0]
            else:
                value = data_bytes
            
            return ParsedParameter(
                group_name=group_name,
                parameter_name=param_name,
                value=value,
                address=list(address),
                raw_message=message
            )
        else:
            self.logger.debug(f"Unknown address: {[hex(x) for x in address]}")
            return None
    
    def parse_sysex_file(self, file_path: Union[str, Path]) -> List[ParsedParameter]:
        """
        Parse a .syx file and extract all recognized parameters.
        
        Args:
            file_path: Path to .syx file
        
        Returns:
            List of parsed parameters
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"SysEx file not found: {file_path}")
        
        self.logger.info(f"Parsing SysEx file: {file_path}")
        
        # Read binary data
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Extract SysEx messages
        messages = self._extract_sysex_messages(data)
        self.logger.info(f"Found {len(messages)} SysEx messages")
          # Parse each message
        parsed_parameters = []
        for i, message in enumerate(messages):
            # Check if this is an expansion card bulk data message
            if len(message) >= 10:
                address = tuple(message[5:9])
                if address[0] == 0x11:  # Expansion card address space
                    # Use bulk data parsing for expansion cards
                    bulk_params = self._parse_bulk_data_message(message)
                    if bulk_params:
                        # Set raw_message for all bulk parameters
                        for param in bulk_params:
                            param.raw_message = message
                        parsed_parameters.extend(bulk_params)
                        continue
            
            # Use traditional single-parameter parsing
            param = self.parse_sysex_message(message)
            if param:
                param.raw_message = message  # Store original message
                parsed_parameters.append(param)
            else:
                self.logger.debug(f"Could not parse message {i}: {[hex(x) for x in message]}")
        
        self.logger.info(f"Successfully parsed {len(parsed_parameters)} parameters")
        return parsed_parameters
    
    def group_parameters_by_type(self, parameters: List[ParsedParameter]) -> Dict[str, List[ParsedParameter]]:
        """Group parameters by their group type."""
        grouped = {}
        for param in parameters:
            if param.group_name not in grouped:
                grouped[param.group_name] = []
            grouped[param.group_name].append(param)
        return grouped
    
    def create_preset_from_parameters(self, parameters: List[ParsedParameter], preset_name: str = "Parsed Preset") -> ParsedPreset:
        """Create a preset object from parsed parameters."""
        # Determine preset type based on parameter groups
        group_names = {param.group_name for param in parameters}
        
        if any('performance' in name for name in group_names):
            preset_type = 'performance'
        elif any('patch' in name for name in group_names):
            preset_type = 'patch'
        else:
            preset_type = 'unknown'
        
        return ParsedPreset(
            name=preset_name,
            preset_type=preset_type,
            parameters=parameters
        )
    
    def export_preset_to_python(self, preset: ParsedPreset, output_path: Union[str, Path]) -> None:
        """
        Export a parsed preset to a Python file for easy reuse.
        
        Args:
            preset: Parsed preset to export
            output_path: Output file path
        """
        output_path = Path(output_path)
        
        python_code = f'''"""
JV-1080 Preset: {preset.name}
Generated by SysExParser from {preset.source_file or "unknown source"}
Type: {preset.preset_type}
"""

from jv1080_manager import JV1080Manager

def apply_preset(jv1080_manager: JV1080Manager, port_name: str, device_id: str = "10"):
    """Apply this preset to the JV-1080."""
    success_count = 0
    total_count = {len(preset.parameters)}
    
'''
        
        # Group parameters for cleaner code
        grouped = self.group_parameters_by_type(preset.parameters)
        
        for group_name, params in grouped.items():
            python_code += f'\n    # {group_name.replace("_", " ").title()} Parameters\n'
            
            for param in params:
                value_repr = repr(param.value) if isinstance(param.value, list) else str(param.value)
                python_code += f'''    if jv1080_manager.send_parameter(
        group_name="{param.group_name}",
        parameter_name="{param.parameter_name}",
        value={value_repr},
        port_name=port_name,
        device_id=device_id
    ):
        success_count += 1
    
'''
        
        python_code += f'''    return success_count, total_count

def get_preset_info():
    """Get information about this preset."""
    return {{
        "name": "{preset.name}",
        "type": "{preset.preset_type}",
        "parameter_count": {len(preset.parameters)},
        "groups": {list(grouped.keys())!r}
    }}

if __name__ == "__main__":
    # Example usage
    jv = JV1080Manager()
    port = jv.select_midi_port()
    if port:
        success, total = apply_preset(jv, port)
        print(f"Applied {{success}}/{{total}} parameters successfully")
    else:
        print("No MIDI port selected")
'''
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(python_code)
        
        self.logger.info(f"Exported preset to: {output_path}")
    
    def batch_parse_directory(self, directory_path: Union[str, Path], output_dir: Optional[Union[str, Path]] = None) -> List[ParsedPreset]:
        """
        Parse all .syx files in a directory and optionally export them.
        
        Args:
            directory_path: Directory containing .syx files
            output_dir: Optional directory to export Python presets
        
        Returns:
            List of parsed presets
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        syx_files = list(directory_path.glob("*.syx"))
        if not syx_files:
            self.logger.warning(f"No .syx files found in {directory_path}")
            return []
        
        self.logger.info(f"Found {len(syx_files)} .syx files")
        
        presets = []
        for syx_file in syx_files:
            try:
                parameters = self.parse_sysex_file(syx_file)
                if parameters:
                    preset_name = syx_file.stem
                    preset = self.create_preset_from_parameters(parameters, preset_name)
                    preset.source_file = str(syx_file)
                    presets.append(preset)
                    
                    # Export to Python if output directory specified
                    if output_dir:
                        output_dir = Path(output_dir)
                        output_dir.mkdir(exist_ok=True)
                        output_file = output_dir / f"{preset_name}_preset.py"
                        self.export_preset_to_python(preset, output_file)
                        
            except Exception as e:
                self.logger.error(f"Error parsing {syx_file}: {e}")
        
        self.logger.info(f"Successfully parsed {len(presets)} presets")
        return presets


    def _parse_bulk_data_message(self, message: List[int]) -> List[ParsedParameter]:
        """
        Parse a bulk data SysEx message into individual parameters.
        Used for expansion card messages that contain multiple parameters per message.
        
        Args:
            message: SysEx message bytes
            
        Returns:
            List of parsed parameters extracted from the bulk data
        """
        if not self._validate_roland_header(message):
            return []
        
        if not self._verify_checksum(message):
            self.logger.warning(f"Invalid checksum in bulk message: {[hex(x) for x in message]}")
            return []
        
        if len(message) < 10:
            return []
        
        # Extract address and data
        base_address = tuple(message[5:9])
        data_bytes = message[9:-2]
        
        # Check if this is an expansion card address (0x11)
        if base_address[0] != 0x11:
            return []
        
        addr_space, perf_slot, part_type, offset = base_address
        
        parsed_params = []
          # Handle different message types based on part_type
        if part_type == 0x00:  # Performance common
            parsed_params.extend(self._parse_common_bulk_data(perf_slot, data_bytes))
        elif part_type in [0x10, 0x12, 0x14, 0x16]:  # Performance parts
            part_num = (part_type - 0x10) // 2 + 1
            parsed_params.extend(self._parse_part_bulk_data(perf_slot, part_num, data_bytes))
        elif part_type == 0x20:  # Patch common
            parsed_params.extend(self._parse_patch_common_bulk_data(perf_slot, data_bytes))
        elif part_type in [0x22, 0x24, 0x26, 0x28]:  # Patch parts
            part_num = (part_type - 0x22) // 2 + 1
            parsed_params.extend(self._parse_patch_part_bulk_data(perf_slot, part_num, data_bytes))
        elif part_type == 0x60:  # Rhythm common
            parsed_params.extend(self._parse_rhythm_common_bulk_data(perf_slot, data_bytes))
        elif 0x24 <= part_type <= 0x62:  # Rhythm parts 2-64 (0x24 = part 2, 0x62 = part 64)
            part_num = part_type - 0x23  # Convert address byte to part number (0x24 -> 2, 0x25 -> 3, etc.)
            parsed_params.extend(self._parse_rhythm_part_bulk_data(perf_slot, part_num, data_bytes))
        return parsed_params
    
    def _parse_common_bulk_data(self, perf_slot: int, data_bytes: List[int]) -> List[ParsedParameter]:
        """Parse common parameters from bulk data."""
        parsed_params = []
        
        if len(data_bytes) < 12:
            return parsed_params
        
        # Extract performance name (first 12 bytes)
        name_bytes = data_bytes[:12]
        group_name = f"expansion_performance_common_perf_{perf_slot:02d}"
        parsed_params.append(ParsedParameter(
            group_name=group_name,
            parameter_name="Performance name",
            value=list(name_bytes),
            address=[0x11, perf_slot, 0x00, 0x00],
            raw_message=[]
        ))
        
        # Parse remaining common parameters
        common_data = data_bytes[12:]
        common_param_info = self._get_common_parameter_definitions()
        
        for i, (param_name, param_info) in enumerate(common_param_info.items()):
            if i >= len(common_data):
                break
            param_value = common_data[i]
            # Signed conversion if needed
            if param_info.get('type') == 'signed' and param_value > 63:
                param_value -= 128
            
            parsed_params.append(ParsedParameter(
                group_name=group_name,
                parameter_name=param_name,
                value=param_value,
                address=[0x11, perf_slot, 0x00, 0x0C + i],
                raw_message=[]
            ))
        
        return parsed_params
    
    def _parse_part_bulk_data(self, perf_slot: int, part_num: int, data_bytes: List[int]) -> List[ParsedParameter]:
        """Parse part parameters from bulk data."""
        parsed_params = []
        
        group_name = f"expansion_performance_part_{part_num}_perf_{perf_slot:02d}"
        part_param_info = self._get_part_parameter_definitions(part_num)
        param_names = list(part_param_info.keys())
        
        for i, name in enumerate(param_names):
            if i >= len(data_bytes):
                break
            param_value = data_bytes[i]
            param_info = part_param_info[name]
            if param_info.get('type') == 'signed' and param_value > 63:
                param_value -= 128
            parsed_params.append(ParsedParameter(
                group_name=group_name,
                parameter_name=name,
                value=param_value,
                address=[0x11, perf_slot, 0x10 + (part_num - 1) * 2, i],
                raw_message=[]
            ))
        
        return parsed_params
    
    def _parse_patch_common_bulk_data(self, perf_slot: int, data_bytes: List[int]) -> List[ParsedParameter]:
        """Parse Expansion Card patch common bulk data."""
        parsed_params = []
        group_key = 'expansion_patch_common'
        group_info = self.parameter_groups.get(group_key, {})
        base_addr = [0x11, perf_slot, int(group_info.get('address_bytes_1_3_hex',[None])[2],16)]
        for param in group_info.get('parameters', []):
            off = int(param['offset_hex'], 16)
            if off < len(data_bytes):
                value = data_bytes[off]
                parsed_params.append(ParsedParameter(
                    group_name=f"{group_key}_perf_{perf_slot:02d}",
                    parameter_name=param['name'],
                    value=value,
                    address=base_addr + [off],
                    raw_message=[]
                ))
        return parsed_params

    def _parse_patch_part_bulk_data(self, perf_slot: int, part_num: int, data_bytes: List[int]) -> List[ParsedParameter]:
        """Parse Expansion Card patch part bulk data."""
        parsed_params = []
        group_key = f'expansion_patch_part_{part_num}'
        group_info = self.parameter_groups.get(group_key, {})
        base_addr = [0x11, perf_slot, int(group_info.get('address_bytes_1_3_hex',[None])[2],16)]
        for param in group_info.get('parameters', []):
            off = int(param['offset_hex'], 16)
            if off < len(data_bytes):
                value = data_bytes[off]
                parsed_params.append(ParsedParameter(
                    group_name=f"{group_key}_perf_{perf_slot:02d}",
                    parameter_name=param['name'],
                    value=value,
                    address=base_addr + [off],
                    raw_message=[]
                ))
        return parsed_params

    def _parse_rhythm_common_bulk_data(self, perf_slot: int, data_bytes: List[int]) -> List[ParsedParameter]:
        """Parse Expansion Card rhythm common bulk data."""
        parsed_params = []
        group_key = 'expansion_rhythm_common'
        group_info = self.parameter_groups.get(group_key, {})
        base_addr = [0x11, perf_slot, int(group_info.get('address_bytes_1_3_hex',[None])[2],16)]
        for param in group_info.get('parameters', []):
            off = int(param['offset_hex'], 16)
            if off < len(data_bytes):
                value = data_bytes[off]
                parsed_params.append(ParsedParameter(
                    group_name=f"{group_key}_perf_{perf_slot:02d}",
                    parameter_name=param['name'],
                    value=value,
                    address=base_addr + [off],
                    raw_message=[]
                ))
        return parsed_params

    def _parse_rhythm_part_bulk_data(self, perf_slot: int, part_num: int, data_bytes: List[int]) -> List[ParsedParameter]:
        """Parse Expansion Card rhythm part bulk data."""
        parsed_params = []
        group_key = f'expansion_rhythm_part_{part_num}'
        group_info = self.parameter_groups.get(group_key, {})
        base_addr = [0x11, perf_slot, int(group_info.get('address_bytes_1_3_hex',[None])[2],16)]
        for param in group_info.get('parameters', []):
            off = int(param['offset_hex'], 16)
            if off < len(data_bytes):
                value = data_bytes[off]
                parsed_params.append(ParsedParameter(
                    group_name=f"{group_key}_perf_{perf_slot:02d}",
                    parameter_name=param['name'],
                    value=value,
                    address=base_addr + [off],
                    raw_message=[]
                ))
        return parsed_params

    def _get_common_parameter_definitions(self) -> Dict[str, Dict]:
        """Get common parameter definitions from YAML config."""
        common_params = {}
        
        # Look up expansion_performance_common group in config
        groups = self.config.get('sysex_parameter_groups', {})
        common_group = groups.get('expansion_performance_common', {})
        parameters = common_group.get('parameters', [])
        
        # Skip the first 12 name parameters, get the actual common parameters
        for param in parameters[12:]:  # Skip name parameters
            param_name = param.get('name', '')
            param_info = {
                'min': param.get('min', 0),
                'max': param.get('max', 127),
                'bytes': param.get('bytes', 1),
                'type': param.get('type', 'unsigned')
            }
            common_params[param_name] = param_info
        
        return common_params
    
    def _get_part_parameter_definitions(self, part_num: int) -> Dict[str, Dict]:
        """Get part parameter definitions from YAML config."""
        part_params = {}
        
        # Look up the appropriate part group
        groups = self.config.get('sysex_parameter_groups', {})
        part_group_name = f'expansion_performance_part_{part_num}'
        part_group = groups.get(part_group_name, {})
        parameters = part_group.get('parameters', [])
        
        for param in parameters:
            param_name = param.get('name', '')
            param_info = {
                'min': param.get('min', 0),
                'max': param.get('max', 127),
                'bytes': param.get('bytes', 1),
                'type': param.get('type', 'unsigned')
            }
            part_params[param_name] = param_info
        
        return part_params
    
    def _get_patch_common_parameter_definitions(self) -> Dict[str, Dict]:
        """Load patch common defs from YAML."""
        grp = self.config['sysex_parameter_groups'].get('expansion_patch_common', {})
        return {p['name']:{'min':p.get('min'), 'max':p.get('max'), 'bytes':p.get('bytes'), 'type':p.get('type','unsigned')} for p in grp.get('parameters',[])}

    def _get_patch_part_parameter_definitions(self, part_num: int) -> Dict[str, Dict]:
        """Load patch part defs from YAML."""
        key = f'expansion_patch_part_{part_num}'
        grp = self.config['sysex_parameter_groups'].get(key, {})
        return {p['name']:{'min':p.get('min'), 'max':p.get('max'), 'bytes':p.get('bytes'), 'type':p.get('type','unsigned')} for p in grp.get('parameters',[])}

    def _get_rhythm_common_parameter_definitions(self) -> Dict[str, Dict]:
        """Load rhythm common defs from YAML."""
        grp = self.config['sysex_parameter_groups'].get('expansion_rhythm_common', {})
        return {p['name']:{'min':p.get('min'), 'max':p.get('max'), 'bytes':p.get('bytes'), 'type':p.get('type','unsigned')} for p in grp.get('parameters',[])}

    def _get_rhythm_part_parameter_definitions(self, part_num: int) -> Dict[str, Dict]:
        """Load rhythm part defs from YAML."""
        key = f'expansion_rhythm_part_{part_num}'
        grp = self.config['sysex_parameter_groups'].get(key, {})
        return {p['name']:{'min':p.get('min'), 'max':p.get('max'), 'bytes':p.get('bytes'), 'type':p.get('type','unsigned')} for p in grp.get('parameters',[])}

def main():
    """Example usage of SysExParser."""
    parser = SysExParser()
    
    print("JV-1080 SysEx Parser")
    print("1. Parse single .syx file")
    print("2. Parse directory of .syx files")
    print("3. Exit")
    
    choice = input("Select option: ").strip()
    
    if choice == "1":
        file_path = input("Enter path to .syx file: ").strip()
        try:
            parameters = parser.parse_sysex_file(file_path)
            if parameters:
                preset = parser.create_preset_from_parameters(parameters, Path(file_path).stem)
                preset.source_file = file_path
                
                output_path = f"{Path(file_path).stem}_preset.py"
                parser.export_preset_to_python(preset, output_path)
                print(f"Exported preset to: {output_path}")
            else:
                print("No parameters found in file")
        except Exception as e:
            print(f"Error: {e}")
    
    elif choice == "2":
        dir_path = input("Enter directory path: ").strip()
        output_dir = input("Enter output directory (or press Enter for current): ").strip()
        if not output_dir:
            output_dir = "exported_presets"
        
        try:
            presets = parser.batch_parse_directory(dir_path, output_dir)
            print(f"Parsed {len(presets)} presets")
        except Exception as e:
            print(f"Error: {e}")
    
    elif choice == "3":
        print("Goodbye!")
    
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
