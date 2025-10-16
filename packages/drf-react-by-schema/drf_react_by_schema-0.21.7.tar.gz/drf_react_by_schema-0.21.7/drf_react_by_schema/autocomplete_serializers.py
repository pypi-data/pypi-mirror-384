from django.apps import apps
from rest_framework import serializers
from . import settings


class GenericAutocompleteSerializer(serializers.ModelSerializer):
    label_field = "__str__"
    id = serializers.IntegerField(read_only=True)
    label = type(
        "SerializerMethodField",
        (serializers.SerializerMethodField, serializers.CharField),
        dict(),
    )("get_source")

    def get_source(self, obj) -> str:
        if self.label_field is None:
            return ""
        if isinstance(self.label_field, str):
            if self.label_field == "__str__":
                return obj.__str__()
            return getattr(obj, self.label_field, "")
        sub_obj = getattr(obj, self.label_field[0], None)
        if not sub_obj:
            return ""
        return getattr(sub_obj, self.label_field[1], "")

    class Meta:
        fields = ("id", "label")


######################

for app in settings["APPS"]:
    for name, model in apps.all_models[app].items():
        model_name = model.__name__
        if isinstance(model, type):
            serializer_name = f"{model_name}Serializer"
            if not serializer_name in dir():
                meta = type(
                    "Meta", (GenericAutocompleteSerializer.Meta,), {"model": model}
                )
                generated_class = type(
                    serializer_name, (GenericAutocompleteSerializer,), {"Meta": meta}
                )
                globals()[serializer_name] = generated_class
