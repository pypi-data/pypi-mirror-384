from django.db import models


class DecimalField(models.DecimalField):
    description = "Extended DecimalField"

    def __init__(
        self,
        *args,
        is_currency=True,
        prefix="",
        suffix="",
        ui_required=False,
        conditional_visible=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.is_currency = is_currency and prefix == "" and suffix == ""
        self.prefix = prefix
        self.suffix = suffix
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible


class IntegerField(models.IntegerField):
    description = "Extended IntegerField allowing pattern_format for inputs"

    def __init__(
        self,
        *args,
        pattern_format=None,
        ui_required=False,
        conditional_visible=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.pattern_format = pattern_format
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible
