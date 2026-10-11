
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_KML = PROJECT_ROOT / "sample.kml"


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


def test_upload_valid_kml():
    with open(SAMPLE_KML, "rb") as file:
        response = client.post(
            "/api/files/",
            files={
                "file": (
                    "sample.kml",
                    file,
                    "application/vnd.google-earth.kml+xml",
                )
            },
        )

    assert response.status_code == 201

    data = response.json()
    assert data["filename"] == "sample.kml"
    assert data["feature_count"] == 2
    assert data["crs"] == "EPSG:4326"
    assert data["status"] == "COMPLETED"


def test_get_file_info():
    with open(SAMPLE_KML, "rb") as file:
        upload = client.post(
            "/api/files/",
            files={"file": ("sample.kml", file, "application/xml")},
        )

    file_id = upload.json()["id"]
    response = client.get(f"/api/files/{file_id}/")

    assert response.status_code == 200
    assert response.json()["id"] == file_id
    assert response.json()["filename"] == "sample.kml"


def test_get_measurements():
    with open(SAMPLE_KML, "rb") as file:
        upload = client.post(
            "/api/files/",
            files={"file": ("sample.kml", file, "application/xml")},
        )

    file_id = upload.json()["id"]
    response = client.get(
        f"/api/files/{file_id}/measurements/"
    )

    assert response.status_code == 200

    data = response.json()
    assert data["feature_count"] == 2

    polygon = next(
        item for item in data["measurements"]
        if item["geometry_type"] == "Polygon"
    )
    point = next(
        item for item in data["measurements"]
        if item["geometry_type"] == "Point"
    )

    assert polygon["area_square_metres"] > 0
    assert polygon["length_metres"] is None
    assert polygon["source_crs"] == "EPSG:4326"
    assert polygon["measurement_crs"] != "EPSG:4326"

    assert point["area_square_metres"] is None
    assert point["length_metres"] is None


def test_unsupported_file_extension():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "invalid.txt",
                b"Not a geospatial file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "Only .kml and .zip files are supported" in response.json()["detail"]


def test_invalid_kml():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "invalid.kml",
                b"This is not valid KML",
                "application/xml",
            )
        },
    )

    assert response.status_code in (400, 422)


def test_invalid_zip():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "invalid.zip",
                b"This is not a valid ZIP archive",
                "application/zip",
            )
        },
    )

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_missing_file_id():
    response = client.get("/api/files/nonexistent-id/")

    assert response.status_code == 404