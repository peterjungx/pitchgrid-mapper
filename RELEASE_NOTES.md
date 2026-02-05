## Changes in v0.2.2
- Added: Intel Mac (x86_64) support - now available for both Apple Silicon and Intel Macs
- Added: Lumatone support (experimental, untested)
- Fixed: LinnStrument channel lookup for reverse mapping
- Improved: Smarter note-off on mapping changes - only stops notes whose mapping actually changed
- Improved: Piano-like layout uses black for unmapped pads

## Changes in v0.2.1
- Fixed: Stop all playing notes on layout changes to prevent stuck notes
- Fixed: MPE support - note-off sent on correct MIDI channel
- Added: Vertical skew transformations for isomorphic layouts
- Improved: String-like layout colors (dark off-scale notes on device)
- Improved: Color enum mappings now parsed from controller config

## Installation

### Windows
1. Download the Windows installer (PitchGrid-Mapper-*-Setup.exe)
2. Run the installer
3. Follow the setup wizard
4. Launch PitchGrid Mapper from Start Menu or Desktop

### macOS
1. Download the appropriate DMG for your Mac:
   - **Apple Silicon** (M1/M2/M3): `PitchGrid-Mapper-*-arm64.dmg`
   - **Intel Mac**: `PitchGrid-Mapper-*-x86_64.dmg`
2. Open the DMG
3. Drag PitchGrid Mapper to Applications
4. Launch from Applications folder

## Requirements
- PitchGrid VST plugin (for scale sync)
- Windows: Virtual MIDI driver (e.g., loopMIDI) for MIDI routing
