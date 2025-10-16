from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ImageField(models.ImageField):
    description = "Extended ImageField with size and MIME type validation"

    def __init__(
        self,
        *args,
        max_file_size=None,
        allowed_mime_types=None,
        conditional_visible=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.max_file_size = max_file_size
        self.allowed_mime_types = allowed_mime_types

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if value:
            if self.max_file_size and value.size > self.max_file_size:
                raise ValidationError(
                    _("File size must be under %(max_size)s MB."),
                    params={"max_size": self.max_file_size // 1024 // 1024},
                )
            if self.allowed_mime_types:
                mime_type = getattr(value, "content_type", None)
                if mime_type and mime_type not in self.allowed_mime_types:
                    raise ValidationError(
                        _("File type not allowed. Allowed types: %(types)s."),
                        params={"types": ", ".join(self.allowed_mime_types)},
                    )


class FileField(models.FileField):
    description = "Extended FileField with size and MIME type validation"

    def __init__(
        self,
        *args,
        max_file_size=None,
        allowed_mime_types=None,
        ui_required=False,
        conditional_visible=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.max_file_size = max_file_size
        self.allowed_mime_types = allowed_mime_types
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if value:
            if self.max_file_size and value.size > self.max_file_size:
                raise ValidationError(
                    _("File size must be under %(max_size)s MB."),
                    params={"max_size": self.max_file_size // 1024 // 1024},
                )
            if self.allowed_mime_types:
                mime_type = getattr(value, "content_type", None)
                if mime_type and mime_type not in self.allowed_mime_types:
                    raise ValidationError(
                        _("File type not allowed. Allowed types: %(types)s."),
                        params={"types": ", ".join(self.allowed_mime_types)},
                    )
