from app.artifacts import ModelManager


def test_model_manager_loads_latest_bundle_and_can_reload():
    manager = ModelManager()
    first = manager.bundle

    manager.reload()
    second = manager.bundle

    assert first.version == second.version
    assert first.onnx_session is not None
