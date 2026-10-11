
from pathlib import Path
import zipfile

import geopandas as gpd
from shapely.geometry import Polygon, LineString

output_dir = Path("test_data")
output_dir.mkdir(exist_ok=True)

# Test 1: Polygon Shapefile
polygon_gdf = gpd.GeoDataFrame(
    {"name": ["Test Land"]},
    geometry=[
        Polygon([
            (77.00, 11.00),
            (77.02, 11.00),
            (77.02, 11.02),
            (77.00, 11.02),
            (77.00, 11.00),
        ])
    ],
    crs="EPSG:4326",
)

# Test 2: LineString Shapefile
line_gdf = gpd.GeoDataFrame(
    {"name": ["Test Road"]},
    geometry=[
        LineString([
            (77.00, 11.00),
            (77.01, 11.01),
            (77.02, 11.00),
        ])
    ],
    crs="EPSG:4326",
)


def create_zip(gdf, name):
    folder = output_dir / name
    folder.mkdir(exist_ok=True)

    shp_path = folder / f"{name}.shp"
    gdf.to_file(shp_path, driver="ESRI Shapefile")

    zip_path = output_dir / f"{name}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in folder.iterdir():
            if file_path.is_file():
                zf.write(file_path, arcname=file_path.name)

    print(f"Created: {zip_path.resolve()}")


create_zip(polygon_gdf, "polygon_test")
create_zip(line_gdf, "line_test")

print("Test files created successfully.")
