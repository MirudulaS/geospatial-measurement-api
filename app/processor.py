
import geopandas as gpd
import zipfile
import math
import pandas as pd
from pathlib import Path

def make_json_safe(value):
    """Convert missing and non-finite values into valid JSON values."""

    if value is None:
        return None

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    # Handle NaN, NaT and pandas missing values.
    try:
        missing = pd.isna(value)
        if isinstance(missing, bool) and missing:
            return None
        if getattr(missing, "ndim", 0) == 0 and bool(missing):
            return None
    except (TypeError, ValueError):
        pass

    # Convert NumPy scalar types into native Python values.
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass

    if isinstance(value, float) and not math.isfinite(value):
        return None

    if isinstance(value, dict):
        return make_json_safe(value)

    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value.isoformat()

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def read_geospatial_file(file_path: str, filename: str):
    """Read a KML file or ZIP containing one Shapefile."""

    extension = Path(filename).suffix.lower()

    if extension == ".kml":
        gdf = gpd.read_file(file_path, driver="KML")

    elif extension == ".zip":
        if not zipfile.is_zipfile(file_path):
            raise ValueError("The uploaded ZIP file is invalid.")

        with zipfile.ZipFile(file_path, "r") as archive:
            shp_files = [
                name for name in archive.namelist()
                if name.lower().endswith(".shp")
                and not name.startswith("__MACOSX/")
            ]

            if not shp_files:
                raise ValueError(
                    "The ZIP archive does not contain a Shapefile."
                )

            if len(shp_files) > 1:
                raise ValueError(
                    "Please upload a ZIP containing only one Shapefile."
                )

            shp_path = shp_files[0]

        gdf = gpd.read_file(f"zip://{file_path}!{shp_path}")

    else:
        raise ValueError("Only .kml and .zip files are supported.")

    source_crs = (
        gdf.crs.to_string() if gdf.crs is not None else None
    )

    return gdf, source_crs


def calculate_measurements(gdf: gpd.GeoDataFrame):
    """
    Calculate polygon area and LineString length in metres-based units.
    Geographic coordinates are transformed before measurement.
    """

    if gdf.crs is None:
        raise ValueError(
            "The source CRS is missing. Measurements cannot be calculated safely."
        )

    # Select a local UTM CRS from the data's geographic extent.
    # This is suitable for many local datasets, but not every global dataset.
    projected_crs = gdf.estimate_utm_crs()

    if projected_crs is None:
        raise ValueError(
            "Unable to determine a suitable projected CRS for measurement."
        )

    projected_gdf = gdf.to_crs(projected_crs)

    results = []

    for index, row in gdf.iterrows():
        geometry = row.geometry
        projected_geometry = projected_gdf.geometry.loc[index]

        if geometry is None or geometry.is_empty:
            geometry_type = (
                geometry.geom_type if geometry is not None else None
            )
            area = None
            length = None
            status = "UNSUPPORTED"
        else:
            geometry_type = geometry.geom_type
            area = None
            length = None
            status = "COMPLETED"

            if geometry_type in ("Polygon", "MultiPolygon"):
                area = float(projected_geometry.area)

            elif geometry_type in ("LineString", "MultiLineString"):
                length = float(projected_geometry.length)

            elif geometry_type == "Point":
                pass

            else:
                status = "UNSUPPORTED"

        results.append({
            "feature_id": int(index) if isinstance(index, int) else str(index),
            "geometry_type": geometry_type,
            "area_square_metres": area,
            "length_metres": length,
            "source_crs": gdf.crs.to_string(),
            "measurement_crs": projected_crs.to_string(),
            "properties": {
                key: value
                for key, value in row.items()
                if key != gdf.geometry.name
            },
            "status": status,
        })

    return make_json_safe(results)
