#!/usr/bin/env python3
"""Test 2: rtmidi port scanning with a virtual output port created first."""

import time
import rtmidi

print("Test 2: rtmidi scanning with virtual output port")
print("=" * 50)

# Create a virtual output port first (like our app does)
midi_out = rtmidi.MidiOut()
midi_out.open_virtual_port("TestVirtualPort")
print("Created virtual output port: TestVirtualPort")
print("Connect/disconnect MIDI devices and watch for changes...")
print()

try:
    while True:
        midi_in = rtmidi.MidiIn()
        in_ports = midi_in.get_ports()
        del midi_in

        print(f"[{time.strftime('%H:%M:%S')}] Input ports: {in_ports}")
        time.sleep(2)
except KeyboardInterrupt:
    print("\nCleaning up...")
    midi_out.close_port()
    del midi_out
