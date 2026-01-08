"""
Coloring schemes for pads based on scale role.

Provides different coloring strategies based on the pad's role in the MOS scale.
"""

import logging
from typing import Optional, Tuple

import scalatrix

logger = logging.getLogger(__name__)


class ColoringScheme:
    """Base class for coloring schemes."""

    def get_color(
        self,
        mos_coord: Tuple[int, int],
        mos: Optional[scalatrix.MOS],
        steps: int
    ) -> Optional[str]:
        """
        Get color for a pad based on its MOS coordinate and role.

        Args:
            mos_coord: The (x, y) natural coordinate in MOS space
            mos: The MOS object containing scale structure
            steps: Total EDO steps

        Returns:
            CSS color string (e.g., "hsl(240, 70%, 60%)") or None
        """
        raise NotImplementedError


class ScaleColoringScheme(ColoringScheme):
    """
    Scale-based coloring: root / onscale / offscale.

    Colors pads based on their role in the scale:
    - Root: Magenta/pink (special highlighting)
    - On-scale: Cyan/blue (notes in the current mode)
    - Off-scale: Gray (notes outside the mode)
    """

    def __init__(
        self,
        root_color: str = "hsl(300, 70%, 60%)",      # Magenta
        onscale_color: str = "hsl(180, 70%, 50%)",   # Cyan
        offscale_color: str = "hsl(0, 0%, 40%)"      # Gray
    ):
        """
        Initialize scale coloring scheme.

        Args:
            root_color: Color for root note
            onscale_color: Color for notes in the scale
            offscale_color: Color for notes outside the scale
        """
        self.root_color = root_color
        self.onscale_color = onscale_color
        self.offscale_color = offscale_color

    def get_color(
        self,
        mos_coord: Tuple[int, int],
        mos: Optional[scalatrix.MOS],
        steps: int
    ) -> Optional[str]:
        """
        Get color based on scale role.

        Logic adapted from pg_linn_companion:
        - Root is the first node in MOS base scale
        - On-scale means the coordinate matches a node in the base scale
        - Off-scale means it doesn't match any node
        """
        if not mos:
            # No MOS available, use offscale color
            return self.offscale_color

        try:
            # Get MOS base scale nodes
            mos_nodes = mos.base_scale.getNodes()

            if not mos_nodes:
                return self.offscale_color

            # Create scalatrix Vector2i for comparison
            coord_vec = scalatrix.Vector2i(mos_coord[0], mos_coord[1])

            # Check if this is the root (first node in MOS)
            root_coord = mos_nodes[0].natural_coord
            if coord_vec.x == root_coord.x and coord_vec.y == root_coord.y:
                return self.root_color

            # Check if this coordinate is in the scale
            for node in mos_nodes:
                if coord_vec.x == node.natural_coord.x and coord_vec.y == node.natural_coord.y:
                    return self.onscale_color

            # Not in scale
            return self.offscale_color

        except Exception as e:
            logger.error(f"Error determining scale role for {mos_coord}: {e}")
            return self.offscale_color


# Default scheme
DEFAULT_COLORING_SCHEME = ScaleColoringScheme()
