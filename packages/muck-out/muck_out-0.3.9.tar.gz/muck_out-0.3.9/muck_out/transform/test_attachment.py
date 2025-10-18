import pytest

from .attachment import transform_attachment


def test_normalize():
    attachment = {
        "type": "Document",
    }

    result = transform_attachment(attachment)

    assert result["type"] == "Document"


@pytest.mark.parametrize(
    ["media_type", "object_type"],
    [
        ("image/png", "Image"),
        ("image/jpeg", "Image"),
        ("video/mp4", "Video"),
        ("audio/mp4", "Audio"),
        ("text/plain", "Document"),
    ],
)
def test_normalize_image(media_type, object_type):
    attachment = {
        "type": "Document",
        "mediaType": media_type,
    }

    result = transform_attachment(attachment)

    assert result["type"] == object_type
