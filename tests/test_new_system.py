"""
Tests for the new YAML-based JV-1080 system.
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import our new classes
from jv1080_manager import JV1080Manager
from sysex_parser import SysExParser
from preset_builder import PresetBuilder, JV1080Preset, PresetParameter

class TestJV1080Manager:
    """Test the main JV1080Manager class."""
    
    def test_manager_initialization(self):
        """Test that the manager initializes correctly."""
        manager = JV1080Manager()
        assert manager is not None
        assert 'roland_jv_1080' in manager.config
        assert 'sysex_common_info' in manager.config['roland_jv_1080']
        assert 'sysex_parameter_groups' in manager.config['roland_jv_1080']
    
    def test_hex_to_int(self):
        """Test hex string conversion."""
        manager = JV1080Manager()
        assert manager._hex_to_int("41") == 0x41
        assert manager._hex_to_int("6A") == 0x6A
        assert manager._hex_to_int("00") == 0x00
        assert manager._hex_to_int("FF") == 0xFF
    
    def test_checksum_calculation(self):
        """Test Roland checksum calculation."""
        manager = JV1080Manager()
        
        # Test known checksum
        data = [0x01, 0x00, 0x00, 0x00, 0x65]  # Address + data for setting 'A' (65)
        checksum = manager._calculate_checksum(data)
        expected = (0x80 - (sum(data) % 0x80)) % 0x80
        assert checksum == expected
    
    def test_build_sysex_message(self):
        """Test SysEx message building."""
        manager = JV1080Manager()
        
        # Test building a message for Performance name 1
        message = manager.build_sysex_message(
            group_name='temp_performance_common',
            parameter_name='Performance name 1',
            value=65  # ASCII 'A'
        )
        
        # Verify message structure
        assert message[0] == 0xF0  # SysEx start
        assert message[1] == 0x41  # Roland manufacturer ID
        assert message[2] == 0x10  # Device ID
        assert message[3] == 0x6A  # JV-1080 model ID
        assert message[4] == 0x12  # DT1 command
        assert message[5:9] == [0x01, 0x00, 0x00, 0x00]  # Address
        assert message[9] == 65   # Data (ASCII 'A')
        assert message[-1] == 0xF7  # SysEx end
        
        # Verify checksum
        checksum_data = message[5:-2]  # Address + data
        expected_checksum = (0x80 - (sum(checksum_data) % 0x80)) % 0x80
        assert message[-2] == expected_checksum
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        manager = JV1080Manager()
        
        # Test valid parameter
        param_info = manager.get_parameter_info('temp_performance_common', 'Performance name 1')
        assert param_info is not None
        assert param_info['min'] == 32
        assert param_info['max'] == 127
        
        # Test invalid group
        param_info = manager.get_parameter_info('invalid_group', 'Performance name 1')
        assert param_info is None
        
        # Test invalid parameter
        param_info = manager.get_parameter_info('temp_performance_common', 'Invalid Parameter')
        assert param_info is None
    
    def test_list_parameters(self):
        """Test parameter listing."""
        manager = JV1080Manager()
        
        # Test listing parameter groups
        groups = manager.list_parameter_groups()
        assert isinstance(groups, list)
        assert 'temp_performance_common' in groups        # Test listing parameters in a group
        params = manager.list_parameters('temp_performance_common')
        assert isinstance(params, list)
        assert 'Performance name 1' in params
        assert 'EFX:Type' in params
    
    @patch('jv1080_manager.get_output_names')
    def test_get_available_ports(self, mock_get_names):
        """Test MIDI port enumeration."""
        mock_get_names.return_value = ['Port 1', 'Port 2']
        
        manager = JV1080Manager()
        ports = manager.get_available_ports()
        
        assert ports == ['Port 1', 'Port 2']
        mock_get_names.assert_called_once()
    
    @patch('jv1080_manager.open_output')
    def test_send_sysex(self, mock_open_output):
        """Test SysEx message sending."""
        mock_port = Mock()
        mock_open_output.return_value.__enter__.return_value = mock_port
        
        manager = JV1080Manager()
        message = [0xF0, 0x41, 0x10, 0x6A, 0x12, 0x01, 0x00, 0x00, 0x00, 0x65, 0x15, 0xF7]
        
        result = manager.send_sysex(message, "test_port")
        
        assert result is True
        mock_open_output.assert_called_once_with("test_port")
        mock_port.send.assert_called_once()


class TestSysExParser:
    """Test the SysEx parser."""
    
    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = SysExParser()
        assert parser is not None
        assert parser.manager is not None
        assert hasattr(parser, 'address_lookup')
    
    def test_roland_header_validation(self):
        """Test Roland header validation."""
        parser = SysExParser()
        
        # Valid header
        valid_message = [0xF0, 0x41, 0x10, 0x6A, 0x12, 0x00, 0x00, 0x00, 0x00]
        assert parser._validate_roland_header(valid_message) is True
        
        # Invalid header (wrong manufacturer)
        invalid_message = [0xF0, 0x42, 0x10, 0x6A, 0x12, 0x00, 0x00, 0x00, 0x00]
        assert parser._validate_roland_header(invalid_message) is False
        
        # Too short
        short_message = [0xF0, 0x41]
        assert parser._validate_roland_header(short_message) is False
    
    def test_checksum_verification(self):
        """Test checksum verification."""
        parser = SysExParser()
        
        # Build a message with correct checksum
        address_data = [0x01, 0x00, 0x00, 0x00, 0x65]  # Address + data
        checksum = (0x80 - (sum(address_data) % 0x80)) % 0x80
        message = [0xF0, 0x41, 0x10, 0x6A, 0x12] + address_data + [checksum, 0xF7]
        
        assert parser._verify_checksum(message) is True
        
        # Corrupt checksum
        bad_message = message[:-2] + [0x00, 0xF7]
        assert parser._verify_checksum(bad_message) is False
    
    def test_sysex_message_extraction(self):
        """Test SysEx message extraction from binary data."""
        parser = SysExParser()
        
        # Create test data with two SysEx messages
        message1 = [0xF0, 0x41, 0x10, 0x6A, 0x12, 0x01, 0x00, 0x00, 0x00, 0x65, 0x15, 0xF7]
        message2 = [0xF0, 0x41, 0x10, 0x6A, 0x12, 0x01, 0x00, 0x00, 0x01, 0x66, 0x13, 0xF7]
        test_data = bytes(message1 + message2)
        
        messages = parser._extract_sysex_messages(test_data)
        
        assert len(messages) == 2
        assert messages[0] == message1
        assert messages[1] == message2


class TestPresetBuilder:
    """Test the preset builder."""
    
    def test_builder_initialization(self):
        """Test builder initialization."""
        builder = PresetBuilder()
        assert builder is not None
        assert builder.manager is not None
        assert builder.current_preset is None
    
    def test_create_new_preset(self):
        """Test preset creation."""
        builder = PresetBuilder()
        
        preset = builder.create_new_preset(
            name="Test Preset",
            preset_type="performance",
            description="A test preset"
        )
        
        assert preset.name == "Test Preset"
        assert preset.preset_type == "performance"
        assert preset.description == "A test preset"
        assert len(preset.parameters) == 0
        assert builder.current_preset == preset
    
    def test_add_parameter(self):
        """Test adding parameters to preset."""
        builder = PresetBuilder()
        builder.create_new_preset("Test", "performance")
        
        # Add valid parameter
        result = builder.add_parameter(
            group_name='temp_performance_common',
            parameter_name='Performance name 1',
            value=65
        )
        
        assert result is True
        assert len(builder.current_preset.parameters) == 1
        param = builder.current_preset.parameters[0]
        assert param.group_name == 'temp_performance_common'
        assert param.parameter_name == 'Performance name 1'
        assert param.value == 65
        
        # Try to add invalid parameter
        result = builder.add_parameter(
            group_name='invalid_group',
            parameter_name='Invalid Param',
            value=100
        )
        
        assert result is False
        assert len(builder.current_preset.parameters) == 1  # Should not have added
    
    def test_set_performance_name(self):
        """Test setting performance name."""
        builder = PresetBuilder()
        builder.create_new_preset("Test", "performance")
        
        result = builder.set_performance_name("TEST NAME")
        
        assert result is True
        # Should have added 12 parameters (one for each character position)
        name_params = [p for p in builder.current_preset.parameters 
                      if p.parameter_name.startswith('Performance name')]
        assert len(name_params) == 12
        
        # Check first few characters
        assert name_params[0].value == ord('T')
        assert name_params[1].value == ord('E')
        assert name_params[2].value == ord('S')
        assert name_params[3].value == ord('T')
        assert name_params[4].value == ord(' ')
    
    def test_preset_serialization(self):
        """Test preset saving and loading."""
        builder = PresetBuilder()
        builder.create_new_preset("Test Preset", "performance", "Test description")
        builder.add_parameter('temp_performance_common', 'EFX:Type', 5)
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save preset
            result = builder.save_preset(builder.current_preset, temp_path)
            assert result is True
            
            # Load preset
            loaded_preset = builder.load_preset(temp_path)
            assert loaded_preset is not None
            assert loaded_preset.name == "Test Preset"
            assert loaded_preset.preset_type == "performance"
            assert loaded_preset.description == "Test description"
            assert len(loaded_preset.parameters) == 1
            assert loaded_preset.parameters[0].parameter_name == 'EFX:Type'
            assert loaded_preset.parameters[0].value == 5
            
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)


# Integration tests
class TestSystemIntegration:
    """Test integration between components."""
    
    def test_manager_parser_integration(self):
        """Test that manager and parser work together."""
        manager = JV1080Manager()
        parser = SysExParser()
        
        # Both should have the same configuration
        assert manager.config == parser.config
        assert manager.parameter_groups == parser.parameter_groups
    
    def test_builder_manager_integration(self):
        """Test that builder and manager work together."""
        builder = PresetBuilder()
        manager = builder.manager
        
        # Create a preset and verify parameter info
        builder.create_new_preset("Test", "performance")
        builder.add_parameter('temp_performance_common', 'EFX:Type', 5)
        
        param_info = manager.get_parameter_info('temp_performance_common', 'EFX:Type')
        assert param_info is not None
        
        # The parameter should be within valid range
        preset_param = builder.current_preset.parameters[0]
        assert param_info['min'] <= preset_param.value <= param_info['max']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
