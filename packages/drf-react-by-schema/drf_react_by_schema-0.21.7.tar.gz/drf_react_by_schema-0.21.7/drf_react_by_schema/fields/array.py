from django.contrib.postgres.fields import ArrayField


class ArrayField(ArrayField):
    description = "Extended PostgreSQL ArrayField"

    def __init__(self, *args, ui_required=False, conditional_visible=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible
