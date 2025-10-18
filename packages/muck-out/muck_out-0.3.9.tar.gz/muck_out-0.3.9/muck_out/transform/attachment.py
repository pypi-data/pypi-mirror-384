from .list_utils import transform_to_list


def transform_attachment(attachment: dict | str) -> dict:
    """Normalizes an attachment"""

    if isinstance(attachment, str):
        return {"href": attachment}

    if attachment.get("type") != "Document":
        return attachment

    media_type = attachment.get("mediaType")
    if media_type is None:
        return attachment

    if media_type.startswith("image/"):
        attachment["type"] = "Image"
    if media_type.startswith("audio/"):
        attachment["type"] = "Audio"
    if media_type.startswith("video/"):
        attachment["type"] = "Video"

    return attachment


def transform_attachments(attachments) -> list[dict] | None:
    list_of_attachments = transform_to_list(attachments)

    return [transform_attachment(attachment) for attachment in list_of_attachments]
