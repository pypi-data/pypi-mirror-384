from django.db import models


class DateField(models.DateField):
    description = "Extended DateField"

    def __init__(
        self, *args, views=None, ui_required=False, conditional_visible=None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        if views:
            self.views = views
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible


class DateTimeField(models.DateTimeField):
    description = "Extended DateTimeField"

    def __init__(self, *args, ui_required=False, conditional_visible=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible
