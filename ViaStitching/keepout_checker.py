#!/usr/bin/env python
"""
Keep-Out Zone Checker for KiCad ViaStitching Plugins
Compatible with KiCad 9.0.x

This module provides functions to check if a via position is allowed
by respecting keep-out zones at both board and footprint level.

Usage:
    from keepout_checker import KeepOutChecker
    
    # Initialize once per fill operation
    checker = KeepOutChecker(board)
    
    # Check each via position
    if checker.is_via_allowed(position, via_size):
        # Place via
        pass

Author: Keep-Out Zone Enhancement 2025 by MrDix
License: GPL v3
"""

import pcbnew
import math


class KeepOutChecker:
    """
    Efficient keep-out zone checker for via placement.
    Caches keep-out zones for performance.
    """
    
    def __init__(self, board, debug=False):
        """
        Initialize the checker and cache all keep-out zones.
        
        Args:
            board: KiCad BOARD object
            debug: Enable debug output
        """
        self.board = board
        self.debug = debug
        self.keepout_zones = self._collect_keepout_zones()
        
        if self.debug and len(self.keepout_zones) > 0:
            print(f"[KeepOutChecker] Found {len(self.keepout_zones)} keep-out zone(s)")
    
    def _collect_keepout_zones(self):
        """
        Collect all keep-out zones that prohibit vias.
        
        Returns:
            List of ZONE objects that are keep-out zones prohibiting vias
        """
        zones = []
        
        try:
            # 1. Board-level keep-out zones
            for i in range(self.board.GetAreaCount()):
                zone = self.board.GetArea(i)
                
                if zone.GetIsRuleArea() and zone.GetDoNotAllowVias():
                    zones.append(zone)
                    if self.debug:
                        print(f"[KeepOutChecker] Added board keep-out zone {i}")
            
            # 2. Footprint-level keep-out zones
            # API compatibility for both older and newer KiCad versions
            if hasattr(self.board, 'GetModules'):
                footprints = self.board.GetModules()
            else:
                footprints = self.board.GetFootprints()
            
            for footprint in footprints:
                for zone in footprint.Zones():
                    if zone.GetIsRuleArea() and zone.GetDoNotAllowVias():
                        zones.append(zone)
                        if self.debug:
                            print(f"[KeepOutChecker] Added footprint keep-out zone")
        
        except Exception as e:
            if self.debug:
                print(f"[KeepOutChecker] Error collecting zones: {e}")
        
        return zones
    
    def _is_point_in_zone(self, zone, point):
        """
        Check if a point is inside a zone using KiCad 9.0 API.
        
        Args:
            zone: ZONE object
            point: VECTOR2I point to test
            
        Returns:
            True if point is in zone, False otherwise
        """
        try:
            # Ensure point is VECTOR2I
            if not isinstance(point, pcbnew.VECTOR2I):
                point = pcbnew.VECTOR2I(int(point.x), int(point.y))
            
            # Get zone layers
            layer_set = zone.GetLayerSet()
            
            # Test on all layers the zone covers
            for layer_id in range(pcbnew.PCBNEW_LAYER_ID_START, 
                                 pcbnew.PCBNEW_LAYER_ID_START + pcbnew.PCB_LAYER_ID_COUNT):
                if layer_set.Contains(layer_id):
                    # KiCad 9.0 API: HitTestFilledArea(layer, VECTOR2I)
                    if zone.HitTestFilledArea(layer_id, point):
                        return True
            
            return False
            
        except Exception as e:
            if self.debug:
                print(f"[KeepOutChecker] Error in point test: {e}")
            return False
    
    def is_via_allowed(self, position, via_size, check_edges=True):
        """
        Check if a via can be placed at the given position.
        
        Args:
            position: VECTOR2I or compatible position
            via_size: Via diameter in nanometers
            check_edges: If True, also check points around via edge
            
        Returns:
            True if via is allowed, False if it would violate a keep-out zone
        """
        # No keep-out zones = all positions allowed
        if len(self.keepout_zones) == 0:
            return True
        
        try:
            # Ensure position is VECTOR2I
            if not isinstance(position, pcbnew.VECTOR2I):
                position = pcbnew.VECTOR2I(int(position.x), int(position.y))
            
            # Check center point
            for zone in self.keepout_zones:
                if self._is_point_in_zone(zone, position):
                    return False
            
            # Optionally check edge points
            if check_edges and via_size > 0:
                via_radius = via_size // 2
                
                # Check 8 points around the via edge
                for angle_deg in [0, 45, 90, 135, 180, 225, 270, 315]:
                    angle_rad = math.radians(angle_deg)
                    edge_x = int(position.x + via_radius * math.cos(angle_rad))
                    edge_y = int(position.y + via_radius * math.sin(angle_rad))
                    edge_point = pcbnew.VECTOR2I(edge_x, edge_y)
                    
                    for zone in self.keepout_zones:
                        if self._is_point_in_zone(zone, edge_point):
                            return False
            
            # All checks passed
            return True
            
        except Exception as e:
            if self.debug:
                print(f"[KeepOutChecker] Error checking position: {e}")
            # Fail-safe: allow placement if error occurs
            return True
    
    def get_zone_count(self):
        """Get the number of keep-out zones found."""
        return len(self.keepout_zones)


# Standalone function for simple usage
def is_via_allowed_at_position(board, position, via_size, cached_checker=None, debug=False):
    """
    Simple function to check if a via is allowed at a position.
    
    Args:
        board: KiCad BOARD object
        position: VECTOR2I position
        via_size: Via diameter in nanometers
        cached_checker: Optional pre-initialized KeepOutChecker for performance
        debug: Enable debug output
        
    Returns:
        True if via is allowed, False otherwise
    """
    if cached_checker is None:
        cached_checker = KeepOutChecker(board, debug=debug)
    
    return cached_checker.is_via_allowed(position, via_size)


# Example usage
if __name__ == "__main__":
    print("Keep-Out Zone Checker Module for KiCad ViaStitching")
    print("=" * 50)
    print()
    print("Usage in your plugin:")
    print()
    print("from keepout_checker import KeepOutChecker")
    print()
    print("# Initialize once")
    print("checker = KeepOutChecker(board, debug=True)")
    print()
    print("# Check each position")
    print("for position in via_positions:")
    print("    if checker.is_via_allowed(position, via_size):")
    print("        # Place via")
    print("        pass")
