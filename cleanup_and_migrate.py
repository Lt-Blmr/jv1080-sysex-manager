"""
Cleanup and Migration Script for JV-1080 SysEx Manager
Organizes old files and migrates to the new YAML-based system.
"""

import shutil
from pathlib import Path
import logging
from typing import List, Dict

def setup_logging():
    """Set up logging for the cleanup process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('cleanup_migration.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_directory_structure(base_path: Path, logger: logging.Logger):
    """Create the new organized directory structure."""
    directories = [
        "legacy",
        "legacy/scripts",
        "legacy/config",
        "presets",
        "presets/exported",
        "presets/python",
        "sysex_files",
        "examples",
        "docs"
    ]
    
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")

def move_legacy_files(base_path: Path, logger: logging.Logger):
    """Move old files to legacy directory."""
    legacy_dir = base_path / "legacy"
    legacy_scripts = legacy_dir / "scripts"
    legacy_config = legacy_dir / "config"
    
    # Files to move to legacy/scripts
    script_files = [
        "BaselineSwitchModes.py",
        "JV_TempPatchMode.py",
        "JV1080_SH-101Module.py",
        "MidiCommTest.py",
        "MonosynthModule.py",
        "Roland_sysex_working_241230.py",
        "RolandSysExManager.py",  # The one in scripts/
        "SwitchModes.py",
        "SwitchModes_Ch.py",
        "Sysex_Parser.py",
        "SysexTest.py",
        "TempTestBeta.py",
    ]
    
    # Move scripts
    scripts_dir = base_path / "scripts"
    if scripts_dir.exists():
        for script_file in script_files:
            source = scripts_dir / script_file
            if source.exists():
                destination = legacy_scripts / script_file
                shutil.move(str(source), str(destination))
                logger.info(f"Moved {script_file} to legacy/scripts/")
    
    # Files to move to legacy/config
    config_files = [
        "Global.ini",
        "jv1080_patch_database.json",
        "Roland_JV1080_Patches.ini",
        "TempTestBetaDelay.ini"
    ]
    
    config_dir = base_path / "config"
    if config_dir.exists():
        for config_file in config_files:
            source = config_dir / config_file
            if source.exists():
                destination = legacy_config / config_file
                shutil.move(str(source), str(destination))
                logger.info(f"Moved {config_file} to legacy/config/")
    
    # Move old RolandSysExManager.py from root
    old_manager = base_path / "RolandSysExManager.py"
    if old_manager.exists():
        shutil.move(str(old_manager), str(legacy_dir / "RolandSysExManager.py"))
        logger.info("Moved root RolandSysExManager.py to legacy/")
    
    # Move performance_builder_gui.py
    old_gui = base_path / "performance_builder_gui.py"
    if old_gui.exists():
        shutil.move(str(old_gui), str(legacy_scripts / "performance_builder_gui.py"))
        logger.info("Moved performance_builder_gui.py to legacy/scripts/")

def update_requirements(base_path: Path, logger: logging.Logger):
    """Update requirements.txt with new dependencies."""
    requirements_content = """# JV-1080 SysEx Manager Requirements
mido>=1.2.10
python-rtmidi>=1.4.0
PyYAML>=6.0
pytest>=7.0.0

# Optional GUI dependencies
tkinter  # Usually included with Python
"""
    
    requirements_path = base_path / "requirements.txt"
    with open(requirements_path, 'w') as f:
        f.write(requirements_content)
    
    logger.info("Updated requirements.txt")

def create_readme(base_path: Path, logger: logging.Logger):
    """Create updated README.md with new structure."""
    readme_content = """# JV-1080 SysEx Manager

Modern Python library for controlling the Roland JV-1080 synthesizer via MIDI SysEx messages.

## ✨ Features

- **YAML-based configuration** - Human-readable parameter definitions
- **Modern Python architecture** - Clean, type-hinted, well-documented code
- **SysEx file parser** - Extract parameters from existing .syx files
- **Preset builder** - Create and manage custom presets
- **Full parameter control** - Access all JV-1080 parameters via SysEx
- **Export capabilities** - Generate Python code from presets

## 📁 Project Structure

```
jv1080-sysex-manager/
├── jv1080_manager.py          # Main JV-1080 control class (YAML-based)
├── sysex_parser.py           # Parse .syx files using YAML config
├── preset_builder.py         # Create and manage presets
├── roland_jv_1080.yaml       # Parameter definitions and configuration
├── requirements.txt          # Python dependencies
├── presets/                  # Preset files
│   ├── exported/            # Exported Python presets
│   └── python/              # Hand-crafted Python presets
├── sysex_files/             # .syx files for parsing
├── examples/                # Usage examples
├── legacy/                  # Old files (kept for reference)
│   ├── scripts/            # Old script files
│   └── config/             # Old INI configuration files
└── tests/                   # Unit tests
```

## 🚀 Quick Start

### Basic Usage

```python
from jv1080_manager import JV1080Manager

# Initialize manager
jv = JV1080Manager()

# Select MIDI port
port = jv.select_midi_port()

# Send a parameter change
jv.send_parameter(
    group_name='temp_performance_common',
    parameter_name='EFX:Type',
    value=5,  # Reverb
    port_name=port
)
```

### Parse SysEx Files

```python
from sysex_parser import SysExParser

# Initialize parser
parser = SysExParser()

# Parse a .syx file
parameters = parser.parse_sysex_file("my_preset.syx")

# Export to Python
preset = parser.create_preset_from_parameters(parameters, "My Preset")
parser.export_preset_to_python(preset, "my_preset.py")
```

### Build Custom Presets

```python
from preset_builder import PresetBuilder

# Initialize builder
builder = PresetBuilder()

# Create new preset
preset = builder.create_new_preset("My Performance", "performance")

# Set performance name
builder.set_performance_name("LEAD SYNTH")

# Add EFX
builder.set_efx_parameters(efx_type=5, params=[64, 100, 80])

# Save preset
builder.save_preset(preset, "my_performance.json")

# Apply to JV-1080
port = builder.manager.select_midi_port()
builder.apply_preset_to_jv1080(preset, port)
```

## 📦 Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd jv1080-sysex-manager

# Install dependencies
pip install -r requirements.txt
```

## 🎛️ Available Scripts

| Script | Purpose |
|--------|---------|
| `jv1080_manager.py` | Main JV-1080 control class |
| `sysex_parser.py` | Parse and convert .syx files |
| `preset_builder.py` | Interactive preset builder |
| `cleanup_and_migrate.py` | Migration script (run once) |

## 🔧 Configuration

The system uses `roland_jv_1080.yaml` for all parameter definitions. This file contains:

- SysEx message structure information
- Parameter groups (Performance, Patch, etc.)
- Address mappings for all parameters
- Value ranges and validation rules

## 📚 Examples

See the `examples/` directory for detailed usage examples and preset templates.

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run specific test
pytest tests/test_sysex.py -v
```

## 🔄 Migration from Old System

If you're upgrading from the old INI-based system:

1. Run the migration script: `python cleanup_and_migrate.py`
2. Old files will be moved to `legacy/` directory
3. Update your code to use the new classes

## 📄 License

See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 🆘 Troubleshooting

### Common Issues

1. **No MIDI ports found**: Ensure your MIDI interface is connected and drivers are installed
2. **Invalid checksum errors**: Check your device ID setting and cable connections
3. **Parameter not found**: Verify parameter names against the YAML configuration

### Getting Help

- Check the `examples/` directory for usage patterns
- Review the `legacy/` directory for reference implementations
- Enable debug logging for detailed SysEx message information

## 📈 Roadmap

- [ ] GUI application for preset management
- [ ] Bulk parameter operations
- [ ] MIDI learn functionality
- [ ] More preset templates
- [ ] Performance optimization for large preset collections
"""

    readme_path = base_path / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    logger.info("Created updated README.md")

def create_examples(base_path: Path, logger: logging.Logger):
    """Create example files."""
    examples_dir = base_path / "examples"
    
    # Basic usage example
    basic_example = """#!/usr/bin/env python3
\"\"\"
Basic JV-1080 Usage Example
Demonstrates fundamental operations with the JV-1080.
\"\"\"

from jv1080_manager import JV1080Manager

def main():
    # Initialize JV-1080 manager
    jv = JV1080Manager()
    
    # Select MIDI port interactively
    port = jv.select_midi_port()
    if not port:
        print("No MIDI port selected. Exiting.")
        return
    
    print(f"Using MIDI port: {port}")
    
    # Switch to Performance mode
    print("Switching to Performance mode...")
    jv.switch_mode("performance", port)
    
    # Set performance name to "BASIC EX"
    print("Setting performance name...")
    performance_name = "BASIC EX"
    for i, char in enumerate(performance_name.ljust(12)[:12]):
        param_name = f"Performance name {i+1}"
        jv.send_parameter('temp_performance_common', param_name, ord(char), port)
    
    # Set some EFX parameters
    print("Setting EFX parameters...")
    jv.send_parameter('temp_performance_common', 'EFX:Type', 5, port)  # Reverb
    jv.send_parameter('temp_performance_common', 'EFX:Parameter 1', 64, port)
    jv.send_parameter('temp_performance_common', 'EFX:Parameter 2', 100, port)
    
    print("Basic example completed successfully!")

if __name__ == "__main__":
    main()
"""
    
    with open(examples_dir / "basic_usage.py", 'w') as f:
        f.write(basic_example)
    
    # Preset example
    preset_example = """#!/usr/bin/env python3
\"\"\"
Preset Management Example
Shows how to create, save, and load presets.
\"\"\"

from preset_builder import PresetBuilder

def create_sample_preset():
    \"\"\"Create a sample preset.\"\"\"
    builder = PresetBuilder()
    
    # Create new preset
    preset = builder.create_new_preset(
        name="Ambient Pad",
        preset_type="performance",
        description="Lush ambient pad with reverb and chorus"
    )
    
    # Set performance name
    builder.set_performance_name("AMBIENT")
    
    # Configure EFX (Reverb)
    builder.set_efx_parameters(
        efx_type=5,  # Reverb
        params=[80, 120, 64, 100, 50, 0, 0, 0, 0, 0, 0, 0]
    )
    
    # Add some additional parameters
    builder.add_parameter('temp_performance_common', 'EFX:Output level', 110)
    builder.add_parameter('temp_performance_common', 'EFX:Chorus send level', 40)
    builder.add_parameter('temp_performance_common', 'EFX:Reverb send level', 100)
    
    return preset

def main():
    builder = PresetBuilder()
    
    # Create sample preset
    print("Creating sample preset...")
    preset = create_sample_preset()
    
    # Save to JSON
    print("Saving preset...")
    builder.save_preset(preset, "ambient_pad.json")
    
    # Export to Python
    print("Exporting to Python...")
    builder.export_preset_to_python(preset, "ambient_pad_preset.py")
    
    # Load and apply
    print("Loading preset...")
    loaded_preset = builder.load_preset("ambient_pad.json")
    
    if loaded_preset:
        port = builder.manager.select_midi_port()
        if port:
            print("Applying preset to JV-1080...")
            success, total = builder.apply_preset_to_jv1080(loaded_preset, port)
            print(f"Applied {success}/{total} parameters successfully!")
    
    print("Preset example completed!")

if __name__ == "__main__":
    main()
"""
    
    with open(examples_dir / "preset_management.py", 'w') as f:
        f.write(preset_example)
    
    logger.info("Created example files")

def create_gitignore(base_path: Path, logger: logging.Logger):
    """Create .gitignore file."""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Project specific
*.log
cleanup_migration.log
exported_presets/
*.syx
presets/exported/*.py
temp_*

# OS
.DS_Store
Thumbs.db
"""
    
    gitignore_path = base_path / ".gitignore"
    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content)
    
    logger.info("Created .gitignore")

def main():
    """Run the cleanup and migration process."""
    base_path = Path.cwd()
    logger = setup_logging()
    
    logger.info("Starting JV-1080 SysEx Manager cleanup and migration")
    logger.info(f"Working directory: {base_path}")
    
    try:
        # Create new directory structure
        logger.info("Creating new directory structure...")
        create_directory_structure(base_path, logger)
        
        # Move legacy files
        logger.info("Moving legacy files...")
        move_legacy_files(base_path, logger)
        
        # Update requirements
        logger.info("Updating requirements...")
        update_requirements(base_path, logger)
        
        # Create documentation
        logger.info("Creating documentation...")
        create_readme(base_path, logger)
        
        # Create examples
        logger.info("Creating examples...")
        create_examples(base_path, logger)
        
        # Create .gitignore
        logger.info("Creating .gitignore...")
        create_gitignore(base_path, logger)
        
        logger.info("Migration completed successfully!")
        
        print("\\n" + "="*50)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\\nNext steps:")
        print("1. Review the new structure in your file explorer")
        print("2. Install updated dependencies: pip install -r requirements.txt")
        print("3. Try the examples in the examples/ directory")
        print("4. Start using the new jv1080_manager.py for your projects")
        print("5. Use sysex_parser.py to convert your existing .syx files")
        print("\\nOld files have been moved to the legacy/ directory for reference.")
        print("Check cleanup_migration.log for detailed information.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"\\nMigration failed: {e}")
        print("Check cleanup_migration.log for details.")

if __name__ == "__main__":
    main()
