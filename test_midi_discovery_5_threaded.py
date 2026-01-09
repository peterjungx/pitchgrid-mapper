#!/usr/bin/env python3
"""Test 5: rtmidi port scanning in a separate thread (like our app)."""

import threading
import time
import rtmidi

print("Test 5: rtmidi scanning in separate thread with virtual port")
print("=" * 50)

# Create a virtual output port on main thread (like our app does)
midi_out = rtmidi.MidiOut()
midi_out.open_virtual_port("TestVirtualPort")
print("Created virtual output port: TestVirtualPort")
print("Connect/disconnect MIDI devices and watch for changes...")
print()

stop_event = threading.Event()

def discovery_loop():
    """Run in separate thread like our discovery loop."""
    while not stop_event.is_set():
        midi_in = rtmidi.MidiIn()
        in_ports = midi_in.get_ports()
        del midi_in

        print(f"[{time.strftime('%H:%M:%S')}] (thread) Input ports: {in_ports}")
        time.sleep(2)

# Start discovery in separate thread
discovery_thread = threading.Thread(target=discovery_loop, daemon=True)
discovery_thread.start()
print("Discovery thread started")

try:
    # Main thread just waits
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")
    stop_event.set()
    discovery_thread.join(timeout=3)
    midi_out.close_port()
    del midi_out
