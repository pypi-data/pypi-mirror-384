from django.core.files.uploadedfile import UploadedFile
from rest_framework.fields import FileField, ImageField


def _enhanced_file_representation(self, value):
    if value is None or value == "":
        return None

    if isinstance(value, str):
        return value

    # Handle Django's FileField/ImageFieldFile when empty
    if hasattr(value, "name") and not value.name:
        return None

    try:
        # Handle UploadedFile objects
        if isinstance(value, UploadedFile):
            if not hasattr(value, "content_type"):
                value.content_type = getattr(
                    value, "content_type", "application/octet-stream"
                )

            return {
                "name": getattr(value, "name", ""),
                "url": None,
                "size": getattr(value, "size", None),
                "content_type": getattr(value, "content_type", None),
            }

        # Handle saved files
        if hasattr(value, "url"):
            return {
                "name": getattr(value, "name", ""),
                "url": value.url,
                "size": getattr(value, "size", None),
                "content_type": getattr(value, "content_type", None),
            }

        return str(value)
    except Exception:
        return None


def _enhanced_file_internal_value(self, data):
    if isinstance(data, UploadedFile):
        return data
    return super().to_internal_value(data)


def patch_drf_fields():
    if not hasattr(FileField.to_representation, "_patched"):
        FileField.to_representation = _enhanced_file_representation
        FileField.to_internal_value = _enhanced_file_internal_value
        ImageField.to_representation = _enhanced_file_representation
        ImageField.to_internal_value = _enhanced_file_internal_value
        FileField.to_representation._patched = True
