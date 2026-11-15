import pytest

from app.url_safety import UnsafeMediaURL, validate_media_url

HOSTS = {"media.example.com"}


@pytest.mark.parametrize("url", [
    "http://media.example.com/video.mp4",
    "https://127.0.0.1/video.mp4",
    "https://[::1]/video.mp4",
    "https://localhost/video.mp4",
    "https://sub.local/video.mp4",
    "https://media.example.com:8443/video.mp4",
    "https://user:pass@media.example.com/video.mp4",
    "https://media.example.com/video.mp4#fragment",
    "https://media.example.com/video.mp4\n",
    "https://evil.example.com/video.mp4",
    "https://media.example.com.evil.test/video.mp4",
    "file:///etc/passwd",
])
def test_reject_unsafe_url(url):
    with pytest.raises(UnsafeMediaURL):
        validate_media_url(url, allowed_hosts=HOSTS)


def test_approved_https_url():
    url = "https://media.example.com/video.mp4?token=abc"
    assert validate_media_url(url, allowed_hosts=HOSTS) == url


def test_no_default_allowlist():
    with pytest.raises(UnsafeMediaURL):
        validate_media_url("https://media.example.com/video.mp4")
