"""
Controller configuration loader and manager.

Loads YAML configuration files for different isomorphic controllers.
"""

import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import yaml
from scipy.spatial import Voronoi

logger = logging.getLogger(__name__)


class ControllerConfig:
    """Configuration for an isomorphic controller."""

    def __init__(self, config_path: Path):
        self.config_path = config_path

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Basic properties
        self.device_name: str = self.config['DeviceName']
        self.midi_device_name: str = self.config['MIDIDeviceName']
        self.virtual_midi_device_name: str = self.config.get(
            'virtualMIDIDeviceName', f"PG {self.device_name}"
        )
        self.is_mpe: bool = self.config['isMPE']
        self.has_global_pitch_bend: bool = self.config['hasGlobalPitchBend']

        # Grid geometry
        self.num_rows: int = self.config['NumRows']
        self.first_row_idx: int = self.config['FirstRowIdx']
        self.row_lengths: List[int] = self.config['RowLengths']
        self.row_offsets: List[int] = self.config['RowOffsets']

        # Physical layout
        self.horizon_to_row_angle: float = self.config['HorizonToRowAngle']
        self.row_to_col_angle: float = self.config['RowToColAngle']
        self.x_spacing: float = self.config['xSpacing']
        self.y_spacing: float = self.config['ySpacing']

        # Optional properties
        self.fixed_labels: Optional[List] = self.config.get('fixedLabels')
        self.default_iso_root_coordinate: Optional[Tuple[int, int]] = None
        if 'defaultIsoRootCoordinate' in self.config:
            coord = self.config['defaultIsoRootCoordinate']
            self.default_iso_root_coordinate = (coord[0], coord[1])

        # MIDI commands (templates)
        self.set_pad_note_and_channel: Optional[str] = self.config.get('SetPadNoteAndChannel')
        self.set_pad_color: Optional[str] = self.config.get('SetPadColor')
        self.set_pad_notes_bulk: Optional[str] = self.config.get('SetPadNotesBulk')
        self.set_pad_colors_bulk: Optional[str] = self.config.get('SetPadColorsBulk')

        # Note mapping functions
        self.note_to_coord_x: Optional[str] = self.config.get('noteToCoordX')
        self.note_to_coord_y: Optional[str] = self.config.get('noteToCoordY')

        # Generate pad coordinates
        self.pads: List[Tuple[int, int, float, float]] = self._generate_pad_coordinates()

        # Calculate Voronoi shapes for each pad
        self.pad_shapes: Dict[Tuple[int, int], List[Tuple[float, float]]] = (
            self._calculate_voronoi_shapes()
        )

        logger.info(f"Loaded controller config: {self.device_name} ({len(self.pads)} pads)")

    def _generate_pad_coordinates(self) -> List[Tuple[int, int, float, float]]:
        """
        Generate logical and physical coordinates for all pads.

        Returns:
            List of (logical_x, logical_y, phys_x, phys_y) tuples
        """
        pads = []

        # Calculate cumulative row offset
        cumulative_row_offset = -sum([
            self.row_offsets[e]
            for e, _ in enumerate(range(self.first_row_idx, 0))
        ])

        # Precompute angles
        x_angle_rad = math.radians(self.horizon_to_row_angle)
        y_angle_rad = math.radians(self.row_to_col_angle + self.horizon_to_row_angle)

        for row_idx in range(self.num_rows):
            row = self.first_row_idx + row_idx
            row_length = self.row_lengths[row_idx]

            if row_idx > 0:
                row_offset = self.row_offsets[row_idx - 1]
                cumulative_row_offset += row_offset

            for col_idx in range(row_length):
                logical_x = cumulative_row_offset + col_idx
                logical_y = row

                # Convert to physical coordinates
                phys_x = (
                    logical_x * self.x_spacing * math.cos(x_angle_rad) +
                    logical_y * self.y_spacing * math.cos(y_angle_rad)
                )
                phys_y = (
                    logical_x * self.x_spacing * math.sin(x_angle_rad) +
                    logical_y * self.y_spacing * math.sin(y_angle_rad)
                )

                pads.append((logical_x, logical_y, phys_x, -phys_y))

        return pads

    def get_logical_coordinates(self) -> List[Tuple[int, int]]:
        """Get list of all logical coordinates."""
        return [(x, y) for x, y, _, _ in self.pads]

    def controller_note_to_logical_coord(self, note: int) -> Optional[Tuple[int, int]]:
        """
        Convert controller MIDI note to logical coordinate.

        This uses the noteToCoordX and noteToCoordY expressions from config.
        """
        if not self.note_to_coord_x or not self.note_to_coord_y:
            return None

        try:
            # Safe eval with limited scope
            scope = {'noteNumber': note}
            x = eval(self.note_to_coord_x, {"__builtins__": {}}, scope)
            y = eval(self.note_to_coord_y, {"__builtins__": {}}, scope)
            return (int(x), int(y))
        except Exception as e:
            logger.error(f"Error converting note {note} to coordinates: {e}")
            return None

    def _logical_to_physical(self, logical_x: int, logical_y: int) -> Tuple[float, float]:
        """Convert logical coordinates to physical coordinates."""
        x_angle_rad = math.radians(self.horizon_to_row_angle)
        y_angle_rad = math.radians(self.row_to_col_angle + self.horizon_to_row_angle)

        phys_x = (
            logical_x * self.x_spacing * math.cos(x_angle_rad) +
            logical_y * self.y_spacing * math.cos(y_angle_rad)
        )
        phys_y = (
            logical_x * self.x_spacing * math.sin(x_angle_rad) +
            logical_y * self.y_spacing * math.sin(y_angle_rad)
        )

        return phys_x, -phys_y

    def _calculate_voronoi_shapes(
        self, shrink_factor: float = 0.9
    ) -> Dict[Tuple[int, int], List[Tuple[float, float]]]:
        """
        Calculate Voronoi polygon vertices for each pad.

        Args:
            shrink_factor: Factor to shrink polygons for visual spacing (0.0-1.0)

        Returns:
            Dictionary mapping (logical_x, logical_y) -> list of (x, y) vertices
        """
        pad_shapes = {}

        for logical_x, logical_y, _, _ in self.pads:
            # Create a 3x3 grid of logical coordinates around this pad
            logical_coords = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    phys_x, phys_y = self._logical_to_physical(
                        logical_x + dx, logical_y + dy
                    )
                    logical_coords.append([phys_x, phys_y])

            points = np.array(logical_coords)

            try:
                vor = Voronoi(points)

                # Get region for central point (index 4 in 3x3 grid)
                center_index = 4
                region_index = vor.point_region[center_index]
                region = vor.regions[region_index]

                if -1 in region or len(region) == 0:
                    # Infinite region or invalid, use default hexagon
                    vertices = self._default_hexagon(shrink_factor)
                else:
                    # Get vertices from Voronoi
                    vertices = vor.vertices[region]
                    # Close the polygon
                    vertices = np.append(vertices, [vertices[0]], axis=0)

                    # Apply shrink factor relative to centroid
                    centroid = np.mean(vertices[:-1], axis=0)
                    vertices = centroid + (vertices - centroid) * shrink_factor

                # Convert to list of tuples
                pad_shapes[(logical_x, logical_y)] = [
                    (float(x), float(y)) for x, y in vertices
                ]

            except Exception as e:
                logger.warning(
                    f"Failed to calculate Voronoi for pad ({logical_x}, {logical_y}): {e}"
                )
                # Use default hexagon
                pad_shapes[(logical_x, logical_y)] = self._default_hexagon(shrink_factor)

        return pad_shapes

    def _default_hexagon(self, shrink_factor: float = 0.9) -> List[Tuple[float, float]]:
        """Generate a default hexagon shape for pads when Voronoi fails."""
        v_scale = self.y_spacing / max(self.x_spacing, 1.0)
        size = 0.5 * self.x_spacing * shrink_factor

        vertices = [
            (0, v_scale * size),
            (size, 0.5 * v_scale * size),
            (size, -0.5 * v_scale * size),
            (0, -v_scale * size),
            (-size, -0.5 * v_scale * size),
            (-size, 0.5 * v_scale * size),
            (0, v_scale * size),  # Close the polygon
        ]

        return vertices


class ControllerManager:
    """Manages available controller configurations."""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.configs: Dict[str, ControllerConfig] = {}
        self.load_configs()

    def load_configs(self):
        """Load all controller configurations from directory."""
        if not self.config_dir.exists():
            logger.warning(f"Controller config directory not found: {self.config_dir}")
            return

        for yaml_file in self.config_dir.glob("*.yaml"):
            try:
                config = ControllerConfig(yaml_file)
                self.configs[config.device_name] = config
                logger.info(f"Loaded controller: {config.device_name}")
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")

    def get_config(self, device_name: str) -> Optional[ControllerConfig]:
        """Get configuration for a specific device."""
        return self.configs.get(device_name)

    def get_all_device_names(self) -> List[str]:
        """Get list of all configured device names."""
        return list(self.configs.keys())

    def match_midi_port_to_config(self, port_name: str) -> Optional[ControllerConfig]:
        """
        Try to match a MIDI port name to a controller configuration.

        Args:
            port_name: MIDI port name from rtmidi

        Returns:
            Matching ControllerConfig or None
        """
        for config in self.configs.values():
            if config.midi_device_name.lower() in port_name.lower():
                return config
        return None
