
# Geospatial File Measurement API

A REST API built with FastAPI to upload and process KML files and zipped Shapefiles. It extracts feature information and calculates polygon areas and line lengths using an appropriate projected coordinate reference system.

## Features

- Upload KML and zipped Shapefile files.
- Extract geometry types, feature properties, and source CRS.
- Calculate Polygon and MultiPolygon areas in square metres.
- Calculate LineString and MultiLineString lengths in metres.
- Transform geographic coordinates into a projected CRS before measurement.
- Return structured JSON responses.
- Validate unsupported file types and invalid ZIP archives.
- Provide interactive API documentation through Swagger UI.

## Technology Stack

- Python
- FastAPI
- GeoPandas
- Shapely
- PyProj
- Uvicorn
- Pytest and HTTPX for testing

## Project Structure

```text
geospatial-measurement-api/
├── app/
│   ├── main.py
│   ├── processor.py
│   └── storage.py
├── tests/
├── test_data/
├── sample.kml
├── create_test_data.py
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd geospatial-measurement-api
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Run the API

```powershell
python -m uvicorn app.main:app --reload
```

The API runs locally at:

http://127.0.0.1:8000

Interactive documentation is available at:

http://127.0.0.1:8000/docs

## API Endpoints

### 1. Home

`GET /`

Checks whether the API is running.

### 2. Upload a file

`POST /api/files/`

Accepts a KML file or a ZIP archive containing a Shapefile.

Example response:

```json
{
  "id": "generated-file-id",
  "filename": "sample.kml",
  "feature_count": 2,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

### 3. Get file information

`GET /api/files/{file_id}/`

Returns metadata for an uploaded file.

### 4. Get measurements

`GET /api/files/{file_id}/measurements/`

Returns feature details and applicable measurements.

Example measurement fields:

```json
{
  "feature_id": 0,
  "geometry_type": "Polygon",
  "area_square_metres": 1209329.93,
  "length_metres": null,
  "source_crs": "EPSG:4326",
  "measurement_crs": "EPSG:32643",
  "properties": {
    "Name": "Sample Land"
  },
  "status": "COMPLETED"
}
```

Values above are illustrative; actual measurements depend on the input geometry and selected projected CRS.

## Measurement Approach

- Polygon and MultiPolygon geometries: calculate area in square metres.
- LineString and MultiLineString geometries: calculate length in metres.
- Point geometries: return no area or length.
- Record the original CRS and the projected CRS used for measurements.
- Reject files that cannot be processed.

Geographic coordinates expressed in degrees should not be used directly for planar area or length calculations. The geometry is transformed into a projected CRS before measurement.

## Error Handling

The API validates supported file extensions and handles malformed KML files and invalid ZIP archives with error responses.

## Limitations

- Uploaded file records are stored in memory and are lost when the server restarts.
- The ZIP input is expected to contain a usable Shapefile and its required supporting files.
- The current project is a local prototype and does not include persistent database storage or authentication.