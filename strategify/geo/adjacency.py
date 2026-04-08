"""Shared adjacency filtering utilities for geospatial neighbor detection.

Provides a single source of truth for determining whether two geometries
share a border (edge contact) versus merely touching at a corner point.
"""

from __future__ import annotations

from shapely.geometry.base import BaseGeometry


def is_edge_neighbor(
    geom_a: BaseGeometry,
    geom_b: BaseGeometry,
    return_length: bool = False,
) -> bool | float:
    """Return True (or shared length) if two geometries share a border.

    Uses intersection type to distinguish edge contacts (LineString /
    MultiLineString) from corner-only contacts (Point). Handles
    GeometryCollection by checking whether any sub-geometry is a line.

    Parameters
    ----------
    geom_a, geom_b:
        Shapely geometry objects to compare.
    return_length:
        If True, returns the length of the shared boundary (float)
        instead of a boolean. Returns 0.0 if not an edge contact.

    Returns
    -------
    bool | float
        Boolean indicating edge contact, or float length if requested.
    """
    if not geom_a.intersects(geom_b):
        return 0.0 if return_length else False

    intersection = geom_a.intersection(geom_b)
    geom_type = intersection.geom_type

    is_edge = False
    length = 0.0

    if geom_type in ("LineString", "MultiLineString"):
        if not intersection.is_empty:
            is_edge = True
            length = intersection.length

    elif geom_type == "GeometryCollection":
        for g in intersection.geoms:
            if g.geom_type in ("LineString", "MultiLineString") and not g.is_empty:
                is_edge = True
                length += g.length

    if return_length:
        return length if is_edge else 0.0
    return is_edge
