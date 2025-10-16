"""Tests for utility helpers in the NomadicML SDK."""

import pytest

from nomadicml.exceptions import ValidationError
from nomadicml.types import VideoSource
from nomadicml.utils import infer_source


def test_infer_source_accepts_signed_url_with_query_params():
    url = (
        "https://storage.googleapis.com/bucket/path/video.mp4"
        "?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Expires=3600"
    )

    assert infer_source(url) is VideoSource.VIDEO_URL


def test_infer_source_rejects_remote_url_without_extension():
    url = "https://storage.googleapis.com/bucket/path/video?alt=media"

    with pytest.raises(ValidationError):
        infer_source(url)
