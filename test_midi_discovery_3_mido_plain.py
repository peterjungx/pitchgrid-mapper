#!/usr/bin/env python3
"""Test 3: Plain mido port scanning without creating any ports."""

import time

try:
    import mido
except ImportError:
    print("mido not installed. Run: pip install mido")
    exit(1)

print("Test 3: Plain mido scanning (no virtual port)")
print(f"Backend: {mido.backend}")
print("=" * 50)
print("Connect/disconnect MIDI devices and watch for changes...")
print()

while True:
    in_ports = mido.get_input_names()
    print(f"[{time.strftime('%H:%M:%S')}] Input ports: {in_ports}")
    time.sleep(2)
