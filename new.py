#!/usr/bin/env python3
"""
JV-1080 SysEx Parser Module

Parses Roland JV-1080 SysEx files (bulk dumps of 128 patches) and exports
each patch (Common + Tone 1–4) to YAML/JSON. Implements complete
Common block (offsets 0–71) and Tone blocks (offsets 0–57) with value
extraction.
"""

import os
import sys
import logging
import argparse
from typing import List, Union, Optional, Dict
from dataclasses import dataclass
import yaml
import json

# -----------------------------------------------
# Data Classes
# -----------------------------------------------

@dataclass
class ParsedParameter:
    """
    Represents a single parameter, extracted from one SysEx message.
    """
    group_name: str              # "Common", "Tone1", "Tone2", "Tone3", or "Tone4"
    parameter_name: str          # e.g. "filter_cutoff", "wave_number", etc.
    value: Union[int, List[int], str]
    address: List[int]           # [addr_high, addr_mid, addr_low]
    raw_message: List[int]       # the full bytes of that one SysEx message
    patch_index: int = -1        # Will be set later, in 0..127


@dataclass
class ParsedPreset:
    """
    Represents a complete patch (= Common block + up to 4 Tone blocks).
    """
    name: str
    preset_type: str             # e.g. "patch"
    parameters: List[ParsedParameter]
    source_file: Optional[str] = None


# -----------------------------------------------
# JV-1080 SysEx Parser Class
# -----------------------------------------------

class JV1080SysExParser:
    """
    Parses a JV-1080 bulk‐dump .syx file (128 patches). Each patch consists of
    5 SysEx messages:
      - Common block (addrHigh=0x10, addrMid=0x00, addrLow = 0x00..0x7F)
      - Tone1 block (addrHigh=0x10, addrMid=0x10..0x8F)
      - Tone2 block (addrHigh=0x10, addrMid=0x20..0x9F)
      - Tone3 block (addrHigh=0x10, addrMid=0x30..0xAF)
      - Tone4 block (addrHigh=0x10, addrMid=0x40..0xBF)

    This parser:
      1) Splits the raw .syx data into individual SysEx messages (F0 → F7).
      2) Parses each message’s header and payload, extracting every parameter.
      3) Bins each ParsedParameter by (patch_index, block_type).
      4) Recombines them into 128 ParsedPreset objects (Common + Tone1–4).
      5) Exports all presets to YAML or JSON.
    """

    def __init__(self):
        pass

    def parse_sysex_file(self, filepath: str) -> List[ParsedParameter]:
        """
        Reads a .syx file, breaks it into SysEx messages, and parses each message
        into a flat list of ParsedParameter objects.
        """
        all_parameters: List[ParsedParameter] = []
        try:
            with open(filepath, "rb") as f:
                data = f.read()

            # Step 1: Extract every SysEx message (bytes from 0xF0 ... 0xF7)
            sysex_messages = self._extract_sysex_messages(data)

            # Step 2: Parse each SysEx message into parameters
            msg_count = 0
            for msg in sysex_messages:
                msg_count += 1
                params = self._parse_sysex_message(msg)
                all_parameters.extend(params)

            logging.info(f"Parsed {msg_count} SysEx messages → {len(all_parameters)} parameters")
        except FileNotFoundError:
            logging.error(f"File not found: {filepath}")
        except Exception as e:
            logging.error(f"Error parsing {filepath}: {e}")

        return all_parameters

    def _extract_sysex_messages(self, data: bytes) -> List[bytes]:
        """
        Splits the raw .syx data into complete SysEx messages (each starting
        with 0xF0 and ending with 0xF7). Returns a list of byte‐strings.
        """
        messages: List[bytes] = []
        idx = 0
        while True:
            try:
                start = data.index(0xF0, idx)
                end = data.index(0xF7, start + 1)
                msg = data[start : end + 1]
                messages.append(msg)
                idx = end + 1
            except ValueError:
                break
        return messages

    def _parse_sysex_message(self, sysex_msg: bytes) -> List[ParsedParameter]:
        """
        Parses a single SysEx message (bytes). Returns zero or more ParsedParameter objects.
        Only processes if the header is:
            F0 41 10 6A 12  <addrHigh> <addrMid> <addrLow>  <...payload...>  F7
        """
        parsed_params: List[ParsedParameter] = []

        # Must be at least 8 bytes: [F0, 41, 10, 6A, 12, addrHigh, addrMid, addrLow, payload..., F7]
        if len(sysex_msg) < 8:
            return []

        # Verify the first five bytes = JV-1080 header
        if not (sysex_msg[0] == 0xF0 and sysex_msg[1] == 0x41 and sysex_msg[2] == 0x10
                and sysex_msg[3] == 0x6A and sysex_msg[4] == 0x12):
            return []

        # Next three bytes are addrHigh, addrMid, addrLow
        addr_high = sysex_msg[5]
        addr_mid  = sysex_msg[6]
        addr_low  = sysex_msg[7]
        address = [addr_high, addr_mid, addr_low]

        # The payload is everything from byte‐index 8 up to but not including the final 0xF7
        payload = sysex_msg[8 : -1]

        # Now delegate to block‐type parsing
        parsed_params = self._parse_jv1080_payload(address, payload, sysex_msg)
        return parsed_params

    def _parse_jv1080_payload(self,
                              address: List[int],
                              payload: bytes,
                              raw_message: bytes) -> List[ParsedParameter]:
        """
        Given (addressHigh, addressMid, addressLow), determine block type (Common vs Tone1–4)
        and the patch index (0..127). Then call the appropriate block‐parser.
        Returns a list of ParsedParameter for that payload.
        """
        parameters: List[ParsedParameter] = []
        addr_high, addr_mid, addr_low = address

        block_type: Optional[str] = None
        patch_index: Optional[int] = None

        # ------ Determine block type & patch index ------
        # 1) Common block: addrMid in 0x00..0x7F  → patchIndex = addrMid
        if 0x00 <= addr_mid <= 0x7F and addr_high == 0x10:
            block_type = "Common"
            patch_index = addr_mid

        # 2) Tone1 block: addrMid in 0x10..0x8F  → patchIndex = addrMid - 0x10
        elif 0x10 <= addr_mid <= 0x8F and addr_high == 0x10:
            block_type = "Tone1"
            patch_index = addr_mid - 0x10

        # 3) Tone2 block: addrMid in 0x20..0x9F  → patchIndex = addrMid - 0x20
        elif 0x20 <= addr_mid <= 0x9F and addr_high == 0x10:
            block_type = "Tone2"
            patch_index = addr_mid - 0x20

        # 4) Tone3 block: addrMid in 0x30..0xAF  → patchIndex = addrMid - 0x30
        elif 0x30 <= addr_mid <= 0xAF and addr_high == 0x10:
            block_type = "Tone3"
            patch_index = addr_mid - 0x30

        # 5) Tone4 block: addrMid in 0x40..0xBF  → patchIndex = addrMid - 0x40
        elif 0x40 <= addr_mid <= 0xBF and addr_high == 0x10:
            block_type = "Tone4"
            patch_index = addr_mid - 0x40

        else:
            # Not one of the recognized patch data blocks
            return []

        # ------ Parse payload by block type ------
        if block_type == "Common":
            parameters.extend(self._parse_common_block(payload, address, raw_message))
        else:
            # Tone1..Tone4 all share the same structure except the group name
            tone_num = int(block_type[-1])  # e.g. "Tone3" → 3
            parameters.extend(self._parse_tone_block(payload, address, raw_message, tone_num))

        # Attach the computed patch_index to each ParsedParameter
        for p in parameters:
            p.patch_index = patch_index if patch_index is not None else -1

        return parameters

    def _parse_common_block(self,
                            payload: bytes,
                            address: List[int],
                            raw_message: bytes) -> List[ParsedParameter]:
        """
        Parses a Common block payload (minimum length 72 bytes).
        Returns one ParsedParameter per defined Common parameter.
        """
        parameters: List[ParsedParameter] = []

        # If the payload is shorter than 72 bytes, it's invalid for Common
        if len(payload) < 72:
            return parameters

        # Complete dictionary of offset→(length, data_type) for Common
        common_params: Dict[str, tuple] = {
            # 0– 9: Patch Name (10 bytes ASCII, padded with 0x00)
            "patch_name":           (0,  10, "string"),

            # 10: Category (0–31)
            "category":             (10, 1,  "int"),
            # 11: Bank (0–1 for Preset A/B)
            "bank":                 (11, 1,  "int"),
            # 12: Patch Number (0–127)
            "patch_number":         (12, 1,  "int"),
            # 13: PCM Bank Select (0–63)
            "pcm_bank":             (13, 1,  "int"),

            # 14: reserved/padding (always 0x00)

            # 15: Chorus Send Level (0–127)
            "chorus_send":          (15, 1,  "int"),
            # 16: Reverb Send Level (0–127)
            "reverb_send":          (16, 1,  "int"),
            # 17: Output Level (0–127)
            "output_level":         (17, 1,  "int"),

            # 18–21: LFO 1 Rate, Delay, PMD, AMD (each 0–99)
            "lfo1_rate":            (18, 1,  "int"),
            "lfo1_delay":           (19, 1,  "int"),
            "lfo1_pmd":             (20, 1,  "int"),
            "lfo1_amd":             (21, 1,  "int"),

            # 22–26: LFO 2 Rate, Delay, Dest (bit‐flags), PMD, AMD
            #   LFO 2 Dest bits: bit0=pitch, bit1=filter, bit2=amp (0–7)
            "lfo2_rate":            (22, 1,  "int"),
            "lfo2_delay":           (23, 1,  "int"),
            "lfo2_dest":            (24, 1,  "int"),
            "lfo2_pmd":             (25, 1,  "int"),
            "lfo2_amd":             (26, 1,  "int"),

            # 27: Portamento Switch (0=off, 1=on)
            "portamento_switch":    (27, 1,  "int"),
            # 28: Portamento Time (0–99)
            "portamento_time":      (28, 1,  "int"),

            # 29: Pitch Bend Range (0–24 semitones)
            "pb_range":             (29, 1,  "int"),
            # 30: Fine Tune (signed 0–99, center=64)
            "fine_tune":            (30, 1,  "int"),
            # 31: Transpose (0–127, center=64)
            "transpose":            (31, 1,  "int"),

            # 32–35: Pitch EG Rate 1–4 (each 0–99)
            "pitch_eg_rate":        (32, 4,  "array"),  # offsets 32,33,34,35

            # 36–39: Pitch EG Level 1–4 (each 0–99)
            "pitch_eg_level":       (36, 4,  "array"),  # offsets 36,37,38,39

            # 40–43: Filter EG Rate 1–4 (each 0–99)
            "filter_eg_rate":       (40, 4,  "array"),  # offsets 40,41,42,43

            # 44–47: Filter EG Level 1–4 (each 0–99)
            "filter_eg_level":      (44, 4,  "array"),  # offsets 44,45,46,47

            # 48–51: Amp EG Rate 1–4 (each 0–99)
            "amp_eg_rate":          (48, 4,  "array"),  # offsets 48,49,50,51

            # 52–55: Amp EG Level 1–4 (each 0–99)
            "amp_eg_level":         (52, 4,  "array"),  # offsets 52,53,54,55

            # 56: Filter Cutoff (0–127)
            "filter_cutoff":        (56, 1,  "int"),
            # 57: Filter Resonance (0–127)
            "filter_resonance":     (57, 1,  "int"),

            # 58: Filter EG Attack Velocity (0–127)
            "filter_eg_attack_vel":  (58, 1, "int"),
            # 59: Filter EG Release Velocity (0–127)
            "filter_eg_release_vel": (59, 1, "int"),

            # 60: Velocity → Amp Depth (0–127)
            "velocity_to_amp_depth": (60, 1, "int"),

            # 61–62: Key Range Low / High (0–127 each)
            "key_range_low":        (61, 1,  "int"),
            "key_range_high":       (62, 1,  "int"),

            # 63–64: Velocity Range Low / High (0–127 each)
            "vel_range_low":        (63, 1,  "int"),
            "vel_range_high":       (64, 1,  "int"),

            # 65: Aftertouch Depth (0–127)
            "aftertouch_depth":     (65, 1,  "int"),

            # 66: Key Transpose (0–127, center=64)
            "key_transpose":        (66, 1,  "int"),

            # 67: Portamento Curve (0–127 → selects curve shape)
            "portamento_curve":     (67, 1,  "int"),

            # 68–71: Reserved/padding (usually all 0x00). If you need to read them:
            "reserved_68":          (68, 1,  "int"),
            "reserved_69":          (69, 1,  "int"),
            "reserved_70":          (70, 1,  "int"),
            "reserved_71":          (71, 1,  "int"),
        }

        # Extract every defined parameter
        for param_name, (offset, length, data_type) in common_params.items():
            if offset + length <= len(payload):
                if data_type == "string":
                    raw_bytes = payload[offset : offset + length]
                    value = raw_bytes.decode("ascii", errors="ignore").rstrip("\x00")
                elif data_type == "array":
                    value = list(payload[offset : offset + length])
                else:  # data_type == "int"
                    value = int(payload[offset])

                param = ParsedParameter(
                    group_name="Common",
                    parameter_name=param_name,
                    value=value,
                    address=address.copy(),
                    raw_message=list(raw_message),
                )
                parameters.append(param)

        return parameters

    def _parse_tone_block(self,
                          payload: bytes,
                          address: List[int],
                          raw_message: bytes,
                          tone_num: int) -> List[ParsedParameter]:
        """
        Parses a Tone block payload (minimum length 58 bytes).
        tone_num ∈ {1,2,3,4} identifies which Tone we are parsing.
        """
        parameters: List[ParsedParameter] = []

        # If payload is shorter than 58, it cannot be a valid Tone block
        if len(payload) < 58:
            return parameters

        # Offsets, lengths, and types for each Tone parameter
        tone_params: Dict[str, tuple] = {
            "on":                  (0,  1,  "int"),    # 0=off, 1=on
            "wave_bank":           (1,  1,  "int"),    # 0=A-PCM, 1=PCM
            "wave_number":         (2,  1,  "int"),    # 0–127 index within bank
            "coarse_tune":         (3,  1,  "int"),    # signed 0–99; 64=center
            "fine_tune":           (4,  1,  "int"),    # signed 0–99; 64=center
            "key_group":           (5,  1,  "int"),    # 0–3 groups A–D
            "key_range_low":       (6,  1,  "int"),    # 0–127
            "key_range_high":      (7,  1,  "int"),    # 0–127
            "vel_range_low":       (8,  1,  "int"),    # 0–127
            "vel_range_high":      (9,  1,  "int"),    # 0–127
            "output_level":        (10, 1,  "int"),    # 0–127
            "pan":                 (11, 1,  "int"),    # 0=Left, 64=Center, 127=Right
            "portamento_switch":   (12, 1,  "int"),    # 0=off, 1=on (per‐tone)
            "portamento_time":     (13, 1,  "int"),    # 0–99 (per‐tone)
            "pitch_eg_rate":       (14, 4,  "array"),  # offsets 14–17
            "pitch_eg_level":      (18, 4,  "array"),  # offsets 18–21
            "filter_eg_rate":      (22, 4,  "array"),  # offsets 22–25
            "filter_eg_level":     (26, 4,  "array"),  # offsets 26–29
            "amp_eg_rate":         (30, 4,  "array"),  # offsets 30–33
            "amp_eg_level":        (34, 4,  "array"),  # offsets 34–37
            "filter_cutoff":       (38, 1,  "int"),    # 0–127
            "filter_resonance":    (39, 1,  "int"),    # 0–127
            "filter_eg_attack_vel":(40, 1,  "int"),    # 0–127
            "filter_eg_release_vel":(41,1,  "int"),    # 0–127
            "lfo_pmd":             (42, 1,  "int"),    # 0–99
            "lfo_amd":             (43, 1,  "int"),    # 0–99
            "lfo_key_sync":        (44, 1,  "int"),    # 0=off, 1=on
            "key_to_level_depth":  (45, 1,  "int"),    # 0–127
            "key_detune_depth":    (46, 1,  "int"),    # 0–127
            "key_follow":          (47, 1,  "int"),    # 0–127
            "ams_depth":           (48, 1,  "int"),    # 0–99
            "pms_depth":           (49, 1,  "int"),    # 0–99
            "pb_range":            (50, 1,  "int"),    # 0–24 semitones
            "aftertouch_depth":    (51, 1,  "int"),    # 0–127
            "poly_mono":           (52, 1,  "int"),    # 0=Poly,1=Mono
            "unison_detune":       (53, 1,  "int"),    # 0–127
            "unison_spread":       (54, 1,  "int"),    # 0–127
            "resonance_mod_depth": (55, 1,  "int"),    # 0–127
            # Offsets 56–57 are reserved (often zero-padded)
        }

        for param_name, (offset, length, data_type) in tone_params.items():
            if offset + length <= len(payload):
                if data_type == "array":
                    value = list(payload[offset : offset + length])
                else:
                    # data_type == "int"
                    value = int(payload[offset])

                param = ParsedParameter(
                    group_name=f"Tone{tone_num}",
                    parameter_name=param_name,
                    value=value,
                    address=address.copy(),
                    raw_message=list(raw_message),
                )
                parameters.append(param)

        return parameters

    def group_parameters_into_patches(self,
                                      parameters: List[ParsedParameter]) -> List[ParsedPreset]:
        """
        Two‐pass grouping:

        1) Bucket every ParsedParameter by (patch_index, block_type).
        2) For each patch_index 0..127 that has at least one Common block,
           assemble Common + Tone1..Tone4 into a ParsedPreset.
        """
        # Create an empty bucket for 128 possible patches,
        # each with 5 sub‐lists (Common, Tone1, Tone2, Tone3, Tone4).
        buckets: Dict[int, Dict[str, List[ParsedParameter]]] = {
            i: {"Common": [], "Tone1": [], "Tone2": [], "Tone3": [], "Tone4": []}
            for i in range(128)
        }

        # Pass #1: populate buckets
        for p in parameters:
            idx = p.patch_index
            block = p.group_name  # "Common", "Tone1", "Tone2", "Tone3", or "Tone4"
            if idx is None or not (0 <= idx < 128):
                continue
            if block not in buckets[idx]:
                continue
            buckets[idx][block].append(p)

        # Pass #2: assemble full patches
        presets: List[ParsedPreset] = []
        for idx in range(128):
            common_list = buckets[idx]["Common"]
            if not common_list:
                # If there is no Common block for this patch index, skip it
                continue

            all_params: List[ParsedParameter] = []
            # Add the Common parameters first
            all_params.extend(common_list)
            # Then add Tone1–Tone4 (if any)
            for t in range(1, 5):
                block_name = f"Tone{t}"
                all_params.extend(buckets[idx][block_name])

            # Extract the patch name from Common (if present)
            patch_name = "Unknown"
            for cp in common_list:
                if cp.parameter_name == "patch_name" and isinstance(cp.value, str):
                    patch_name = cp.value
                    break

            preset = ParsedPreset(
                name=patch_name,
                preset_type="patch",
                parameters=sorted(all_params, key=lambda x: (x.group_name, x.parameter_name))
            )
            presets.append(preset)

        return presets

    def export_presets_to_yaml(self,
                               presets: List[ParsedPreset],
                               output_file: str):
        """
        Exports a list of ParsedPreset objects to a single YAML file. The output
        is a list of presets, each containing:
          - name: <patch_name>
          - type: "patch"
          - parameters: { "Common.patch_name": "...", "Common.category": 7, ... }
        """
        data_to_dump = []
        for preset in presets:
            entry = {
                "name": preset.name,
                "type": preset.preset_type,
                "parameters": {}
            }
            for param in preset.parameters:
                key = f"{param.group_name}.{param.parameter_name}"
                entry["parameters"][key] = param.value
            data_to_dump.append(entry)

        with open(output_file, "w") as yf:
            yaml.safe_dump(data_to_dump, yf, default_flow_style=False)

    def export_presets_to_json(self,
                               presets: List[ParsedPreset],
                               output_file: str):
        """
        Exports a list of ParsedPreset objects to JSON format. Each ParsedPreset
        is converted to a dictionary via dataclasses.asdict() and written out.
        """
        json_list = []
        for preset in presets:
            # Convert dataclass to dict, but convert ParsedParameter objects to built-ins
            param_dicts = []
            for p in preset.parameters:
                param_dicts.append({
                    "group_name": p.group_name,
                    "parameter_name": p.parameter_name,
                    "value": p.value,
                    "address": p.address,
                    "raw_message": p.raw_message,
                    "patch_index": p.patch_index
                })
            json_list.append({
                "name": preset.name,
                "type": preset.preset_type,
                "parameters": param_dicts
            })

        with open(output_file, "w") as jf:
            json.dump(json_list, jf, indent=2)
            logging.info(f"Exported {len(json_list)} presets to {output_file}")

# -----------------------------------------------
# Command‐line Interface
# -----------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="JV-1080 SysEx Parser")
    parser.add_argument("input_syx", help="Input .syx file (bulk dump of 128 patches)")
    parser.add_argument("output_yaml", nargs="?", default=None,
                        help="Output YAML filename (e.g. \"bank_patches.yaml\"). If omitted, adds _patches.yaml.")
    parser.add_argument("--json", action="store_true",
                        help="Also dump JSON (same root name, with .json extension).")
    args = parser.parse_args()

    input_path = args.input_syx
    if not args.output_yaml:
        base, _ = os.path.splitext(input_path)
        output_path = base + "_patches.yaml"
    else:
        output_path = args.output_yaml

    parser_obj = JV1080SysExParser()

    # 1) Parse all parameters from the .syx
    all_params = parser_obj.parse_sysex_file(input_path)
    if not all_params:
        logging.error(f"No parameters found. Exiting.")
        sys.exit(1)

    # 2) Group into complete patches
    presets = parser_obj.group_parameters_into_patches(all_params)

    # 3) Export to YAML
    parser_obj.export_presets_to_yaml(presets, output_path)
    print(f"✓ Exported {len(presets)} patches to {output_path}")

    # 4) (Optional) Export to JSON
    if args.json:
        json_output = os.path.splitext(output_path)[0] + ".json"
        parser_obj.export_presets_to_json(presets, json_output)
        print(f"✓ Also exported JSON to {json_output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
