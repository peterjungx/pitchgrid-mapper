#!/usr/bin/env python3
"""Test 4: mido port scanning with a virtual output port created first."""

import time

try:
    import mido
except ImportError:
    print("mido not installed. Run: pip install mido")
    exit(1)

print("Test 4: mido scanning with virtual output port")
print(f"Backend: {mido.backend}")
print("=" * 50)

# Create a virtual output port first (like our app does)
virtual_port = mido.open_output("TestVirtualPort", virtual=True)
print("Created virtual output port: TestVirtualPort")
print("Connect/disconnect MIDI devices and watch for changes...")
print()

try:
    while True:
        in_ports = mido.get_input_names()
        print(f"[{time.strftime('%H:%M:%S')}] Input ports: {in_ports}")
        time.sleep(2)
except KeyboardInterrupt:
    print("\nCleaning up...")
    virtual_port.close()
