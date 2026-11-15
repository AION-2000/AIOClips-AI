import pytest

from backend.app.match_links import canonical_youtube_url, parse_youtube_video_id


def test_sample_match_link():
    url = "https://youtu.be/mmeLCAP74KA?si=Sw3Ooa10LK0Ooy2L"
    assert parse_youtube_video_id(url) == "mmeLCAP74KA"
    assert canonical_youtube_url(url) == "https://www.youtube.com/watch?v=mmeLCAP74KA"


@pytest.mark.parametrize("url", [
    "http://youtu.be/mmeLCAP74KA",
    "https://youtube.com.evil.example/watch?v=mmeLCAP74KA",
    "https://evil.example/?v=mmeLCAP74KA",
    "https://youtu.be/not-an-id",
    "https://youtube.com/watch?v=mmeLCAP74KA&v=AAAAAAAAAAA",
    "https://user:pass@youtu.be/mmeLCAP74KA",
])
def test_rejects_unsafe_or_invalid_links(url):
    with pytest.raises(ValueError):
        parse_youtube_video_id(url)


def test_watch_url():
    assert parse_youtube_video_id("https://www.youtube.com/watch?v=mmeLCAP74KA") == "mmeLCAP74KA"
