from rest_framework import serializers


class TypedSerializerMethodField(serializers.SerializerMethodField):
    description = "Extended SerializerMethodField"

    def __init__(self, *args, return_type="string", conditional_visible=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_type = return_type
        self.conditional_visible = conditional_visible
