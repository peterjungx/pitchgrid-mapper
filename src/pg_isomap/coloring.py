"""
Coloring schemes for pads based on scale role.

Provides different coloring strategies based on the pad's role in the MOS scale.
"""

import logging
from typing import Dict, Optional, Tuple

import scalatrix as sx

logger = logging.getLogger(__name__)


class ColoringScheme:
    """Base class for coloring schemes."""

    def get_color(
        self,
        mos_coord: Tuple[int, int],
        mos: Optional[sx.MOS],
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
        onsuperscale_color: str = "hsl(120, 70%, 50%)", # Green
        offscale_color: str = "hsl(0, 0%, 50%)",      # Gray
        onscale_color_unmapped: str = "hsl(270, 70%, 30%)",   # Cyan muted (darker)
        onsuperscale_color_unmapped: str = "hsl(120, 70%, 30%)", # Green muted (darker)
        offscale_color_unmapped: str = "hsl(0, 0%, 0%)"      # Gray muted (darker)
    ):
        """
        Initialize scale coloring scheme.

        Args:
            root_color: Color for root note
            onscale_color: Color for notes in the scale
            onsuperscale_color: Color for notes in the superscale   
            offscale_color: Color for notes outside the scale
            onscale_color_unmapped: Color for unmapped notes in the scale
            onsuperscale_color_unmapped: Color for unmapped notes in the superscale
            offscale_color_unmapped: Color for unmapped notes outside the scale
        """
        self.root_color = root_color
        self.onscale_color = onscale_color
        self.onsuperscale_color = onsuperscale_color
        self.offscale_color = offscale_color
        self.onscale_color_unmapped = onscale_color_unmapped
        self.onsuperscale_color_unmapped = onsuperscale_color_unmapped
        self.offscale_color_unmapped = offscale_color_unmapped

    def get_color(
        self,
        mos_coord: Optional[Tuple[int, int]],
        mos: sx.MOS,
        coord_to_scale_index: Dict[Tuple[int, int], int],
        supermos: Optional[sx.MOS] = None,
        use_dark_offscale: bool = False
    ) -> Optional[str]:
        """
        Get color based on scale role and mapping.

        Args:
            mos_coord: The (x, y) natural coordinate in MOS space, or None if pad is outside layout
            mos: The MOS object containing scale structure
            coord_to_scale_index: Mapping from coordinates to scale indices
            supermos: Optional superscale MOS object
            use_dark_offscale: If True, use unmapped color for off-scale notes
                              (useful for string-like layouts where all pads are mapped)
        """
        # Pads with no MOS coordinate (e.g., outside piano strips) get no color
        if mos_coord is None:
            return None

        try:
            d = mos_coord[0] * mos.b - mos_coord[1] * mos.a + mos.mode
            is_root = d == mos.mode
            if is_root:
                return self.root_color

            is_in_scale = d >= 0 and d < mos.n0
            if is_in_scale:
                if mos_coord in coord_to_scale_index:
                    return self.onscale_color
                else:
                    return self.onscale_color_unmapped

            if supermos:
                d_super = mos_coord[0] * supermos.b - mos_coord[1] * supermos.a + supermos.mode
                is_in_supermos = d_super >= 0 and d_super < supermos.n0
                if is_in_supermos:
                    if mos_coord in coord_to_scale_index:
                        return self.onsuperscale_color
                    else:
                        return self.onsuperscale_color_unmapped

            # For off-scale notes, use dark color if requested (string-like layout)
            if use_dark_offscale:
                return self.offscale_color_unmapped

            if mos_coord in coord_to_scale_index:
                return self.offscale_color

            return self.offscale_color_unmapped

        except Exception as e:
            logger.error(f"Error determining scale role for {mos_coord}: {e}")
            return self.offscale_color


# Default scheme
DEFAULT_COLORING_SCHEME = ScaleColoringScheme()
