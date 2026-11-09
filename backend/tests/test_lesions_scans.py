from __future__ import annotations

import io
import json

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import DISCLAIMER, settings
from tests.conftest import Account, upload
from tests.synthetic import regular_spot, to_jpeg

FORBIDDEN_TERMS = [
    "melanoma", "carcinoma", "keratos", "nevi", "dermatofibroma", "vascular", "benign",
    "malignant", "cancer", "probabilit",
]


def assert_no_class_names(payload: object) -> None:
    text = json.dumps(payload).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in text, f"{term!r} leaked into API response"


def test_lesion_crud(client: TestClient, alice: Account) -> None:
    created = client.post(
        "/api/v1/lesions/", headers=alice.headers, json={"label": "Left shoulder", "body_location": "back"}
    )
    assert created.status_code == 201
    lesion = created.json()
    assert lesion["scan_count"] == 0 and lesion["latest_concern"] is None and lesion["thumbnail_url"] is None

    listing = client.get("/api/v1/lesions", headers=alice.headers).json()
    assert listing["total"] == 1 and listing["items"][0]["id"] == lesion["id"]

    patched = client.patch(
        f"/api/v1/lesions/{lesion['id']}", headers=alice.headers, json={"notes": "Since 2020", "body_location": "chest"}
    )
    assert patched.status_code == 200
    assert patched.json()["notes"] == "Since 2020" and patched.json()["body_location"] == "chest"

    detail = client.get(f"/api/v1/lesions/{lesion['id']}", headers=alice.headers).json()
    assert detail["scans"] == []

    assert client.delete(f"/api/v1/lesions/{lesion['id']}", headers=alice.headers).status_code == 204
    assert client.get(f"/api/v1/lesions/{lesion['id']}", headers=alice.headers).status_code == 404


def test_lesion_validation(client: TestClient, alice: Account) -> None:
    r = client.post("/api/v1/lesions/", headers=alice.headers, json={"label": "x", "body_location": "elbow"})
    assert r.status_code == 422


def test_lesions_are_private(client: TestClient, alice: Account, bob: Account) -> None:
    lesion = client.post(
        "/api/v1/lesions/", headers=alice.headers, json={"label": "Mine", "body_location": "face"}
    ).json()
    assert client.get(f"/api/v1/lesions/{lesion['id']}", headers=bob.headers).status_code == 404
    assert client.patch(f"/api/v1/lesions/{lesion['id']}", headers=bob.headers, json={"label": "x"}).status_code == 404
    assert client.delete(f"/api/v1/lesions/{lesion['id']}", headers=bob.headers).status_code == 404
    assert client.get("/api/v1/lesions/", headers=bob.headers).json()["total"] == 0


def test_upload_scan_full_contract(client: TestClient, alice: Account, irregular_jpeg: bytes) -> None:
    scan = upload(client, alice, irregular_jpeg)
    expected = {
        "id", "lesion_id", "created_at", "concern_level", "concern_score", "thumbnail_url", "headline",
        "image_url", "quality", "features", "observations", "recommendations", "symptoms", "model", "disclaimer",
    }
    assert set(scan) == expected
    assert scan["disclaimer"] == DISCLAIMER
    assert scan["concern_level"] in {"low", "moderate", "higher"}
    assert 0 <= scan["concern_score"] <= 100
    assert set(scan["quality"]) == {"ok", "blur_score", "brightness", "contrast", "issues"}
    assert set(scan["features"]) == {
        "asymmetry", "border_irregularity", "color_variation", "diameter_px", "diameter_relative", "color_count"
    }
    assert scan["model"]["kind"] == "heuristic"
    assert scan["image_url"] == f"/api/v1/scans/{scan['id']}/image"
    assert scan["thumbnail_url"] == f"/api/v1/scans/{scan['id']}/image?variant=thumb"
    assert scan["concern_level"] == "higher"
    assert scan["headline"].startswith("Irregular visual patterns detected.")
    assert "Consider professional dermatologist evaluation." in scan["recommendations"]
    assert_no_class_names(scan)

    lesion = client.get(f"/api/v1/lesions/{scan['lesion_id']}", headers=alice.headers).json()
    assert lesion["label"] == "Spot 1" and lesion["body_location"] == "other"
    assert lesion["scan_count"] == 1 and lesion["latest_concern"] == "higher"
    assert lesion["thumbnail_url"] == scan["thumbnail_url"]


def test_regular_spot_is_low_with_self_check_advice(client: TestClient, alice: Account, regular_jpeg: bytes) -> None:
    scan = upload(client, alice, regular_jpeg)
    assert scan["quality"]["ok"] is True
    assert scan["concern_level"] == "low"
    assert scan["headline"] == "No prominent irregular visual patterns detected."
    recs = " ".join(scan["recommendations"])
    assert "self-checks" in recs and "dermatologist" in recs


def test_upload_to_existing_lesion_with_symptoms(client: TestClient, alice: Account, regular_jpeg: bytes) -> None:
    lesion = client.post(
        "/api/v1/lesions/", headers=alice.headers, json={"label": "Arm", "body_location": "forearm_left"}
    ).json()
    symptoms = {"bleeding": True, "changed_size": True, "notes": "noticed last week"}
    scan = upload(client, alice, regular_jpeg, lesion_id=str(lesion["id"]), symptoms=json.dumps(symptoms))
    assert scan["lesion_id"] == lesion["id"]
    assert scan["symptoms"]["bleeding"] is True and scan["symptoms"]["itching"] is False
    # Symptoms raise the score above the plain image score and add guidance.
    plain = upload(client, alice, regular_jpeg, lesion_id=str(lesion["id"]))
    assert scan["concern_score"] > plain["concern_score"]
    assert any("healthcare professional" in r for r in scan["recommendations"])


def test_upload_to_foreign_lesion_404(client: TestClient, alice: Account, bob: Account, regular_jpeg: bytes) -> None:
    lesion = client.post("/api/v1/lesions/", headers=alice.headers, json={"label": "A", "body_location": "face"}).json()
    r = client.post(
        "/api/v1/scans/",
        headers=bob.headers,
        files={"image": ("a.jpg", regular_jpeg, "image/jpeg")},
        data={"lesion_id": str(lesion["id"])},
    )
    assert r.status_code == 404


def test_invalid_symptoms_json(client: TestClient, alice: Account, regular_jpeg: bytes) -> None:
    r = client.post(
        "/api/v1/scans/",
        headers=alice.headers,
        files={"image": ("a.jpg", regular_jpeg, "image/jpeg")},
        data={"symptoms": "{not json"},
    )
    assert r.status_code == 422


@pytest.mark.parametrize(
    ("content", "ctype", "status"),
    [
        (b"definitely not an image", "image/jpeg", 422),
        (b"GIF89a" + b"\x00" * 100, "image/jpeg", 422),
        (b"%PDF-1.4 fake", "application/pdf", 415),
    ],
)
def test_rejects_non_images(client: TestClient, alice: Account, content: bytes, ctype: str, status: int) -> None:
    r = client.post("/api/v1/scans/", headers=alice.headers, files={"image": ("x", content, ctype)})
    assert r.status_code == status


def test_rejects_truncated_jpeg(client: TestClient, alice: Account, regular_jpeg: bytes) -> None:
    r = client.post(
        "/api/v1/scans/", headers=alice.headers, files={"image": ("x.jpg", regular_jpeg[:2000], "image/jpeg")}
    )
    assert r.status_code == 422


def test_rejects_oversized_upload(client: TestClient, alice: Account, regular_jpeg: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 1000)
    r = client.post("/api/v1/scans/", headers=alice.headers, files={"image": ("x.jpg", regular_jpeg, "image/jpeg")})
    assert r.status_code == 413


def test_rejects_too_many_pixels(client: TestClient, alice: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "MAX_IMAGE_PIXELS", 100 * 100)
    r = client.post(
        "/api/v1/scans/", headers=alice.headers, files={"image": ("x.jpg", to_jpeg(regular_spot(256)), "image/jpeg")}
    )
    assert r.status_code == 422


def test_png_with_alpha_accepted(client: TestClient, alice: Account) -> None:
    rgba = Image.fromarray(regular_spot()).convert("RGBA")
    buf = io.BytesIO()
    rgba.save(buf, format="PNG")
    r = client.post("/api/v1/scans/", headers=alice.headers, files={"image": ("x.png", buf.getvalue(), "image/png")})
    assert r.status_code == 201


def test_exif_orientation_applied_and_metadata_stripped(client: TestClient, alice: Account) -> None:
    pixels = regular_spot(512)[:, :384]  # 384 wide x 512 tall
    exif = Image.Exif()
    exif[0x0112] = 6  # orientation: rotate 90 CW
    exif[0x010F] = "SecretCam"  # Make
    exif.get_ifd(0x8825)[1] = "N"  # GPS latitude ref
    scan = upload(client, alice, to_jpeg(pixels, exif=exif.tobytes()))
    r = client.get(scan["image_url"], headers=alice.headers)
    assert r.status_code == 200
    stored = Image.open(io.BytesIO(r.content))
    assert stored.size == (512, 384)  # rotated per EXIF
    assert len(stored.getexif()) == 0
    assert b"SecretCam" not in r.content
    assert "icc_profile" not in stored.info


def test_image_access_control(client: TestClient, alice: Account, bob: Account, regular_jpeg: bytes) -> None:
    scan = upload(client, alice, regular_jpeg)
    owner = client.get(scan["image_url"], headers=alice.headers)
    assert owner.status_code == 200
    assert owner.headers["content-type"] == "image/jpeg"
    assert owner.headers["cache-control"] == "private, no-store"

    thumb = client.get(scan["thumbnail_url"], headers=alice.headers)
    assert max(Image.open(io.BytesIO(thumb.content)).size) <= 256

    assert client.get(scan["image_url"], headers=bob.headers).status_code == 404
    assert client.get(scan["image_url"]).status_code == 401
    assert client.get(f"/api/v1/scans/{scan['id']}", headers=bob.headers).status_code == 404
    assert client.delete(f"/api/v1/scans/{scan['id']}", headers=bob.headers).status_code == 404


def test_images_stored_outside_static_and_encrypted_at_rest(
    client: TestClient, alice: Account, regular_jpeg: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    from cryptography.fernet import Fernet

    monkeypatch.setattr(settings, "IMAGE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    scan = upload(client, alice, regular_jpeg)
    files = sorted((settings.UPLOAD_DIR / str(alice.id)).iterdir())
    assert len(files) == 2 and all(f.name.endswith(".jpg.enc") for f in files)
    assert not files[0].read_bytes().startswith(b"\xff\xd8")  # not a plaintext JPEG
    r = client.get(scan["image_url"], headers=alice.headers)
    assert r.status_code == 200 and r.content.startswith(b"\xff\xd8")


def test_list_and_delete_scans(client: TestClient, alice: Account, regular_jpeg: bytes, irregular_jpeg: bytes) -> None:
    first = upload(client, alice, regular_jpeg)
    second = upload(client, alice, irregular_jpeg, lesion_id=str(first["lesion_id"]))
    other = upload(client, alice, regular_jpeg)

    listing = client.get("/api/v1/scans/", headers=alice.headers).json()
    assert listing["total"] == 3
    assert listing["items"][0]["id"] == other["id"]  # newest first
    filtered = client.get(f"/api/v1/scans?lesion_id={first['lesion_id']}", headers=alice.headers).json()
    assert {s["id"] for s in filtered["items"]} == {first["id"], second["id"]}
    page = client.get("/api/v1/scans/?limit=1&offset=1", headers=alice.headers).json()
    assert len(page["items"]) == 1 and page["total"] == 3

    detail = client.get(f"/api/v1/lesions/{first['lesion_id']}", headers=alice.headers).json()
    assert [s["id"] for s in detail["scans"]] == [second["id"], first["id"]]

    before = len(list((settings.UPLOAD_DIR / str(alice.id)).iterdir()))
    assert client.delete(f"/api/v1/scans/{second['id']}", headers=alice.headers).status_code == 204
    after = len(list((settings.UPLOAD_DIR / str(alice.id)).iterdir()))
    assert before - after == 2
    assert client.get(f"/api/v1/scans/{second['id']}", headers=alice.headers).status_code == 404


def test_delete_lesion_deletes_scan_files(client: TestClient, alice: Account, regular_jpeg: bytes) -> None:
    scan = upload(client, alice, regular_jpeg)
    assert client.delete(f"/api/v1/lesions/{scan['lesion_id']}", headers=alice.headers).status_code == 204
    assert list((settings.UPLOAD_DIR / str(alice.id)).iterdir()) == []
    assert client.get(f"/api/v1/scans/{scan['id']}", headers=alice.headers).status_code == 404


def test_poor_quality_photo_is_never_reassuring(client: TestClient, alice: Account) -> None:
    dark_blur = np.full((400, 400, 3), 25, dtype=np.uint8)
    scan = upload(client, alice, to_jpeg(dark_blur))
    assert scan["quality"]["ok"] is False
    assert scan["quality"]["issues"]
    assert scan["concern_level"] != "low"
    assert "Retake the photo in good light." in scan["recommendations"]
    assert "Retake" in scan["headline"]


def test_scan_rate_limit(client: TestClient, alice: Account, regular_jpeg: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_SCANS_PER_MINUTE", 2)
    upload(client, alice, regular_jpeg)
    upload(client, alice, regular_jpeg)
    r = client.post("/api/v1/scans/", headers=alice.headers, files={"image": ("a.jpg", regular_jpeg, "image/jpeg")})
    assert r.status_code == 429 and "retry-after" in r.headers
