#!/usr/bin/env python3
"""Test 1: Plain rtmidi port scanning without creating any ports."""

import time
import rtmidi

print("Test 1: Plain rtmidi scanning (no virtual port)")
print("=" * 50)
print("Connect/disconnect MIDI devices and watch for changes...")
print()

while True:
    midi_in = rtmidi.MidiIn()
    in_ports = midi_in.get_ports()
    del midi_in

    print(f"[{time.strftime('%H:%M:%S')}] Input ports: {in_ports}")
    time.sleep(2)
