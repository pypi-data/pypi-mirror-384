import geopandas as gpd

INDEX_LEFT_COLUMN = "index_left"
INDEX_RIGHT_COLUMN = "index_right"
INTERSECTION_AREA_COLUMN = "intersection_area"
SHARE_LEFT_COLUMN = "share_left"
SHARE_RIGHT_COLUMN = "share_right"


def sjoin_intersections(left_gdf: gpd.GeoDataFrame, right_gdf: gpd.GeoDataFrame):
    """
    Compute geometric intersections between two GeoDataFrames and calculate area shares.

    This function performs a spatial overlay (`how='intersection'`) between two
    GeoDataFrames, preserving only the intersecting geometries. For each resulting
    intersection, it computes the intersection area as well as the relative share
    of that area with respect to the original geometries from both inputs.

    Parameters
    ----------
    left_gdf : geopandas.GeoDataFrame
        The left GeoDataFrame. Must contain polygonal geometries.
    right_gdf : geopandas.GeoDataFrame
        The right GeoDataFrame. Must contain polygonal geometries.

    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame containing intersection geometries between `left_gdf`
        and `right_gdf`, with the following additional columns:

        - ``INTERSECTION_AREA_COLUMN`` : float
          The area of the intersection geometry.
        - ``SHARE_LEFT_COLUMN`` : float
          The ratio of the intersection area to the area of the corresponding
          geometry in `left_gdf`.
        - ``SHARE_RIGHT_COLUMN`` : float
          The ratio of the intersection area to the area of the corresponding
          geometry in `right_gdf`.
        - ``INDEX_LEFT_COLUMN`` and ``INDEX_RIGHT_COLUMN`` : int
          Indices of the intersecting geometries from `left_gdf` and `right_gdf`,
          respectively.

    Notes
    -----
    - The function creates copies of both input GeoDataFrames to avoid modifying them in place.
    - Geometry types are not preserved strictly (`keep_geom_type=False`) to include
      all intersection results.
    - Division by zero can occur if any input geometry has zero area.

    Examples
    --------
    >>> import geopandas as gpd
    >>> from shapely.geometry import Polygon
    >>> left = gpd.GeoDataFrame(geometry=[Polygon([(0,0), (2,0), (2,2), (0,2)])])
    >>> right = gpd.GeoDataFrame(geometry=[Polygon([(1,1), (3,1), (3,3), (1,3)])])
    >>> sjoin_intersections(left, right)
       INDEX_LEFT  INDEX_RIGHT  intersection_area  share_left  share_right  geometry
    0            0            0               1.0         0.25         0.25  POLYGON ((1 1, 2 1, 2 2, 1 2, 1 1))
    """
    left_gdf = left_gdf.copy()
    right_gdf = right_gdf.copy()

    left_gdf[INDEX_LEFT_COLUMN] = left_gdf.index
    right_gdf[INDEX_RIGHT_COLUMN] = right_gdf.index

    overlay_gdf = gpd.overlay(
        left_gdf,
        right_gdf,
        how="intersection",
        keep_geom_type=False,
    )
    overlay_gdf[INTERSECTION_AREA_COLUMN] = overlay_gdf.area

    left_areas = left_gdf.geometry.area
    right_areas = right_gdf.geometry.area
    overlay_areas = overlay_gdf[INTERSECTION_AREA_COLUMN]

    overlay_gdf[SHARE_LEFT_COLUMN] = overlay_areas / overlay_gdf[INDEX_LEFT_COLUMN].map(left_areas)
    overlay_gdf[SHARE_RIGHT_COLUMN] = overlay_areas / overlay_gdf[INDEX_RIGHT_COLUMN].map(right_areas)

    return overlay_gdf
