import pytest
from app.original_video import render_explainer

def test_requires_beats(tmp_path):
    with pytest.raises(ValueError):
        render_explainer(title="Pressing", beats=[], output=str(tmp_path / "out.mp4"))
def test_rejects_non_mp4(tmp_path):
    with pytest.raises(ValueError):
        render_explainer(title="Pressing", beats=["Beat"], output=str(tmp_path / "out.mov"))
def test_rejects_long_title(tmp_path):
    with pytest.raises(ValueError):
        render_explainer(title="x"*111, beats=["Beat"], output=str(tmp_path / "out.mp4"))
def test_rejects_long_beat(tmp_path):
    with pytest.raises(ValueError):
        render_explainer(title="Pressing", beats=["x"*181], output=str(tmp_path / "out.mp4"))
