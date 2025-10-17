from __future__ import annotations
import opengeode.lib64.opengeode_py_geometry
from opengeode.lib64.opengeode_py_geometry import Angle
from opengeode.lib64.opengeode_py_geometry import BoundingBox2D
from opengeode.lib64.opengeode_py_geometry import BoundingBox3D
from opengeode.lib64.opengeode_py_geometry import Circle
from opengeode.lib64.opengeode_py_geometry import ColocatedInfo2D
from opengeode.lib64.opengeode_py_geometry import ColocatedInfo3D
from opengeode.lib64.opengeode_py_geometry import CoordinateSystem1D
from opengeode.lib64.opengeode_py_geometry import CoordinateSystem2D
from opengeode.lib64.opengeode_py_geometry import CoordinateSystem3D
from opengeode.lib64.opengeode_py_geometry import Cylinder
from opengeode.lib64.opengeode_py_geometry import Frame1D
from opengeode.lib64.opengeode_py_geometry import Frame2D
from opengeode.lib64.opengeode_py_geometry import Frame3D
from opengeode.lib64.opengeode_py_geometry import INTERSECTION_TYPE
from opengeode.lib64.opengeode_py_geometry import InfiniteLine2D
from opengeode.lib64.opengeode_py_geometry import InfiniteLine3D
from opengeode.lib64.opengeode_py_geometry import IntersectionResultInfiniteLine3D
from opengeode.lib64.opengeode_py_geometry import IntersectionResultInlinedVectorPoint2D
from opengeode.lib64.opengeode_py_geometry import IntersectionResultInlinedVectorPoint3D
from opengeode.lib64.opengeode_py_geometry import IntersectionResultPoint2D
from opengeode.lib64.opengeode_py_geometry import IntersectionResultPoint3D
from opengeode.lib64.opengeode_py_geometry import NNSearch2D
from opengeode.lib64.opengeode_py_geometry import NNSearch3D
from opengeode.lib64.opengeode_py_geometry import OpenGeodeGeometryLibrary
from opengeode.lib64.opengeode_py_geometry import Plane
from opengeode.lib64.opengeode_py_geometry import Point1D
from opengeode.lib64.opengeode_py_geometry import Point2D
from opengeode.lib64.opengeode_py_geometry import Point3D
from opengeode.lib64.opengeode_py_geometry import Position
from opengeode.lib64.opengeode_py_geometry import Ray2D
from opengeode.lib64.opengeode_py_geometry import Ray3D
from opengeode.lib64.opengeode_py_geometry import Segment2D
from opengeode.lib64.opengeode_py_geometry import Segment3D
from opengeode.lib64.opengeode_py_geometry import Side
from opengeode.lib64.opengeode_py_geometry import Sphere2D
from opengeode.lib64.opengeode_py_geometry import Sphere3D
from opengeode.lib64.opengeode_py_geometry import Tetrahedron
from opengeode.lib64.opengeode_py_geometry import Triangle2D
from opengeode.lib64.opengeode_py_geometry import Triangle3D
from opengeode.lib64.opengeode_py_geometry import Vector1D
from opengeode.lib64.opengeode_py_geometry import Vector2D
from opengeode.lib64.opengeode_py_geometry import Vector3D
from opengeode.lib64.opengeode_py_geometry import colinear_segment_segment_intersection_detection2D
from opengeode.lib64.opengeode_py_geometry import dot_perpendicular
from opengeode.lib64.opengeode_py_geometry import lexicographic_mapping2D
from opengeode.lib64.opengeode_py_geometry import lexicographic_mapping3D
from opengeode.lib64.opengeode_py_geometry import line_cylinder_intersection3D
from opengeode.lib64.opengeode_py_geometry import line_line_intersection2D
from opengeode.lib64.opengeode_py_geometry import line_plane_intersection3D
from opengeode.lib64.opengeode_py_geometry import line_sphere_intersection2D
from opengeode.lib64.opengeode_py_geometry import line_sphere_intersection3D
from opengeode.lib64.opengeode_py_geometry import line_triangle_distance3D
from opengeode.lib64.opengeode_py_geometry import line_triangle_intersection3D
from opengeode.lib64.opengeode_py_geometry import line_triangle_intersection_detection3D
from opengeode.lib64.opengeode_py_geometry import morton_mapping2D
from opengeode.lib64.opengeode_py_geometry import morton_mapping3D
from opengeode.lib64.opengeode_py_geometry import ostream_redirect
from opengeode.lib64.opengeode_py_geometry import perpendicular
from opengeode.lib64.opengeode_py_geometry import plane_circle_intersection3D
from opengeode.lib64.opengeode_py_geometry import point_ball_distance2D
from opengeode.lib64.opengeode_py_geometry import point_ball_distance3D
from opengeode.lib64.opengeode_py_geometry import point_circle_distance3D
from opengeode.lib64.opengeode_py_geometry import point_circle_signed_distance3D
from opengeode.lib64.opengeode_py_geometry import point_disk_distance3D
from opengeode.lib64.opengeode_py_geometry import point_line_distance2D
from opengeode.lib64.opengeode_py_geometry import point_line_distance3D
from opengeode.lib64.opengeode_py_geometry import point_line_projection2D
from opengeode.lib64.opengeode_py_geometry import point_line_projection3D
from opengeode.lib64.opengeode_py_geometry import point_line_signed_distance2D
from opengeode.lib64.opengeode_py_geometry import point_plane_distance3D
from opengeode.lib64.opengeode_py_geometry import point_plane_projection
from opengeode.lib64.opengeode_py_geometry import point_plane_signed_distance3D
from opengeode.lib64.opengeode_py_geometry import point_point_distance2D
from opengeode.lib64.opengeode_py_geometry import point_point_distance3D
from opengeode.lib64.opengeode_py_geometry import point_segment_distance2D
from opengeode.lib64.opengeode_py_geometry import point_segment_distance3D
from opengeode.lib64.opengeode_py_geometry import point_segment_position2D
from opengeode.lib64.opengeode_py_geometry import point_segment_position3D
from opengeode.lib64.opengeode_py_geometry import point_segment_projection2D
from opengeode.lib64.opengeode_py_geometry import point_segment_projection3D
from opengeode.lib64.opengeode_py_geometry import point_side_to_line2D
from opengeode.lib64.opengeode_py_geometry import point_side_to_plane3D
from opengeode.lib64.opengeode_py_geometry import point_side_to_segment2D
from opengeode.lib64.opengeode_py_geometry import point_side_to_triangle3D
from opengeode.lib64.opengeode_py_geometry import point_sphere_distance2D
from opengeode.lib64.opengeode_py_geometry import point_sphere_distance3D
from opengeode.lib64.opengeode_py_geometry import point_sphere_signed_distance2D
from opengeode.lib64.opengeode_py_geometry import point_sphere_signed_distance3D
from opengeode.lib64.opengeode_py_geometry import point_tetrahedron_distance3D
from opengeode.lib64.opengeode_py_geometry import point_tetrahedron_position3D
from opengeode.lib64.opengeode_py_geometry import point_triangle_distance2D
from opengeode.lib64.opengeode_py_geometry import point_triangle_distance3D
from opengeode.lib64.opengeode_py_geometry import point_triangle_position2D
from opengeode.lib64.opengeode_py_geometry import point_triangle_position3D
from opengeode.lib64.opengeode_py_geometry import point_triangle_projection2D
from opengeode.lib64.opengeode_py_geometry import point_triangle_projection3D
from opengeode.lib64.opengeode_py_geometry import point_triangle_signed_distance3D
from opengeode.lib64.opengeode_py_geometry import rotate
from opengeode.lib64.opengeode_py_geometry import segment_barycentric_coordinates2D
from opengeode.lib64.opengeode_py_geometry import segment_barycentric_coordinates3D
from opengeode.lib64.opengeode_py_geometry import segment_cylinder_intersection3D
from opengeode.lib64.opengeode_py_geometry import segment_line_distance2D
from opengeode.lib64.opengeode_py_geometry import segment_line_distance3D
from opengeode.lib64.opengeode_py_geometry import segment_line_intersection2D
from opengeode.lib64.opengeode_py_geometry import segment_line_intersection_detection2D
from opengeode.lib64.opengeode_py_geometry import segment_plane_intersection3D
from opengeode.lib64.opengeode_py_geometry import segment_plane_intersection_detection3D
from opengeode.lib64.opengeode_py_geometry import segment_segment_distance2D
from opengeode.lib64.opengeode_py_geometry import segment_segment_distance3D
from opengeode.lib64.opengeode_py_geometry import segment_segment_intersection2D
from opengeode.lib64.opengeode_py_geometry import segment_segment_intersection_detection2D
from opengeode.lib64.opengeode_py_geometry import segment_sphere_intersection2D
from opengeode.lib64.opengeode_py_geometry import segment_sphere_intersection3D
from opengeode.lib64.opengeode_py_geometry import segment_triangle_distance3D
from opengeode.lib64.opengeode_py_geometry import segment_triangle_intersection3D
from opengeode.lib64.opengeode_py_geometry import segment_triangle_intersection_detection3D
from opengeode.lib64.opengeode_py_geometry import tetrahedron_barycentric_coordinates
from opengeode.lib64.opengeode_py_geometry import tetrahedron_signed_volume
from opengeode.lib64.opengeode_py_geometry import tetrahedron_volume
from opengeode.lib64.opengeode_py_geometry import tetrahedron_volume_sign
from opengeode.lib64.opengeode_py_geometry import triangle_area2D
from opengeode.lib64.opengeode_py_geometry import triangle_area3D
from opengeode.lib64.opengeode_py_geometry import triangle_area_sign2D
from opengeode.lib64.opengeode_py_geometry import triangle_area_sign3D
from opengeode.lib64.opengeode_py_geometry import triangle_barycentric_coordinates2D
from opengeode.lib64.opengeode_py_geometry import triangle_barycentric_coordinates3D
from opengeode.lib64.opengeode_py_geometry import triangle_circle_intersection3D
from opengeode.lib64.opengeode_py_geometry import triangle_signed_area2D
from opengeode.lib64.opengeode_py_geometry import triangle_signed_area3D
__all__: list[str] = ['Angle', 'BoundingBox2D', 'BoundingBox3D', 'Circle', 'ColocatedInfo2D', 'ColocatedInfo3D', 'CoordinateSystem1D', 'CoordinateSystem2D', 'CoordinateSystem3D', 'Cylinder', 'Frame1D', 'Frame2D', 'Frame3D', 'INTERSECTION_TYPE', 'InfiniteLine2D', 'InfiniteLine3D', 'IntersectionResultInfiniteLine3D', 'IntersectionResultInlinedVectorPoint2D', 'IntersectionResultInlinedVectorPoint3D', 'IntersectionResultPoint2D', 'IntersectionResultPoint3D', 'NNSearch2D', 'NNSearch3D', 'OpenGeodeGeometryLibrary', 'Plane', 'Point1D', 'Point2D', 'Point3D', 'Position', 'Ray2D', 'Ray3D', 'Segment2D', 'Segment3D', 'Side', 'Sphere2D', 'Sphere3D', 'Tetrahedron', 'Triangle2D', 'Triangle3D', 'Vector1D', 'Vector2D', 'Vector3D', 'colinear_segment_segment_intersection_detection2D', 'dot_perpendicular', 'edge0', 'edge01', 'edge02', 'edge03', 'edge1', 'edge12', 'edge13', 'edge2', 'edge23', 'facet0', 'facet1', 'facet2', 'facet3', 'incorrect', 'inside', 'intersect', 'lexicographic_mapping2D', 'lexicographic_mapping3D', 'line_cylinder_intersection3D', 'line_line_intersection2D', 'line_plane_intersection3D', 'line_sphere_intersection2D', 'line_sphere_intersection3D', 'line_triangle_distance3D', 'line_triangle_intersection3D', 'line_triangle_intersection_detection3D', 'morton_mapping2D', 'morton_mapping3D', 'negative', 'none', 'ostream_redirect', 'outside', 'parallel', 'perpendicular', 'plane_circle_intersection3D', 'point_ball_distance2D', 'point_ball_distance3D', 'point_circle_distance3D', 'point_circle_signed_distance3D', 'point_disk_distance3D', 'point_line_distance2D', 'point_line_distance3D', 'point_line_projection2D', 'point_line_projection3D', 'point_line_signed_distance2D', 'point_plane_distance3D', 'point_plane_projection', 'point_plane_signed_distance3D', 'point_point_distance2D', 'point_point_distance3D', 'point_segment_distance2D', 'point_segment_distance3D', 'point_segment_position2D', 'point_segment_position3D', 'point_segment_projection2D', 'point_segment_projection3D', 'point_side_to_line2D', 'point_side_to_plane3D', 'point_side_to_segment2D', 'point_side_to_triangle3D', 'point_sphere_distance2D', 'point_sphere_distance3D', 'point_sphere_signed_distance2D', 'point_sphere_signed_distance3D', 'point_tetrahedron_distance3D', 'point_tetrahedron_position3D', 'point_triangle_distance2D', 'point_triangle_distance3D', 'point_triangle_position2D', 'point_triangle_position3D', 'point_triangle_projection2D', 'point_triangle_projection3D', 'point_triangle_signed_distance3D', 'positive', 'rotate', 'segment_barycentric_coordinates2D', 'segment_barycentric_coordinates3D', 'segment_cylinder_intersection3D', 'segment_line_distance2D', 'segment_line_distance3D', 'segment_line_intersection2D', 'segment_line_intersection_detection2D', 'segment_plane_intersection3D', 'segment_plane_intersection_detection3D', 'segment_segment_distance2D', 'segment_segment_distance3D', 'segment_segment_intersection2D', 'segment_segment_intersection_detection2D', 'segment_sphere_intersection2D', 'segment_sphere_intersection3D', 'segment_triangle_distance3D', 'segment_triangle_intersection3D', 'segment_triangle_intersection_detection3D', 'tetrahedron_barycentric_coordinates', 'tetrahedron_signed_volume', 'tetrahedron_volume', 'tetrahedron_volume_sign', 'triangle_area2D', 'triangle_area3D', 'triangle_area_sign2D', 'triangle_area_sign3D', 'triangle_barycentric_coordinates2D', 'triangle_barycentric_coordinates3D', 'triangle_circle_intersection3D', 'triangle_signed_area2D', 'triangle_signed_area3D', 'vertex0', 'vertex1', 'vertex2', 'vertex3', 'zero']
edge0: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge0: 6>
edge01: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge01: 9>
edge02: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge02: 10>
edge03: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge03: 11>
edge1: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge1: 7>
edge12: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge12: 12>
edge13: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge13: 13>
edge2: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge2: 8>
edge23: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.edge23: 14>
facet0: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.facet0: 15>
facet1: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.facet1: 16>
facet2: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.facet2: 17>
facet3: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.facet3: 18>
incorrect: opengeode.lib64.opengeode_py_geometry.INTERSECTION_TYPE  # value = <INTERSECTION_TYPE.incorrect: 3>
inside: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.inside: 1>
intersect: opengeode.lib64.opengeode_py_geometry.INTERSECTION_TYPE  # value = <INTERSECTION_TYPE.intersect: 1>
negative: opengeode.lib64.opengeode_py_geometry.Side  # value = <Side.negative: 1>
none: opengeode.lib64.opengeode_py_geometry.INTERSECTION_TYPE  # value = <INTERSECTION_TYPE.none: 0>
outside: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.outside: 0>
parallel: opengeode.lib64.opengeode_py_geometry.INTERSECTION_TYPE  # value = <INTERSECTION_TYPE.parallel: 2>
positive: opengeode.lib64.opengeode_py_geometry.Side  # value = <Side.positive: 0>
vertex0: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.vertex0: 2>
vertex1: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.vertex1: 3>
vertex2: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.vertex2: 4>
vertex3: opengeode.lib64.opengeode_py_geometry.Position  # value = <Position.vertex3: 5>
zero: opengeode.lib64.opengeode_py_geometry.Side  # value = <Side.zero: 2>
