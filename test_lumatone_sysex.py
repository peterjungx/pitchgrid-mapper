#!/usr/bin/env python3
"""Quick test to verify Lumatone SysEx message format."""

import sys
sys.path.insert(0, 'src')

from pg_isomap.controller_config import ControllerConfig
from pg_isomap.midi_setup import MIDITemplateBuilder
from pathlib import Path

def test_lumatone_sysex():
    """Test Lumatone SysEx message generation."""
    config = ControllerConfig(Path("controller_config/Lumatone.yaml"))
    builder = MIDITemplateBuilder(config)

    print("=== Lumatone SysEx Test ===\n")

    # Test a few pads from different boards
    test_pads = [
        (0, 0, "should be board 1"),
        (6, 0, "should be board 2"),
        (12, 0, "should be board 3"),
        (18, 0, "should be board 4"),
        (24, 0, "should be board 5"),
    ]

    for x, y, description in test_pads:
        # Calculate board index
        scope = config._build_helper_scope(x, y)
        board_idx = eval(config.config['boardIndex'], {"__builtins__": {}}, scope)
        key_idx = config.logical_coord_to_controller_note(x, y) - 30  # noteAssign is 30 + keyIndex
        channel = config.logical_coord_to_controller_channel(x, y)
        note_number = config.logical_coord_to_controller_note(x, y)

        print(f"Pad ({x}, {y}) - {description}")
        print(f"  Board Index: {board_idx} (should be 1-5 for SysEx)")
        print(f"  Key Index: {key_idx}")
        print(f"  Channel: {channel} (should be 0-4 for MIDI)")
        print(f"  Note Number: {note_number}")

        # Generate a color message
        midi_bytes = builder.set_pad_color(x, y, 255, 0, 0, 0)  # Red color
        if midi_bytes:
            hex_str = ' '.join(f'{b:02X}' for b in midi_bytes)
            print(f"  SetPadColor SysEx: {hex_str}")

            # Verify structure
            if midi_bytes[0] == 0xF0 and midi_bytes[-1] == 0xF7:
                print(f"    ✓ Valid SysEx (F0...F7)")
                print(f"    Manufacturer: {midi_bytes[1]:02X} {midi_bytes[2]:02X} {midi_bytes[3]:02X}")
                print(f"    Board Index byte: {midi_bytes[4]} (should match calculated: {board_idx})")
                print(f"    Command: {midi_bytes[5]:02X} (01 = SET_KEY_COLOUR)")
                print(f"    Key Index byte: {midi_bytes[6]}")
            else:
                print(f"    ✗ Invalid SysEx structure!")

        # Generate a note/channel assignment message
        midi_bytes = builder.set_pad_note_and_channel(x, y, note_number, channel)
        if midi_bytes:
            hex_str = ' '.join(f'{b:02X}' for b in midi_bytes)
            print(f"  SetPadNoteAndChannel SysEx: {hex_str}")

            # Verify structure
            if midi_bytes[0] == 0xF0 and midi_bytes[-1] == 0xF7:
                print(f"    ✓ Valid SysEx (F0...F7)")
                print(f"    Manufacturer: {midi_bytes[1]:02X} {midi_bytes[2]:02X} {midi_bytes[3]:02X}")
                print(f"    Board Index byte: {midi_bytes[4]} (should match calculated: {board_idx})")
                print(f"    Command: {midi_bytes[5]:02X} (00 = CHANGE_KEY_NOTE)")
                print(f"    Key Index byte: {midi_bytes[6]}")
                print(f"    Note Number byte: {midi_bytes[7]}")
                print(f"    MIDI Channel byte: {midi_bytes[8]}")
            else:
                print(f"    ✗ Invalid SysEx structure!")
        else:
            print(f"  ✗ SetPadNoteAndChannel returned None!")
        print()

    print("=== Verifying board index range ===")
    board_indices = set()
    for lx, ly, _, _ in config.pads:
        scope = config._build_helper_scope(lx, ly)
        board_idx = eval(config.config['boardIndex'], {"__builtins__": {}}, scope)
        board_indices.add(board_idx)

    print(f"Board indices found: {sorted(board_indices)}")
    print(f"Expected: [1, 2, 3, 4, 5] for Lumatone")
    if sorted(board_indices) == [1, 2, 3, 4, 5]:
        print("✓ Board indices are correct (1-5)")
    else:
        print("✗ Board indices are NOT correct!")

if __name__ == "__main__":
    test_lumatone_sysex()
