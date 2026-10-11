
import logging
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.processor import (
    calculate_measurements,
    read_geospatial_file,
)

# Configure logging so errors appear in the Uvicorn terminal.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Geospatial File Measurement API",
    description=(
        "Upload KML or zipped Shapefile data, "
        "inspect features, and calculate measurements."
    ),
    version="1.0.0",
)

# Temporary in-memory storage.
# Records are lost when the server restarts.
files_db = {}


@app.get("/")
def home():
    return {
        "message": "Geospatial Measurement API is running"
    }


@app.post("/api/files/", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a KML or zipped Shapefile."""

    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    if extension not in {".kml", ".zip"}:
        raise HTTPException(
            status_code=400,
            detail="Only .kml and .zip files are supported.",
        )

    temp_path = None

    try:
        # Save the upload temporarily so GeoPandas can read it.
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temp_path = temp_file.name

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                temp_file.write(chunk)

        # Parse the uploaded geospatial file.
        gdf, source_crs = read_geospatial_file(
            temp_path,
            filename,
        )

        file_id = str(uuid4())

        # Keep the GeoDataFrame for later measurement requests.
        files_db[file_id] = {
            "id": file_id,
            "filename": filename,
            "feature_count": len(gdf),
            "crs": source_crs,
            "status": "COMPLETED",
            "features": gdf,
        }

        logger.info(
            "File uploaded successfully: %s (%s features)",
            filename,
            len(gdf),
        )

        return {
            "id": file_id,
            "filename": filename,
            "feature_count": len(gdf),
            "crs": source_crs,
            "status": "COMPLETED",
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Failed to process uploaded file")

        raise HTTPException(
            status_code=422,
            detail=f"Unable to process the uploaded file: {exc}",
        ) from exc

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        await file.close()


@app.get("/api/files/{file_id}/")
def get_file_info(file_id: str):
    """Return information about an uploaded file."""

    file_record = files_db.get(file_id)

    if file_record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found. Upload the file again if the server restarted.",
        )

    return {
        "id": file_record["id"],
        "filename": file_record["filename"],
        "feature_count": file_record["feature_count"],
        "crs": file_record["crs"],
        "status": file_record["status"],
    }


@app.get("/api/files/{file_id}/measurements/")
def get_measurements(file_id: str):
    """Calculate and return measurements for every feature."""

    file_record = files_db.get(file_id)

    if file_record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found. Upload the file again if the server restarted.",
        )

    try:
        measurements = calculate_measurements(
            file_record["features"]
        )

        return {
            "file_id": file_id,
            "filename": file_record["filename"],
            "feature_count": len(measurements),
            "measurements": measurements,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Print the complete traceback in the Uvicorn terminal.
        logger.exception(
            "Measurement calculation failed for file %s",
            file_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Measurement calculation failed. "
                "Check the server terminal for the full error."
            ),
        ) from exc
