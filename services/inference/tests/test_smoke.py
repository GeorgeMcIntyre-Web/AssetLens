from assetlens_inference.main import app


def test_app_imports() -> None:
    assert app.title == "AssetLens Inference"
