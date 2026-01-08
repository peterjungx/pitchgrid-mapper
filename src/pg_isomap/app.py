"""
Main application coordinator.

Manages the lifecycle of all components and coordinates between them.
"""

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from .coloring import DEFAULT_COLORING_SCHEME
from .config import settings
from .controller_config import ControllerConfig, ControllerManager
from .layouts import (
    IsomorphicLayout,
    LayoutCalculator,
    LayoutConfig,
    LayoutType,
    PianoLikeLayout,
    StringLikeLayout,
)
from .midi_handler import MIDIHandler
from .osc_handler import OSCHandler
from .tuning import TuningHandler

logger = logging.getLogger(__name__)


class PGIsomapApp:
    """Main application coordinator."""

    def __init__(self):
        # Components
        self.controller_manager = ControllerManager(settings.controller_config_dir)
        self.midi_handler = MIDIHandler(settings.virtual_midi_device_name)
        self.osc_handler = OSCHandler(
            host=settings.osc_host,
            server_port=settings.osc_server_port,
            client_port=settings.osc_client_port
        )
        self.tuning_handler = TuningHandler()

        # State
        self.current_controller: Optional[ControllerConfig] = None
        self.current_layout_config: LayoutConfig = LayoutConfig(layout_type=LayoutType.ISOMORPHIC)
        self.current_layout_calculator: Optional[LayoutCalculator] = None

        # WebAPI reference (set by WebAPI after initialization)
        self.web_api = None

        # Discovery thread
        self._discovery_thread: Optional[threading.Thread] = None
        self._discovery_running = False

        # Setup callbacks
        self.osc_handler.on_scale_update = self._handle_scale_update
        self.osc_handler.on_note_mapping = self._handle_note_mapping
        self.osc_handler.on_connection_changed = self._handle_osc_connection_changed

    def start(self):
        """Start the application."""
        logger.info("Starting PG Isomap...")

        # Try to auto-load computer keyboard config FIRST
        self._try_load_computer_keyboard()

        # Initialize virtual MIDI port
        if not self.midi_handler.initialize_virtual_port():
            logger.error("Failed to create virtual MIDI port")
            return False

        # Start MIDI processing
        self.midi_handler.start()

        # Start OSC server
        self.osc_handler.start()

        # Start controller discovery
        self._start_discovery()

        logger.info("PG Isomap started successfully")
        logger.info(f"Current controller: {self.current_controller.device_name if self.current_controller else 'None'}")
        return True

    def stop(self):
        """Stop the application."""
        logger.info("Stopping PG Isomap...")

        # Stop discovery
        self._stop_discovery()

        # Stop components
        self.midi_handler.shutdown()
        self.osc_handler.stop()

        logger.info("PG Isomap stopped")

    def _start_discovery(self):
        """Start controller discovery thread."""
        if self._discovery_running:
            return

        self._discovery_running = True
        self._discovery_thread = threading.Thread(
            target=self._discovery_loop,
            daemon=True
        )
        self._discovery_thread.name = "Controller-Discovery"
        self._discovery_thread.start()

    def _stop_discovery(self):
        """Stop controller discovery thread."""
        self._discovery_running = False
        if self._discovery_thread:
            self._discovery_thread.join(timeout=5.0)
            self._discovery_thread = None

    def _discovery_loop(self):
        """Periodically scan for controllers."""
        while self._discovery_running:
            try:
                # Scan for available controllers
                # Available ports can be queried via get_available_controllers()
                # when needed by the UI
                self.midi_handler.get_available_controllers()

            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")

            time.sleep(settings.discovery_interval_seconds)

    def _try_load_computer_keyboard(self):
        """Try to load computer keyboard config on startup."""
        kb_config = self.controller_manager.get_config("Computer Keyboard")
        if kb_config:
            self.current_controller = kb_config
            self._recalculate_layout()
            logger.info("Computer keyboard config loaded")

    def connect_to_controller(self, device_name: str) -> bool:
        """
        Connect to a physical controller.

        Args:
            device_name: Name of the controller from configuration

        Returns:
            True if connection successful
        """
        # Get config
        config = self.controller_manager.get_config(device_name)
        if not config:
            logger.error(f"No configuration found for {device_name}")
            return False

        # Try to connect
        if not self.midi_handler.connect_to_controller(config.midi_device_name):
            return False

        # Update current controller
        self.current_controller = config

        # Reset layout calculator to default when changing controllers
        self.current_layout_calculator = None

        # Recalculate layout
        self._recalculate_layout()

        logger.info(f"Connected to {device_name}")
        return True

    def disconnect_controller(self):
        """Disconnect from current controller."""
        self.midi_handler.disconnect_controller()
        self.current_controller = None
        logger.info("Controller disconnected")

    def update_layout_config(self, config: LayoutConfig):
        """Update layout configuration and recalculate."""
        self.current_layout_config = config
        self._recalculate_layout()

    def apply_transformation(self, transformation_type: str) -> bool:
        """
        Apply a transformation to the current layout.

        Args:
            transformation_type: Transformation to apply (e.g., 'shift_left', 'rotate_right')

        Returns:
            True if transformation was applied successfully
        """
        if not self.current_layout_calculator:
            logger.warning("No layout calculator available")
            return False

        # Check if the layout calculator supports transformations
        if not hasattr(self.current_layout_calculator, 'apply_transformation'):
            logger.warning(f"Layout type {self.current_layout_config.layout_type} does not support transformations")
            return False

        try:
            # Apply the transformation
            self.current_layout_calculator.apply_transformation(transformation_type)

            # Recalculate the layout with the new transform
            self._recalculate_layout()

            logger.info(f"Applied transformation: {transformation_type}")
            return True

        except Exception as e:
            logger.error(f"Error applying transformation {transformation_type}: {e}")
            return False

    def _recalculate_layout(self):
        """Recalculate layout mapping and update MIDI handler."""
        if not self.current_controller:
            logger.warning("No controller loaded, cannot calculate layout")
            return

        # Create layout calculator only if we don't have one or if the type changed
        needs_new_calculator = (
            self.current_layout_calculator is None or
            (self.current_layout_config.layout_type == LayoutType.ISOMORPHIC and not isinstance(self.current_layout_calculator, IsomorphicLayout)) or
            (self.current_layout_config.layout_type == LayoutType.STRING_LIKE and not isinstance(self.current_layout_calculator, StringLikeLayout)) or
            (self.current_layout_config.layout_type == LayoutType.PIANO_LIKE and not isinstance(self.current_layout_calculator, PianoLikeLayout))
        )

        if needs_new_calculator:
            if self.current_layout_config.layout_type == LayoutType.ISOMORPHIC:
                # Pass default root coordinate from controller config
                default_root = self.current_controller.default_iso_root_coordinate
                self.current_layout_calculator = IsomorphicLayout(
                    self.current_layout_config,
                    default_root=default_root
                )
            elif self.current_layout_config.layout_type == LayoutType.STRING_LIKE:
                self.current_layout_calculator = StringLikeLayout(self.current_layout_config)
            elif self.current_layout_config.layout_type == LayoutType.PIANO_LIKE:
                self.current_layout_calculator = PianoLikeLayout(self.current_layout_config)
            else:
                logger.error(f"Unsupported layout type: {self.current_layout_config.layout_type}")
                return

        # Get logical coordinates from controller
        logical_coords = self.current_controller.get_logical_coordinates()

        # Calculate mapping using scale degrees from tuning handler
        mapping = self.current_layout_calculator.calculate_mapping(
            logical_coords,
            self.tuning_handler.scale_degrees,
            self.tuning_handler.steps,
            mos=self.tuning_handler.mos
        )

        # Build reverse mapping (controller_note -> logical_coord)
        # This requires knowing how the controller maps its physical pads to MIDI notes
        reverse_mapping: Dict[int, Tuple[int, int]] = {}

        for logical_x, logical_y in logical_coords:
            # Use controller's note mapping function if available
            controller_note = self._logical_to_controller_note(logical_x, logical_y)
            if controller_note is not None:
                reverse_mapping[controller_note] = (logical_x, logical_y)

        # Update MIDI handler
        self.midi_handler.update_note_mapping(mapping, reverse_mapping)

        logger.info(
            f"Layout recalculated: {len(mapping)} mapped pads, "
            f"{len(reverse_mapping)} reverse mappings"
        )

        # Broadcast updated status to WebSocket clients
        if self.web_api:
            self.web_api.broadcast_status_update()

    def _logical_to_controller_note(self, logical_x: int, logical_y: int) -> Optional[int]:
        """
        Convert logical coordinate to controller's native MIDI note number.

        This is controller-specific. For now, use a simple formula.
        Real implementation should use controller config.
        """
        if not self.current_controller:
            return None

        # For LinnStrument: note = x + y * 16
        # For other controllers, this varies
        # TODO: Make this configurable in controller YAML

        # Simple default: assume row-major layout
        note = logical_x + logical_y * 16

        if 0 <= note <= 127:
            return note
        return None

    def _handle_scale_update(self, scale_data: dict):
        """Handle scale/tuning update from PitchGrid plugin."""
        logger.info("Received scale/tuning update from PitchGrid")

        # Check if this is tuning data from /pitchgrid/plugin/tuning
        args = scale_data.get('args', [])

        if len(args) >= 7:
            # Parse tuning data: (depth, mode, root_freq, stretch, skew, mode_offset, steps)
            try:
                depth, mode, root_freq, stretch, skew, mode_offset, steps = args[:7]

                # Update tuning handler
                self.tuning_handler.update_tuning(
                    depth=depth,
                    mode=mode,
                    root_freq=root_freq,
                    stretch=stretch,
                    skew=skew,
                    mode_offset=mode_offset,
                    steps=steps
                )

                # Recalculate layout with new scale degrees
                self._recalculate_layout()

            except Exception as e:
                logger.error(f"Error processing tuning data: {e}")
        else:
            logger.warning(f"Unexpected scale data format: {args}")

    def _handle_note_mapping(self, mapping_data: dict):
        """Handle note mapping update from PitchGrid plugin."""
        logger.info("Received note mapping from PitchGrid")

        # Parse and apply note mapping
        # TODO: Implement based on actual PitchGrid OSC format

    def _handle_osc_connection_changed(self, connected: bool):
        """Handle OSC connection state change."""
        logger.info(f"OSC connection state changed: {'connected' if connected else 'disconnected'}")

        # Broadcast updated status to WebSocket clients
        if self.web_api:
            self.web_api.broadcast_status_update()

    def get_status(self) -> dict:
        """Get current application status."""
        # Get detected controllers (those actually available via MIDI)
        available_ports = self.midi_handler.get_available_controllers()
        detected_controllers = []
        for config_name in self.controller_manager.get_all_device_names():
            config = self.controller_manager.get_config(config_name)
            if config and config.device_name != "Computer Keyboard":
                # Check if this controller's MIDI device is available
                for port in available_ports:
                    if config.midi_device_name.lower() in port.lower():
                        detected_controllers.append(config_name)
                        break

        # Get controller pads for visualization with note mapping and colors
        controller_pads = []
        if self.current_controller:
            for x, y, px, py in self.current_controller.pads:
                coord = (x, y)
                # Get mapped note if available
                mapped_note = self.midi_handler.note_mapping.get(coord)

                # Calculate MOS coordinate and color based on scale system
                mos_coord = None
                color = None

                if self.current_layout_calculator and hasattr(self.current_layout_calculator, 'get_mos_coordinate'):
                    # Get MOS coordinate for this pad
                    mos_coord = self.current_layout_calculator.get_mos_coordinate(x, y)

                    # Use coloring scheme to determine color
                    color = DEFAULT_COLORING_SCHEME.get_color(
                        mos_coord=mos_coord,
                        mos=self.tuning_handler.mos,
                        steps=self.tuning_handler.steps
                    )
                elif mapped_note is not None:
                    # Fallback: simple hue based on note number
                    hue = (mapped_note * 30) % 360
                    color = f"hsl({hue}, 70%, 60%)"

                controller_pads.append({
                    'x': x,
                    'y': y,
                    'phys_x': px,
                    'phys_y': py,
                    'shape': self.current_controller.pad_shapes.get((x, y), []),
                    'note': mapped_note,
                    'color': color,
                    'mos_coord': mos_coord,
                })

        return {
            'connected_controller': self.current_controller.device_name if self.current_controller else None,
            'layout_type': self.current_layout_config.layout_type.value,
            'virtual_midi_device': settings.virtual_midi_device_name,
            'available_controllers': self.controller_manager.get_all_device_names(),
            'detected_controllers': detected_controllers,
            'controller_pads': controller_pads,
            'osc_connected': self.osc_handler.is_connected(),
            'osc_port': self.osc_handler.port,
            'tuning': self.tuning_handler.get_tuning_info(),
            'midi_stats': {
                'messages_processed': self.midi_handler.messages_processed,
                'notes_remapped': self.midi_handler.notes_remapped,
            }
        }
