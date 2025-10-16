from django.db import models
from django.core.validators import RegexValidator

from ..utils import get_pattern_format


class CharField(models.CharField):
    description = (
        "Extended CharField allowing pattern_format for inputs and ui required"
    )

    def __init__(
        self,
        *args,
        pattern_format=None,
        ui_required=False,
        conditional_visible=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pattern_format = pattern_format
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible

        pattern_format__str = get_pattern_format(pattern_format)

        if pattern_format__str:
            kwargs["max_length"] = pattern_format__str.count("#")

        super().__init__(*args, **kwargs)

        if pattern_format__str:
            self.validators.append(
                RegexValidator(
                    regex=f'^\\d{{{pattern_format__str.count("#")}}}$',  # ^\d{11}$
                    message=f'Precisa conter exatamente {pattern_format__str.count("#")} dígitos',
                )
            )


class TextField(models.TextField):
    description = "Extended TextField allowing ui required"

    def __init__(self, *args, ui_required=False, conditional_visible=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible


class EmailField(models.EmailField):
    description = "Extended EmailField allowing ui required"

    def __init__(self, *args, ui_required=False, conditional_visible=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_required = ui_required
        self.conditional_visible = conditional_visible
