import json

from app.ml import model_registry


def test_promote_to_production_writes_active_pointer(tmp_path, monkeypatch):
    version = "test-model-001"
    version_dir = tmp_path / "versions" / version
    version_dir.mkdir(parents=True)
    (version_dir / "model_metadata.json").write_text(
        json.dumps({
            "model_version": version,
            "training_data_source": "synthetic",
            "lifecycle_status": "CANDIDATE",
        })
    )

    monkeypatch.setattr(model_registry, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(model_registry, "VERSIONS_DIR", tmp_path / "versions")
    monkeypatch.setattr(model_registry, "ACTIVE_POINTER_PATH", tmp_path / "active_version.json")

    result = model_registry.promote_to_production(
        version,
        "analyst@example.com",
        "test promotion",
    )

    assert result["active_version"] == version
    assert result["promoted_by"] == "analyst@example.com"

    metadata = json.loads((version_dir / "model_metadata.json").read_text())
    assert metadata["promoted_to_production"] is True
    assert metadata["production_promoted_by"] == "analyst@example.com"
    assert metadata["lifecycle_status"] == "ACTIVE"

    active_pointer = json.loads((tmp_path / "active_version.json").read_text())
    assert active_pointer["active_version"] == version


def test_validation_failed_versions_cannot_be_promoted(tmp_path, monkeypatch):
    version = "test-model-002"
    version_dir = tmp_path / "versions" / version
    version_dir.mkdir(parents=True)
    (version_dir / "model_metadata.json").write_text(
        json.dumps({
            "model_version": version,
            "training_data_source": "synthetic",
            "lifecycle_status": "VALIDATION_FAILED",
        })
    )

    monkeypatch.setattr(model_registry, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(model_registry, "VERSIONS_DIR", tmp_path / "versions")
    monkeypatch.setattr(model_registry, "ACTIVE_POINTER_PATH", tmp_path / "active_version.json")

    try:
        model_registry.promote_to_production(version, "analyst@example.com", "blocked")
    except ValueError as exc:
        assert "VALIDATION_FAILED" in str(exc)
    else:
        raise AssertionError("Expected promotion to be rejected")
