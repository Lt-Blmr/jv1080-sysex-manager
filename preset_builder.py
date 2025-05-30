"""
JV-1080 Preset Builder
Create and manage presets using the modern YAML-based system.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from jv1080_manager import JV1080Manager
import logging

@dataclass
class PresetParameter:
    """Represents a single parameter in a preset."""
    group_name: str
    parameter_name: str
    value: Union[int, List[int]]
    description: Optional[str] = None

@dataclass
class JV1080Preset:
    """Represents a complete JV-1080 preset."""
    name: str
    preset_type: str  # 'performance', 'patch', 'rhythm'
    description: str
    parameters: List[PresetParameter]
    tags: Optional[List[str]] = None
    author: str = "Unknown"
    created_date: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class PresetBuilder:
    """
    Build and manage JV-1080 presets using the modern YAML configuration.
    """
    
    def __init__(self, config_path: str = "roland_jv_1080_fixed.yaml"):
        """Initialize preset builder."""
        self.manager = JV1080Manager(config_path)
        self.config = self.manager.config
        self.parameter_groups = self.manager.parameter_groups
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Current preset being built
        self.current_preset: Optional[JV1080Preset] = None
    
    def create_new_preset(self, name: str, preset_type: str = "performance", description: str = "") -> JV1080Preset:
        """
        Create a new preset.
        
        Args:
            name: Preset name
            preset_type: Type of preset ('performance', 'patch', etc.)
            description: Preset description
        
        Returns:
            New preset object
        """
        from datetime import datetime
        
        preset = JV1080Preset(
            name=name,
            preset_type=preset_type,
            description=description,
            parameters=[],
            created_date=datetime.now().isoformat()
        )
        
        self.current_preset = preset
        self.logger.info(f"Created new preset: {name}")
        return preset
    
    def add_parameter(self, group_name: str, parameter_name: str, value: Union[int, List[int]], description: str = "") -> bool:
        """
        Add a parameter to the current preset.
        
        Args:
            group_name: Parameter group name
            parameter_name: Parameter name
            value: Parameter value
            description: Optional description
        
        Returns:
            True if successful, False otherwise
        """
        if not self.current_preset:
            self.logger.error("No current preset. Create a new preset first.")
            return False
        
        # Validate parameter exists
        param_info = self.manager.get_parameter_info(group_name, parameter_name)
        if not param_info:
            self.logger.error(f"Unknown parameter: {parameter_name} in group {group_name}")
            return False
        
        # Validate value range
        if isinstance(value, int) and 'min' in param_info and 'max' in param_info:
            if not (param_info['min'] <= value <= param_info['max']):
                self.logger.error(f"Value {value} out of range [{param_info['min']}-{param_info['max']}] for {parameter_name}")
                return False
        
        # Add parameter
        preset_param = PresetParameter(
            group_name=group_name,
            parameter_name=parameter_name,
            value=value,
            description=description
        )
        
        # Check if parameter already exists and update it
        for i, existing_param in enumerate(self.current_preset.parameters):
            if (existing_param.group_name == group_name and 
                existing_param.parameter_name == parameter_name):
                self.current_preset.parameters[i] = preset_param
                self.logger.info(f"Updated parameter: {parameter_name}")
                return True
        
        # Add new parameter
        self.current_preset.parameters.append(preset_param)
        self.logger.info(f"Added parameter: {parameter_name} = {value}")
        return True
    
    def remove_parameter(self, group_name: str, parameter_name: str) -> bool:
        """Remove a parameter from the current preset."""
        if not self.current_preset:
            self.logger.error("No current preset")
            return False
        
        for i, param in enumerate(self.current_preset.parameters):
            if param.group_name == group_name and param.parameter_name == parameter_name:
                del self.current_preset.parameters[i]
                self.logger.info(f"Removed parameter: {parameter_name}")
                return True
        
        self.logger.warning(f"Parameter not found: {parameter_name}")
        return False
    
    def set_performance_name(self, name: str) -> bool:
        """
        Set the performance name (12 characters max).
        
        Args:
            name: Performance name string
        
        Returns:
            True if successful
        """
        if not self.current_preset:
            self.logger.error("No current preset")
            return False
        
        # Convert string to ASCII values and pad/truncate to 12 characters
        name = name[:12].ljust(12)  # Pad with spaces if needed
        ascii_values = [ord(c) for c in name]
        
        # Set each character as a separate parameter
        success = True
        for i, value in enumerate(ascii_values):
            param_name = f"Performance name {i+1}"
            if not self.add_parameter('temp_performance_common', param_name, value):
                success = False
        
        return success
    
    def set_efx_parameters(self, efx_type: int, params: List[int]) -> bool:
        """
        Set EFX parameters.
        
        Args:
            efx_type: EFX type (0-39)
            params: List of parameter values (up to 12 parameters)
        
        Returns:
            True if successful
        """
        if not self.current_preset:
            self.logger.error("No current preset")
            return False
        
        success = True
        
        # Set EFX type
        if not self.add_parameter('temp_performance_common', 'EFX:Type', efx_type):
            success = False
        
        # Set parameters (pad with zeros if needed)
        params = (params + [0] * 12)[:12]  # Ensure we have exactly 12 parameters
        
        for i, value in enumerate(params):
            param_name = f"EFX:Parameter {i+1}"
            if not self.add_parameter('temp_performance_common', param_name, value):
                success = False
        
        return success
    
    def apply_preset_to_jv1080(self, preset: JV1080Preset, port_name: str, device_id: str = "10") -> Tuple[int, int]:
        """
        Apply a preset to the JV-1080.
        
        Args:
            preset: Preset to apply
            port_name: MIDI port name
            device_id: Device ID in hex format
        
        Returns:
            Tuple of (successful_parameters, total_parameters)
        """
        success_count = 0
        total_count = len(preset.parameters)
        
        self.logger.info(f"Applying preset '{preset.name}' to JV-1080...")
        
        for param in preset.parameters:
            if self.manager.send_parameter(
                group_name=param.group_name,
                parameter_name=param.parameter_name,
                value=param.value,
                port_name=port_name,
                device_id=device_id
            ):
                success_count += 1
            else:
                self.logger.warning(f"Failed to send parameter: {param.parameter_name}")
        
        self.logger.info(f"Applied {success_count}/{total_count} parameters")
        return success_count, total_count
    
    def save_preset(self, preset: JV1080Preset, file_path: Union[str, Path]) -> bool:
        """
        Save a preset to a JSON file.
        
        Args:
            preset: Preset to save
            file_path: Output file path
        
        Returns:
            True if successful
        """
        file_path = Path(file_path)
        
        try:
            # Convert to dict for JSON serialization
            preset_dict = asdict(preset)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(preset_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved preset to: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error saving preset: {e}")
            return False
    
    def load_preset(self, file_path: Union[str, Path]) -> Optional[JV1080Preset]:
        """
        Load a preset from a JSON file.
        
        Args:
            file_path: Preset file path
        
        Returns:
            Loaded preset or None if failed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"Preset file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                preset_dict = json.load(f)
            
            # Convert parameters back to PresetParameter objects
            parameters = []
            for param_dict in preset_dict['parameters']:
                param = PresetParameter(**param_dict)
                parameters.append(param)
            
            preset_dict['parameters'] = parameters
            preset = JV1080Preset(**preset_dict)
            
            self.current_preset = preset
            self.logger.info(f"Loaded preset: {preset.name}")
            return preset
        
        except Exception as e:
            self.logger.error(f"Error loading preset: {e}")
            return None
    
    def export_preset_to_python(self, preset: JV1080Preset, file_path: Union[str, Path]) -> bool:
        """
        Export a preset to a Python file for easy reuse.
        
        Args:
            preset: Preset to export
            file_path: Output file path
        
        Returns:
            True if successful
        """
        file_path = Path(file_path)
        
        try:
            python_code = f'''"""
JV-1080 Preset: {preset.name}
{preset.description}

Type: {preset.preset_type}
Author: {preset.author}
Created: {preset.created_date}
Parameters: {len(preset.parameters)}
"""

from jv1080_manager import JV1080Manager

def apply_preset(port_name: str, device_id: str = "10"):
    """Apply the preset '{preset.name}' to the JV-1080."""
    jv = JV1080Manager()
    success_count = 0
    total_count = {len(preset.parameters)}
    
'''
            
            # Group parameters by group for cleaner code
            grouped = {}
            for param in preset.parameters:
                if param.group_name not in grouped:
                    grouped[param.group_name] = []
                grouped[param.group_name].append(param)
            
            for group_name, params in grouped.items():
                python_code += f'\n    # {group_name.replace("_", " ").title()}\n'
                
                for param in params:
                    value_repr = repr(param.value) if isinstance(param.value, list) else str(param.value)
                    comment = f"  # {param.description}" if param.description else ""
                    
                    python_code += f'''    if jv.send_parameter("{param.group_name}", "{param.parameter_name}", {value_repr}, port_name, device_id):{comment}
        success_count += 1
    
'''
            
            python_code += f'''    print(f"Applied {{success_count}}/{{total_count}} parameters")
    return success_count == total_count

def get_preset_info():
    """Get information about this preset."""
    return {{
        "name": "{preset.name}",
        "type": "{preset.preset_type}",
        "author": "{preset.author}",
        "description": "{preset.description}",
        "parameter_count": {len(preset.parameters)},
        "tags": {preset.tags!r}
    }}

if __name__ == "__main__":
    # Interactive usage
    from jv1080_manager import JV1080Manager
    
    jv = JV1080Manager()
    port = jv.select_midi_port()
    
    if port:
        print(f"Applying preset: {preset.name}")
        success = apply_preset(port)
        if success:
            print("Preset applied successfully!")
        else:
            print("Some parameters failed to apply.")
    else:
        print("No MIDI port selected.")
'''
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            self.logger.info(f"Exported preset to Python file: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting preset: {e}")
            return False
    
    def list_available_parameters(self, group_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List available parameters.
        
        Args:
            group_name: Optional group name to filter by
        
        Returns:
            Dictionary mapping group names to parameter lists
        """
        if group_name:
            if group_name in self.parameter_groups:
                return {group_name: self.manager.list_parameters(group_name)}
            else:
                return {}
        else:
            result = {}
            for group in self.manager.list_parameter_groups():
                result[group] = self.manager.list_parameters(group)
            return result


def interactive_preset_builder():
    """Interactive preset builder."""
    builder = PresetBuilder()
    
    print("JV-1080 Preset Builder")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. Create new preset")
        print("2. Add parameter to current preset")
        print("3. Set performance name")
        print("4. Set EFX parameters")
        print("5. Save current preset")
        print("6. Load preset")
        print("7. Apply current preset to JV-1080")
        print("8. Export preset to Python")
        print("9. List available parameters")
        print("10. Show current preset info")
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        try:
            if choice == "1":
                name = input("Preset name: ").strip()
                preset_type = input("Preset type (performance/patch): ").strip() or "performance"
                description = input("Description: ").strip()
                builder.create_new_preset(name, preset_type, description)
                print(f"Created preset: {name}")
            
            elif choice == "2":
                if not builder.current_preset:
                    print("No current preset. Create one first.")
                    continue
                
                print("\nAvailable groups:", ", ".join(builder.manager.list_parameter_groups()))
                group = input("Group name: ").strip()
                
                if group in builder.parameter_groups:
                    params = builder.manager.list_parameters(group)
                    print(f"\nAvailable parameters in {group}:")
                    for i, param in enumerate(params):
                        print(f"  {i+1}. {param}")
                    
                    param_choice = input("Parameter name (or number): ").strip()
                    
                    # Handle numeric choice
                    if param_choice.isdigit():
                        param_idx = int(param_choice) - 1
                        if 0 <= param_idx < len(params):
                            param_name = params[param_idx]
                        else:
                            print("Invalid parameter number")
                            continue
                    else:
                        param_name = param_choice
                    
                    # Get parameter info for validation
                    param_info = builder.manager.get_parameter_info(group, param_name)
                    if param_info:
                        print(f"Parameter range: {param_info.get('min', 'N/A')} - {param_info.get('max', 'N/A')}")
                    
                    value_str = input("Value: ").strip()
                    try:
                        value = int(value_str)
                        description = input("Description (optional): ").strip()
                        
                        if builder.add_parameter(group, param_name, value, description):
                            print("Parameter added successfully")
                        else:
                            print("Failed to add parameter")
                    except ValueError:
                        print("Invalid value")
                else:
                    print("Invalid group name")
            
            elif choice == "3":
                if not builder.current_preset:
                    print("No current preset. Create one first.")
                    continue
                
                name = input("Performance name (12 chars max): ").strip()
                if builder.set_performance_name(name):
                    print("Performance name set successfully")
                else:
                    print("Failed to set performance name")
            
            elif choice == "4":
                if not builder.current_preset:
                    print("No current preset. Create one first.")
                    continue
                
                efx_type = int(input("EFX type (0-39): ").strip())
                params_str = input("Parameters (comma-separated, up to 12): ").strip()
                params = [int(x.strip()) for x in params_str.split(",") if x.strip()]
                
                if builder.set_efx_parameters(efx_type, params):
                    print("EFX parameters set successfully")
                else:
                    print("Failed to set EFX parameters")
            
            elif choice == "5":
                if not builder.current_preset:
                    print("No current preset to save")
                    continue
                
                filename = input("Save as (filename): ").strip()
                if not filename.endswith('.json'):
                    filename += '.json'
                
                if builder.save_preset(builder.current_preset, filename):
                    print(f"Preset saved to: {filename}")
                else:
                    print("Failed to save preset")
            
            elif choice == "6":
                filename = input("Load preset file: ").strip()
                preset = builder.load_preset(filename)
                if preset:
                    print(f"Loaded preset: {preset.name}")
                else:
                    print("Failed to load preset")
            
            elif choice == "7":
                if not builder.current_preset:
                    print("No current preset to apply")
                    continue
                
                port = builder.manager.select_midi_port()
                if port:
                    success, total = builder.apply_preset_to_jv1080(builder.current_preset, port)
                    print(f"Applied {success}/{total} parameters")
                else:
                    print("No MIDI port selected")
            
            elif choice == "8":
                if not builder.current_preset:
                    print("No current preset to export")
                    continue
                
                filename = input("Export as (filename): ").strip()
                if not filename.endswith('.py'):
                    filename += '.py'
                
                if builder.export_preset_to_python(builder.current_preset, filename):
                    print(f"Preset exported to: {filename}")
                else:
                    print("Failed to export preset")
            
            elif choice == "9":
                group = input("Group name (or press Enter for all): ").strip() or None
                params = builder.list_available_parameters(group)
                
                for group_name, param_list in params.items():
                    print(f"\n{group_name}:")
                    for param in param_list:
                        print(f"  {param}")
            
            elif choice == "10":
                if builder.current_preset:
                    preset = builder.current_preset
                    print(f"\nCurrent Preset: {preset.name}")
                    print(f"Type: {preset.preset_type}")
                    print(f"Description: {preset.description}")
                    print(f"Parameters: {len(preset.parameters)}")
                    print(f"Author: {preset.author}")
                    print(f"Created: {preset.created_date}")
                    print(f"Tags: {', '.join(preset.tags)}")
                else:
                    print("No current preset")
            
            elif choice == "0":
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice")
        
        except (ValueError, KeyboardInterrupt) as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    interactive_preset_builder()
