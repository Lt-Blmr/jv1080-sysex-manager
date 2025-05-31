#!/usr/bin/env python3
"""
JV-1080 SysEx Parser Module

Parses Roland JV-1080 SysEx files (bulk dumps of 128 patches) and exports presets to YAML/JSON format.
Implements complete Common block (offsets 0–71) and Tone block (offsets 0–57) parameter mappings with value interpretation, analysis, and compare features.
"""

import os
import sys
import logging
import argparse
import statistics
import yaml
import json
import re
from typing import Any, List, Optional, Dict, Union
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict


@dataclass
class ParsedParameter:
    group_name: str
    parameter_name: str
    value: Any
    address: List[int]
    raw_message: List[int]
    patch_index: Optional[int] = None
    interpreted_value: Optional[str] = None
    value_range: Optional[str] = None
    manufacturer: Optional[int] = None
    device_id: Optional[int] = None
    model_id: Optional[int] = None
    command: Optional[int] = None


@dataclass
class ParsedPreset:
    name: str
    preset_type: str
    parameters: List[ParsedParameter]
    category: Optional[str] = None
    bank: Optional[str] = None
    patch_number: Optional[int] = None
    source_file: Optional[str] = None
    msb: Optional[int] = None  # MIDI Bank Select MSB
    lsb: Optional[int] = None  # MIDI Bank Select LSB
    pc: Optional[int] = None   # Program Change (0-127)


@dataclass
class AnalysisResult:
    total_presets: int
    parameter_statistics: Dict[str, Dict[str, Any]]
    category_distribution: Dict[str, int]
    common_parameter_values: Dict[str, List[Any]]
    tone_usage_patterns: Dict[str, Any]


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename or folder name."""
    # Remove or replace characters not allowed in Windows, macOS, Linux filenames
    # Windows: \\/:*?"<>|, also remove control chars
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = re.sub(r'\s+', '_', name)  # Replace whitespace with underscores
    name = re.sub(r'[^\w\-_.]', '', name)  # Remove any other non-safe chars
    name = name.strip('._')  # Remove leading/trailing dots/underscores
    if not name:
        name = 'untitled'
    return name


class SysExParser:
    """Parser for JV-1080 SysEx files."""
    
    def __init__(self):
        self.category_names = {
            0: "Piano", 1: "E.Piano", 2: "Organ", 3: "Accordion",
            4: "Bell", 5: "Mallet", 6: "Choir", 7: "Voice",
            8: "Sax", 9: "Brass", 10: "Reed", 11: "Pipe",
            12: "Synth Lead", 13: "Synth Pad", 14: "Synth FX", 15: "Strings",
            16: "Guitar", 17: "Bass", 18: "Plucked", 19: "Ethnic",
            20: "Percussion", 21: "SFX", 22: "Drums", 23: "User"
        }
        
        self.bank_names = {
            0: "Preset A", 1: "Preset B", 2: "Preset C", 3: "Preset D",
            4: "User", 5: "Card"
        }
    
    def _interpret_parameter_value(self, group_name: str, param_name: str, value: Any) -> tuple[str, str]:
        """Interpret parameter values into human-readable format."""
        interpreted = str(value)
        value_range = ""
        
        try:
            if group_name == "Common":
                if param_name == "category" and isinstance(value, int):
                    # built-in categories 0–31
                    if value <= 31:
                        interpreted = self.category_names.get(value, f"Unknown({value})")
                        value_range = "0-31"
                    # expansion boards: 32 → SR-JV80-01, 33 → SR-JV80-02, … up to e.g. 50
                    elif 32 <= value <= 50:
                        board_num = value - 31
                        interpreted = f"SR-JV80-{board_num:02d}"
                        value_range = "32-50 (expansion)"
                    else:
                        interpreted = f"Unknown({value})"
                        value_range = "0-31 + expansions"
                elif param_name == "bank" and isinstance(value, int):
                    interpreted = self.bank_names.get(value, f"Unknown({value})")
                    value_range = "0-5"
                elif param_name in ["chorus_send", "reverb_send", "output_level"]:
                    interpreted = f"{value}/127"
                    value_range = "0-127"
                elif param_name in ["fine_tune", "transpose", "key_transpose"]:
                    # These are centered at 64
                    offset = value - 64
                    interpreted = f"{offset:+d}" if offset != 0 else "0"
                    value_range = "0-127 (64=center)"
                elif param_name == "pb_range":
                    interpreted = f"±{value} semitones"
                    value_range = "0-24"
                elif param_name in ["portamento_switch", "tone_switch"]:
                    interpreted = "On" if value else "Off"
                    value_range = "0=Off, 1=On"
                elif param_name.endswith("_rate") or param_name.endswith("_level"):
                    interpreted = f"{value}/99" if value <= 99 else f"{value}/127"
                    value_range = "0-99" if value <= 99 else "0-127"
                elif param_name == "lfo2_dest" and isinstance(value, int):
                    # Bitmask interpretation
                    destinations = []
                    if value & 1: destinations.append("Pitch")
                    if value & 2: destinations.append("Filter") 
                    if value & 4: destinations.append("Amp")
                    interpreted = ", ".join(destinations) if destinations else "None"
                    value_range = "0-7 (bitmap)"
                    
            elif group_name.startswith("Tone"):
                if param_name == "waveform_bank":
                    interpreted = f"Bank {value}"
                    value_range = "0-63"
                elif param_name == "waveform_number":
                    interpreted = f"Wave {value}"
                    value_range = "0-127"
                elif param_name in ["coarse_tune", "fine_tune"]:
                    if param_name == "coarse_tune":
                        offset = value - 64
                        interpreted = f"{offset:+d} semitones"
                        value_range = "0-127 (64=center)"
                    else:
                        offset = value - 64
                        interpreted = f"{offset:+d} cents"
                        value_range = "0-127 (64=center)"
                elif param_name == "pan":
                    if value == 64:
                        interpreted = "Center"
                    elif value < 64:
                        interpreted = f"L{64-value}"
                    else:
                        interpreted = f"R{value-64}"
                    value_range = "0-127 (64=center)"
                elif param_name in ["porta_switch", "lfo_key_sync", "poly_mono_switch"]:
                    interpreted = "On" if value else "Off"
                    value_range = "0=Off, 1=On"
                elif param_name.endswith("_level") or param_name.endswith("_depth"):
                    interpreted = f"{value}/127"
                    value_range = "0-127"
                    
        except (ValueError, TypeError):
            pass  # Keep default string representation
            
        return interpreted, value_range
    
    def parse_sysex_file(self, file_path: str) -> List[ParsedParameter]:
        """Parse a .syx file and return all parameters."""
        parameters = []
        
        with open(file_path, 'rb') as f:
            data = f.read()
        
        logging.info(f"Loaded {len(data)} bytes from {file_path}")
        
        i = 0
        msg_count = 0
        while i < len(data):
            # Look for SysEx start (F0)
            if data[i] != 0xF0:
                i += 1
                continue
                
            # Find the end of this SysEx message (F7)
            start = i
            end = start + 1
            while end < len(data) and data[end] != 0xF7:
                end += 1
            
            if end >= len(data):
                break  # No F7 found
                
            # Extract the complete SysEx message (including F0 and F7)
            sysex_msg = data[start:end + 1]
            msg_count += 1
            
            # Parse this SysEx message
            msg_params = self._parse_sysex_message(sysex_msg)
            parameters.extend(msg_params)
            
            i = end + 1
            
        logging.info(f"Processed {msg_count} SysEx messages, found {len(parameters)} parameters")
        return parameters
    
    def _parse_sysex_message(self, sysex_msg: bytes) -> List[ParsedParameter]:
        """Parse a single SysEx message."""
        if len(sysex_msg) < 8:
            return []

        # must be Roland JV-1080 header
        if sysex_msg[:5] != b'\xF0\x41\x10\x6A\x12':
            return []

        addr_h, addr_m, addr_l = sysex_msg[5], sysex_msg[6], sysex_msg[7]
        address = [addr_h, addr_m, addr_l]
        payload = sysex_msg[8:-1]

        # skip SR-JV80 bank-select messages (00 xx 20) or any non-dump
        if addr_h not in (0x11, 0x03):
            logging.debug(f"Skipping non-dump Sysex (addr {addr_h:02X} {addr_m:02X} {addr_l:02X})")
            return []

        # … now your existing 0x11 and 0x03 parsing branches …
        # Handle 0x11 addresses (the actual format in our file)
        if addr_h == 0x11 and addr_l == 0x00:  # Common blocks: 11 XX 00
            logging.debug(f"Parsing Common block for patch {addr_m}")
            return self._parse_common_block(payload, address, sysex_msg)
        elif addr_h == 0x11 and addr_l in [0x10, 0x12, 0x14, 0x16]:  # Tone blocks: 11 XX YY
            # Determine tone number from the pattern
            # 11 00 10, 11 00 12, 11 00 14, 11 00 16 = Tones 1-4 for patch 0
            # 11 01 10, 11 01 12, 11 01 14, 11 01 16 = Tones 1-4 for patch 1, etc.
            tone_num = (addr_l - 0x10) // 2 + 1  # 0x10->1, 0x12->2, 0x14->3, 0x16->4
            logging.debug(f"Parsing Tone {tone_num} block for patch {addr_m}")
            params = self._parse_tone_block(payload, address, sysex_msg)
            for param in params:
                param.group_name = f"Tone{tone_num}"
            return params
        # ---- NEW: Temp-Patch single‐param messages (H=0x03, L=00/10/12/14/16) ----
        elif addr_h == 0x03 and addr_l in [0x00, 0x10, 0x12, 0x14, 0x16]:
            logging.debug(f"Parsing Temp-Patch msg H={addr_h:02X}, patch={addr_m:02X}, L={addr_l:02X}, payload={payload}")
            # payload layout: [param_id, msb, lsb, …]
            if len(payload) >= 3:
                param_id, msb, lsb = payload[0], payload[1], payload[2]
                # reconstruct 14-bit value
                value = (msb << 7) | lsb
 
                # choose group name
                if addr_l == 0x00:
                    group = "TempCommon"
                else:
                    tone_num = (addr_l - 0x10) // 2 + 1
                    group = f"TempTone{tone_num}"
 
                param = ParsedParameter(
                    group_name=group,
                    parameter_name=f"param_{param_id}",
                    value=value,
                    address=address.copy(),
                    raw_message=list(sysex_msg)
                )
                return [param]
            return []
         # -----------------------------------------------------------------------
 
        # unknown block
        logging.debug(f"Unknown block type: {addr_h:02X} {addr_m:02X} {addr_l:02X}")
        return []
    
    def _parse_common_block(self, payload: bytes, address: List[int], raw_message: bytes) -> List[ParsedParameter]:
        """
        Parse a 'Common' block payload (must be ≥ 72 bytes).
        Uses known offsets for each Common parameter.
        """
        parameters: List[ParsedParameter] = []

        if len(payload) < 72:
            logging.warning(f"Common block payload too short: {len(payload)} bytes")
            return parameters

        # Complete mapping of offsets → (length, data_type) for Common block
        common_params = {
            # 0–11: Patch Name (12 bytes ASCII, padded with 0x00 or spaces)
            "patch_name":          (0,  12, "string"),

            # 12: Category (0–31)
            "category":            (12, 1,  "int"),
            # 13: Bank (0–1 for Preset A/B, etc.)
            "bank":                (13, 1,  "int"),
            # 14: Patch Number (0–127)
            "patch_number":        (14, 1,  "int"),
            # 15: PCM Bank Select (0–63)
            "pcm_bank":            (15, 1,  "int"),

            # 16 is reserved/padding (always 0x00)

            # 17: Chorus Send Level (0–127)
            "chorus_send":         (17, 1,  "int"),
            # 18: Reverb Send Level (0–127)
            "reverb_send":         (18, 1,  "int"),
            # 19: Output Level (0–127)
            "output_level":        (19, 1,  "int"),

            # 20–23: LFO 1 Rate, Delay, PMD, AMD (each 0–99)
            "lfo1_rate":           (20, 1,  "int"),
            "lfo1_delay":          (21, 1,  "int"),
            "lfo1_pmd":            (22, 1,  "int"),
            "lfo1_amd":            (23, 1,  "int"),

            # 24–28: LFO 2 Rate, Delay, Dest (bit flags), PMD, AMD
            #   LFO2 Dest is a bitmask: bit0 = pitch, bit1 = filter, bit2 = amp (0–7)
            "lfo2_rate":           (24, 1,  "int"),
            "lfo2_delay":          (25, 1,  "int"),
            "lfo2_dest":           (26, 1,  "int"),
            "lfo2_pmd":            (27, 1,  "int"),
            "lfo2_amd":            (28, 1,  "int"),

            # 29: Portamento Switch (0 = off, 1 = on)
            "portamento_switch":   (29, 1,  "int"),
            # 30: Portamento Time (0–99)
            "portamento_time":     (30, 1,  "int"),

            # 31: Pitch Bend Range (0–24 semitones)
            "pb_range":            (31, 1,  "int"),
            # 32: Fine Tune (signed 0–99, center=64)
            "fine_tune":           (32, 1,  "int"),
            # 33: Transpose (0–127, center=64)
            "transpose":           (33, 1,  "int"),

            # 34–37: Pitch EG Rate 1–4 (each 0–99)
            "pitch_eg_rate":       (34, 4,  "array"),  # offsets 34,35,36,37

            # 38–41: Pitch EG Level 1–4 (each 0–99)
            "pitch_eg_level":      (38, 4,  "array"),  # offsets 38,39,40,41

            # 42–45: Filter EG Rate 1–4 (each 0–99)
            "filter_eg_rate":      (42, 4,  "array"),  # offsets 42,43,44,45

            # 46–49: Filter EG Level 1–4 (each 0–99)
            "filter_eg_level":     (46, 4,  "array"),  # offsets 46,47,48,49

            # 50–53: Amp EG Rate 1–4 (each 0–99)
            "amp_eg_rate":         (50, 4,  "array"),  # offsets 50,51,52,53

            # 54–57: Amp EG Level 1–4 (each 0–99)
            "amp_eg_level":        (54, 4,  "array"),  # offsets 54,55,56,57

            # 58: Filter Cutoff (0–127)
            "filter_cutoff":       (58, 1,  "int"),
            # 59: Filter Resonance (0–127)
            "filter_resonance":    (59, 1,  "int"),

            # 60: Filter EG Attack Velocity (0–127)
            "filter_eg_attack_vel":  (60, 1, "int"),
            # 61: Filter EG Release Velocity (0–127)
            "filter_eg_release_vel": (61, 1, "int"),

            # 62: Velocity → Amp Depth (0–127)
            "velocity_to_amp_depth": (62, 1, "int"),

            # 63–64: Key Range Low / High (0–127 each)
            "key_range_low":       (63, 1,  "int"),
            "key_range_high":      (64, 1,  "int"),

            # 65–66: Velocity Range Low / High (0–127 each)
            "vel_range_low":       (65, 1,  "int"),
            "vel_range_high":      (66, 1,  "int"),

            # 67: Aftertouch Depth (0–127)
            "aftertouch_depth":    (67, 1,  "int"),

            # 68: Key Transpose (0–127, center=64)
            "key_transpose":       (68, 1,  "int"),            # 69: Portamento Curve (0-127 chooses curve shape)
            "portamento_curve":    (69, 1,  "int"),

            # 70–73 are reserved/padding and typically always 0x00
        }

        # Extract each defined parameter from payload
        for param_name, (offset, length, data_type) in common_params.items():
            if offset + length <= len(payload):
                if data_type == "string":
                    raw_bytes = payload[offset : offset + length]
                   # strip both NULs and spaces; assume 12-byte fixed name field
                    value = raw_bytes.decode("ascii", errors="ignore").strip("\x00 ")
                elif data_type == "array":
                    value = list(payload[offset : offset + length])
                else:  # data_type == "int"
                    value = int(payload[offset])

                # Get interpreted value
                interpreted_value, value_range = self._interpret_parameter_value("Common", param_name, value)

                param = ParsedParameter(
                    group_name="Common",
                    parameter_name=param_name,
                    value=value,
                    address=address.copy(),
                    raw_message=list(raw_message),
                    interpreted_value=interpreted_value,
                    value_range=value_range,
                    manufacturer=raw_message[1],
                    device_id=raw_message[2],
                    model_id=raw_message[3],
                    command=raw_message[4]
                )
                parameters.append(param)

        return parameters

    def _parse_tone_block(self, payload: bytes, address: List[int], raw_message: bytes) -> List[ParsedParameter]:
        """
        Parse a 'Tone' block payload (must be ≥ 58 bytes).
        Uses known offsets for each Tone parameter.
        """
        parameters: List[ParsedParameter] = []

        if len(payload) < 58:
            logging.warning(f"Tone block payload too short: {len(payload)} bytes")
            return parameters

        # Complete mapping of offsets for Tone block
        tone_params = {
            "tone_switch":         (0,  1, "int"),
            "waveform_bank":       (1,  1, "int"),
            "waveform_number":     (2,  1, "int"),
            "coarse_tune":         (3,  1, "int"),
            "fine_tune":           (4,  1, "int"),
            "key_group":           (5,  1, "int"),
            "key_range_low":       (6,  1, "int"),
            "key_range_high":      (7,  1, "int"),
            "vel_range_low":       (8,  1, "int"),
            "vel_range_high":      (9,  1, "int"),
            "output_level":        (10, 1, "int"),
            "pan":                 (11, 1, "int"),
            "porta_switch":        (12, 1, "int"),
            "porta_time":          (13, 1, "int"),
            "pitch_eg_rate":       (14, 4, "array"),
            "pitch_eg_level":      (18, 4, "array"),
            "filter_eg_rate":      (22, 4, "array"),
            "filter_eg_level":     (26, 4, "array"),
            "amp_eg_rate":         (30, 4, "array"),
            "amp_eg_level":        (34, 4, "array"),
            "filter_cutoff":       (38, 1, "int"),
            "filter_resonance":    (39, 1, "int"),
            "filter_eg_attack_vel":(40, 1, "int"),
            "filter_eg_release_vel":(41,1, "int"),
            "lfo_pmd_depth":       (42, 1, "int"),
            "lfo_amd_depth":       (43, 1, "int"),
            "lfo_key_sync":        (44, 1, "int"),
            "key_to_level_depth":  (45, 1, "int"),
            "key_num_detune_depth":(46, 1, "int"),
            "key_follow":          (47, 1, "int"),
            "ams_depth":           (48, 1, "int"),
            "pms_depth":           (49, 1, "int"),
            "pitch_bend_range":    (50, 1, "int"),
            "aftertouch_depth":    (51, 1, "int"),
            "poly_mono_switch":    (52, 1, "int"),
            "unison_detune":       (53, 1, "int"),
            "unison_pan_spread":   (54, 1, "int"),
            "resonance_mod_depth": (55, 1, "int"),
        }

        for param_name, (offset, length, data_type) in tone_params.items():
            if offset + length <= len(payload):
                if data_type == "string":
                    raw_bytes = payload[offset : offset + length]
                    value = raw_bytes.decode("ascii", errors="ignore").rstrip("\x00")
                elif data_type == "array":
                    value = list(payload[offset : offset + length])
                else:
                    value = int(payload[offset])

                # Get interpreted value  
                interpreted_value, value_range = self._interpret_parameter_value("Tone", param_name, value)

                param = ParsedParameter(
                    group_name="Tone",
                    parameter_name=param_name,
                    value=value,
                    address=address.copy(),
                    raw_message=list(raw_message),
                    interpreted_value=interpreted_value,
                    value_range=value_range,
                    manufacturer=raw_message[1],
                    device_id=raw_message[2],
                    model_id=raw_message[3],
                    command=raw_message[4]
                )
                parameters.append(param)

        return parameters

    def group_parameters_into_patches(self, all_params: List[ParsedParameter]) -> List[ParsedPreset]:
        """Group parameters by patch and extract MSB/LSB/PC for expansion support."""
        patches = {}
        msb_dict = {}
        lsb_dict = {}
        pc_dict = {}
        for param in all_params:
            patch_key = param.address[1]
            if patch_key not in patches:
                patch_name = "Unknown"
                if param.group_name == "Common" and param.parameter_name == "patch_name":
                    patch_name = str(param.value) if not isinstance(param.value, str) else param.value
                patches[patch_key] = ParsedPreset(
                    name=str(patch_name),
                    preset_type="JV-1080 Patch",
                    parameters=[]
                )
            patches[patch_key].parameters.append(param)
            # Update patch metadata if we find specific parameters
            if param.group_name == "Common":
                if param.parameter_name == "patch_name":
                    patches[patch_key].name = str(param.value) if not isinstance(param.value, str) else param.value
                elif param.parameter_name == "category":
                    patches[patch_key].category = param.interpreted_value
                elif param.parameter_name == "bank":
                    patches[patch_key].bank = param.interpreted_value
                elif param.parameter_name == "patch_number":
                    patches[patch_key].patch_number = param.value
                # Extract MSB/LSB/PC for expansion support if present
                elif param.parameter_name == "bank":
                    msb_dict[patch_key] = 87 if param.value == 4 else 80  # Example: User=87, Preset=80 (adjust as needed)
                elif param.parameter_name == "patch_number":
                    pc_dict[patch_key] = param.value
            # Optionally, extract from other param fields if needed
        # Assign MSB/LSB/PC to each patch
        for patch_key, preset in patches.items():
            # For JV-1080, MSB/LSB/PC logic may depend on bank/category/expansion
            # Here is a basic example, adjust as needed for your expansion logic:
            bank_val = None
            pc_val = None
            for p in preset.parameters:
                if p.group_name == "Common" and p.parameter_name == "bank":
                    bank_val = p.value
                if p.group_name == "Common" and p.parameter_name == "patch_number":
                    pc_val = p.value
            # Default MSB/LSB/PC logic for JV-1080:
            if bank_val is not None and pc_val is not None:
                if bank_val == 0:  # Preset A
                    preset.msb, preset.lsb, preset.pc = 80, 0, pc_val
                elif bank_val == 1:  # Preset B
                    preset.msb, preset.lsb, preset.pc = 80, 1, pc_val
                elif bank_val == 2:  # Preset C
                    preset.msb, preset.lsb, preset.pc = 80, 2, pc_val
                elif bank_val == 3:  # Preset D
                    preset.msb, preset.lsb, preset.pc = 80, 3, pc_val
                elif bank_val == 4:  # User
                    preset.msb, preset.lsb, preset.pc = 87, 0, pc_val
                elif bank_val == 5:  # Card
                    preset.msb, preset.lsb, preset.pc = 86, 0, pc_val
                elif 32 <= bank_val <= 50:  # Expansion boards (SR-JV80-01..)
                    # Roland expansion: MSB=89, LSB=bank_val-32, PC=patch_number
                    preset.msb, preset.lsb, preset.pc = 89, bank_val-32, pc_val
                else:
                    preset.msb, preset.lsb, preset.pc = None, None, pc_val
            else:
                preset.msb, preset.lsb, preset.pc = None, None, pc_val
        return list(patches.values())
    
    def export_presets_to_yaml(self, presets: List[ParsedPreset], output_file: str):
        preset_data = []
        for preset in presets:
            is_exp = False
            exp_name = None
            patch_group = None
            card_num = None
            card_val = None
            card_field = None
            patch_number_within_card = preset.patch_number
            # Only use expansion logic if msb == 89
            if preset.msb == 89:
                for param in preset.parameters:
                    if param.group_name == "Common" and param.parameter_name == "category":
                        if isinstance(param.value, int) and 32 <= param.value <= 50:
                            card_val = param.value
                            card_num = card_val - 31
                            exp_name = f"SR-JV80-{card_num:02d}"
                            is_exp = True
                if is_exp and preset.lsb is not None:
                    patch_group = preset.lsb
                    card_field = exp_name
                    bank_out = f"{exp_name} (LSB={patch_group}, MSB=89)"
                    patch_number_within_card = (patch_group * 128) + (preset.pc + 1 if preset.pc is not None else 1)
                    category_out = None  # Don't show category for expansions
                else:
                    bank_out = preset.bank
                    card_field = None
                    category_out = preset.category
            else:
                bank_out = preset.bank
                card_field = None
                category_out = preset.category
            preset_dict = {
                'name': preset.name,
                'preset_type': preset.preset_type,
                'bank': bank_out,
                'patch_number': patch_number_within_card,
                'midi_address': {
                    'msb': preset.msb,
                    'lsb': preset.lsb,
                    'pc': preset.pc
                },
                'parameters': {}
            }
            if card_field:
                preset_dict['card'] = card_field
            if category_out:
                preset_dict['category'] = category_out
            for param in preset.parameters:
                if param.group_name not in preset_dict['parameters']:
                    preset_dict['parameters'][param.group_name] = {}
                preset_dict['parameters'][param.group_name][param.parameter_name] = {
                    'value': param.value,
                    'interpreted': param.interpreted_value,
                    'range': param.value_range
                }
            preset_data.append(preset_dict)
        with open(output_file, 'w') as f:
            yaml.dump(
                preset_data,
                f,
                default_flow_style=False,
                indent=2,
                allow_unicode=True
            )
        logging.info(f"Exported {len(presets)} presets to {output_file}")

    def export_presets_to_json(self, presets: List[ParsedPreset], output_file: str):
        preset_data = []
        for preset in presets:
            is_exp = False
            exp_name = None
            patch_group = None
            card_num = None
            card_val = None
            card_field = None
            patch_number_within_card = preset.patch_number
            if preset.msb == 89:
                for param in preset.parameters:
                    if param.group_name == "Common" and param.parameter_name == "category":
                        if isinstance(param.value, int) and 32 <= param.value <= 50:
                            card_val = param.value
                            card_num = card_val - 31
                            exp_name = f"SR-JV80-{card_num:02d}"
                            is_exp = True
                if is_exp and preset.lsb is not None:
                    patch_group = preset.lsb
                    card_field = exp_name
                    bank_out = f"{exp_name} (LSB={patch_group}, MSB=89)"
                    patch_number_within_card = (patch_group * 128) + (preset.pc + 1 if preset.pc is not None else 1)
                    category_out = None
                else:
                    bank_out = preset.bank
                    card_field = None
                    category_out = preset.category
            else:
                bank_out = preset.bank
                card_field = None
                category_out = preset.category
            preset_dict = {
                'name': preset.name,
                'preset_type': preset.preset_type,
                'bank': bank_out,
                'patch_number': patch_number_within_card,
                'midi_address': {
                    'msb': preset.msb,
                    'lsb': preset.lsb,
                    'pc': preset.pc
                },
                'parameters': {}
            }
            if card_field:
                preset_dict['card'] = card_field
            if category_out:
                preset_dict['category'] = category_out
            for param in preset.parameters:
                if param.group_name not in preset_dict['parameters']:
                    preset_dict['parameters'][param.group_name] = {}
                preset_dict['parameters'][param.group_name][param.parameter_name] = {
                    'value': param.value,
                    'interpreted': param.interpreted_value,
                    'range': param.value_range
                }
            preset_data.append(preset_dict)
        with open(output_file, 'w') as f:
            json.dump(preset_data, f, indent=2)
        logging.info(f"Exported {len(presets)} presets to {output_file}")

    def export_tone_parameters_yaml(self, tone_params: List[ParsedParameter], output_file: str):
        """Export a single Tone's parameters as a flat YAML mapping (no group nesting)."""
        flat = {}
        for param in tone_params:
            # Only output the raw value, not interpreted/range
            flat[param.parameter_name] = param.value
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(flat, f, default_flow_style=False, indent=2, allow_unicode=True)
        logging.info(f"Exported flat Tone parameters to {output_file}")

    def export_common_parameters_yaml(self, common_params: List[ParsedParameter], output_file: str):
        """Export a single Common block's parameters as a flat YAML mapping (no group nesting), including reserved_pad1 (offset 14, always 0x00)."""
        flat = {}
        for param in common_params:
            flat[param.parameter_name] = param.value
        # Insert reserved_pad1 (byte 14, always 0x00) if not present
        if 'reserved_pad1' not in flat:
            flat['reserved_pad1'] = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(flat, f, default_flow_style=False, indent=2, allow_unicode=True)
        logging.info(f"Exported flat Common parameters to {output_file}")

    def analyze_presets(self, presets: List[ParsedPreset]) -> AnalysisResult:
        """Perform comprehensive analysis of the presets."""
        # Collect statistics
        parameter_stats = defaultdict(lambda: defaultdict(list))
        category_distribution = Counter()
        common_param_values = defaultdict(list)
        tone_usage = defaultdict(int)
        
        for preset in presets:
            if preset.category:
                category_distribution[preset.category] += 1
                
            for param in preset.parameters:
                # Collect parameter statistics
                if isinstance(param.value, (int, float)):
                    parameter_stats[param.group_name][param.parameter_name].append(param.value)
                
                # Track common parameter values
                common_param_values[f"{param.group_name}.{param.parameter_name}"].append(param.value)
                
                # Track tone usage patterns
                if param.group_name.startswith("Tone") and param.parameter_name == "tone_switch":
                    if param.value == 1:  # Tone is enabled
                        tone_usage[param.group_name] += 1
        
        # Calculate statistics for numeric parameters
        stats_summary = {}
        for group_name, params in parameter_stats.items():
            stats_summary[group_name] = {}
            for param_name, values in params.items():
                if values:
                    stats_summary[group_name][param_name] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'mean': round(statistics.mean(values), 2),
                        'median': statistics.median(values),
                        'mode': statistics.mode(values) if len(set(values)) < len(values) else None
                    }
        
        # Calculate tone usage patterns
        total_presets = len(presets)
        tone_patterns = {
            'total_presets': total_presets,
            'tone_usage_percentage': {
                tone: round((count / total_presets) * 100, 1) 
                for tone, count in tone_usage.items()
            },
            'average_tones_per_preset': round(sum(tone_usage.values()) / total_presets, 2) if total_presets > 0 else 0
        }
        
        return AnalysisResult(
            total_presets=total_presets,
            parameter_statistics=stats_summary,
            category_distribution=dict(category_distribution),
            common_parameter_values=dict(common_param_values),
            tone_usage_patterns=tone_patterns
        )

    def export_analysis_report(self, analysis: AnalysisResult, output_file: str):
        """Export analysis report to file."""
        report_data = asdict(analysis)
        
        if output_file.endswith('.json'):
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2)
        else:  # Default to YAML
            with open(output_file, 'w') as f:
                yaml.dump(report_data, f, default_flow_style=False, indent=2)
        
        logging.info(f"Exported analysis report to {output_file}")

    def compare_presets(self, preset1: ParsedPreset, preset2: ParsedPreset) -> Dict[str, Any]:
        """Compare two presets and return differences."""
        differences = {
            'preset1_name': preset1.name,
            'preset2_name': preset2.name,
            'different_parameters': {},
            'common_parameters': {},
            'preset1_only': {},
            'preset2_only': {}
        }
        
        # Create parameter lookup dictionaries
        params1 = {f"{p.group_name}.{p.parameter_name}": p for p in preset1.parameters}
        params2 = {f"{p.group_name}.{p.parameter_name}": p for p in preset2.parameters}
        
        all_param_keys = set(params1.keys()) | set(params2.keys())
        
        for key in all_param_keys:
            if key in params1 and key in params2:
                param1, param2 = params1[key], params2[key]
                if param1.value != param2.value:
                    differences['different_parameters'][key] = {
                        'preset1': {'value': param1.value, 'interpreted': param1.interpreted_value},
                        'preset2': {'value': param2.value, 'interpreted': param2.interpreted_value}
                    }
                else:
                    differences['common_parameters'][key] = {
                        'value': param1.value,
                        'interpreted': param1.interpreted_value
                    }
            elif key in params1:
                param1 = params1[key]
                differences['preset1_only'][key] = {
                    'value': param1.value,
                    'interpreted': param1.interpreted_value
                }
            else:
                param2 = params2[key]
                differences['preset2_only'][key] = {
                    'value': param2.value,
                    'interpreted': param2.interpreted_value
                }
        
        return differences

    def export_presets_to_folder(self, presets: List[ParsedPreset], output_folder: str, format: str = 'yaml'):
        """Export each parsed preset as a separate YAML or JSON file in a folder, including MSB/LSB/PC fields. For expansion cards, set bank/category from Common block bank/category and LSB patch group."""
        output_folder = sanitize_filename(output_folder)
        os.makedirs(output_folder, exist_ok=True)
        for idx, preset in enumerate(presets):
            is_exp = False
            exp_name = None
            patch_group = None
            card_num = None
            card_val = None
            if preset.msb == 89:
                for param in preset.parameters:
                    if param.group_name == "Common" and param.parameter_name == "category":
                        if isinstance(param.value, int) and 32 <= param.value <= 50:
                            card_val = param.value
                            card_num = card_val - 31
                            exp_name = f"SR-JV80-{card_num:02d}"
                            is_exp = True
                if is_exp and preset.lsb is not None:
                    patch_group = preset.lsb
                    bank_out = f"{exp_name} (LSB={patch_group}, MSB=89)"
                    patch_number_within_card = (patch_group * 128) + (preset.pc + 1 if preset.pc is not None else 1)
                    category_out = None
                else:
                    bank_out = preset.bank
                    category_out = preset.category
                    patch_number_within_card = preset.patch_number
            else:
                bank_out = preset.bank
                category_out = preset.category
                patch_number_within_card = preset.patch_number
            flat = {}
            sysex_messages = []
            for param in preset.parameters:
                flat[param.parameter_name] = param.value
                if param.raw_message and param.raw_message not in sysex_messages:
                    sysex_messages.append(param.raw_message)
            out_data = {
                'name': preset.name,
                'category': category_out,
                'bank': bank_out,
                'patch_number': patch_number_within_card,
                'msb': preset.msb,
                'lsb': preset.lsb,
                'pc': preset.pc,
                'parameters': flat,
                'sysex_messages': sysex_messages
            }
            safe_name = sanitize_filename(preset.name)
            file_name = f"{idx:03d}_{safe_name}.{format}"
            out_path = os.path.join(output_folder, file_name)
            with open(out_path, 'w', encoding='utf-8') as f:
                if format == 'json':
                    json.dump(out_data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(out_data, f, default_flow_style=False, indent=2, allow_unicode=True)
        logging.info(f"Exported {len(presets)} presets to folder {output_folder}")

def main():
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    parser = argparse.ArgumentParser(description="Parse JV-1080 .syx files with advanced analysis")
    parser.add_argument("input_file", nargs='?', default="sysex/OrchII-2.syx",
                       help="Path to .syx file (default: sysex/OrchII-2.syx)")
    parser.add_argument("-o", "--output", default="presets.yaml", 
                       help="Output file (YAML or JSON based on extension)")
    parser.add_argument("-a", "--analyze", action="store_true", 
                       help="Generate analysis report")
    parser.add_argument("--analysis-output", default="analysis.yaml",
                       help="Analysis report output file")
    parser.add_argument("--compare", nargs=2, metavar=("PRESET1", "PRESET2"),
                       help="Compare two presets by name")
    parser.add_argument("--list-presets", action="store_true",
                       help="List all preset names")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Enable debug logging")
    parser.add_argument("--format", choices=["yaml", "json"], 
                       help="Force output format (overrides file extension)")
    parser.add_argument("--export-flat-common", nargs=2, metavar=("PATCH_INDEX", "OUTPUT_YAML"),
                       help="Export flat YAML for Common block of patch index (0-127)")
    parser.add_argument("--export-flat-tone", nargs=3, metavar=("PATCH_INDEX", "TONE_NUM", "OUTPUT_YAML"),
                       help="Export flat YAML for Tone block (1-4) of patch index (0-127)")
    parser.add_argument("--export-folder", nargs=2, metavar=("PATCH_INDEX", "OUTPUT_FOLDER"),
                       help="Export each preset as separate YAML/JSON files in folder")
    parser.add_argument("--export-all-folder", metavar="OUTPUT_FOLDER", help="Export all presets as separate YAML/JSON files in folder")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    sys_parser = SysExParser()
    all_params: List[ParsedParameter] = sys_parser.parse_sysex_file(args.input_file)
    presets: List[ParsedPreset] = sys_parser.group_parameters_into_patches(all_params)
    print(f"✓ Parsed {len(all_params)} parameters from {len(presets)} presets")

    # Flat Common export
    if args.export_flat_common:
        patch_idx = int(args.export_flat_common[0])
        out_yaml = args.export_flat_common[1]
        if 0 <= patch_idx < len(presets):
            common_params = [p for p in presets[patch_idx].parameters if p.group_name == "Common"]
            sys_parser.export_common_parameters_yaml(common_params, out_yaml)
            print(f"✓ Exported flat Common YAML for patch {patch_idx} to {out_yaml}")
        else:
            print(f"Patch index {patch_idx} out of range.")
        return

    # Flat Tone export
    if args.export_flat_tone:
        patch_idx = int(args.export_flat_tone[0])
        tone_num = int(args.export_flat_tone[1])
        out_yaml = args.export_flat_tone[2]
        if 0 <= patch_idx < len(presets) and 1 <= tone_num <= 4:
            tone_params = [p for p in presets[patch_idx].parameters if p.group_name == f"Tone{tone_num}"]
            sys_parser.export_tone_parameters_yaml(tone_params, out_yaml)
            print(f"✓ Exported flat Tone{tone_num} YAML for patch {patch_idx} to {out_yaml}")
        else:
            print(f"Patch index or tone number out of range.")
        return

    # List presets if requested
    if args.list_presets:
        print("\nPreset List:")
        for i, preset in enumerate(presets):
            category = preset.category or "Unknown"
            bank = preset.bank or "Unknown"
            print(f"  {i:3d}: {preset.name:<20} [{category}, {bank}]")
        return
    
    # Compare presets if requested
    if args.compare:
        preset1_name, preset2_name = args.compare
        preset1 = next((p for p in presets if p.name == preset1_name), None)
        preset2 = next((p for p in presets if p.name == preset2_name), None)
        
        if not preset1:
            print(f"Error: Preset '{preset1_name}' not found")
            return
        if not preset2:
            print(f"Error: Preset '{preset2_name}' not found")
            return
            
        comparison = sys_parser.compare_presets(preset1, preset2)
        
        print(f"\nPreset Comparison: '{preset1_name}' vs '{preset2_name}'")
        print(f"Different parameters: {len(comparison['different_parameters'])}")
        print(f"Common parameters: {len(comparison['common_parameters'])}")
        print(f"Only in {preset1_name}: {len(comparison['preset1_only'])}")
        print(f"Only in {preset2_name}: {len(comparison['preset2_only'])}")
        
        # Show some differences
        if comparison['different_parameters']:
            print("\nKey Differences:")
            for i, (param, diff) in enumerate(list(comparison['different_parameters'].items())[:10]):
                print(f"  {param}:")
                print(f"    {preset1_name}: {diff['preset1']['interpreted']}")
                print(f"    {preset2_name}: {diff['preset2']['interpreted']}")
            if len(comparison['different_parameters']) > 10:
                print(f"  ... and {len(comparison['different_parameters']) - 10} more")
        
        return
    
    # Export presets
    output_format = args.format or ("json" if args.output.endswith('.json') else "yaml")
    
    if output_format == "json":
        sys_parser.export_presets_to_json(presets, args.output)
    else:
        sys_parser.export_presets_to_yaml(presets, args.output)
    
    print(f"✓ Exported to {args.output}")
    
    # Generate analysis if requested
    if args.analyze:
        analysis = sys_parser.analyze_presets(presets)
        sys_parser.export_analysis_report(analysis, args.analysis_output)
        
        print(f"\nAnalysis Summary:")
        print(f"  Total presets: {analysis.total_presets}")
        print(f"  Categories: {len(analysis.category_distribution)}")
        print(f"  Average tones per preset: {analysis.tone_usage_patterns['average_tones_per_preset']}")
        
        if analysis.category_distribution:
            print(f"\nTop Categories:")
            sorted_categories = sorted(analysis.category_distribution.items(), 
                                     key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories[:5]:
                print(f"    {category}: {count} presets")
        
        print(f"✓ Analysis report saved to {args.analysis_output}")
    
    # Export each preset to separate files if requested
    if args.export_folder:
        try:
            patch_idx = int(args.export_folder[0])
        except ValueError:
            print(f"First argument to --export-folder must be a patch index (integer), got: {args.export_folder[0]}")
            return
        output_folder = sanitize_filename(args.export_folder[1])
        if 0 <= patch_idx < len(presets):
            sys_parser.export_presets_to_folder([presets[patch_idx]], output_folder, output_format)
            print(f"✓ Exported patch {patch_idx} to folder {output_folder}")
        else:
            print(f"Patch index {patch_idx} out of range.")
        return

    # Export each preset to separate files if requested
    if args.export_all_folder:
        output_folder = sanitize_filename(args.export_all_folder)
        sys_parser.export_presets_to_folder(presets, output_folder, output_format)
        print(f"✓ Exported all presets to folder {output_folder}")
        return

    # If neither export_all_folder nor export_folder is specified, default to sanitized .syx filename for folder export (if user wants per-preset export)
    # (This logic can be extended as needed)
    # e.g. if args.export_folder is not None and len(args.export_folder) == 2:
    #         output_folder = sanitize_filename(args.export_folder[1])
    #         sys_parser.export_presets_to_folder(presets, output_folder, output_format)
    #         print(f"✓ Exported all presets to folder {output_folder}")
    #     return

if __name__ == "__main__":
    main()
