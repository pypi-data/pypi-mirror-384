import traceback
from django.apps import apps
from rest_framework.utils import model_meta
from rest_framework.serializers import ManyRelatedField
from django.db import models
from . import settings, autocomplete_serializers
from .utils import update_related_fields


class GenericSerializer(autocomplete_serializers.GenericAutocompleteSerializer):
    update_related = None
    model_fields = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_fields = self.Meta.model._meta.get_fields()
        if self.update_related is None:
            self.update_related = []
            for field in self.model_fields:
                if (
                    isinstance(field, models.SlugField)
                    and field.blank
                    and field.name in self.fields
                ):
                    self.fields[field.name].required = False
                field_class_name = field.__class__.__name__
                if field.related_model:
                    serializer = getattr(
                        autocomplete_serializers,
                        f"{field.related_model.__name__}Serializer",
                        None,
                    )
                    # TODO: rename label to verbose_name in ForeignKey
                    field_label = getattr(field, "label", "")
                    label = getattr(field, "verbose_name", None)
                    if not label:
                        label = (
                            field_label
                            if field_label != ""
                            else getattr(
                                field.related_model._meta,
                                "verbose_name",
                                field.related_model.__name__,
                            )
                        )
                    if field_class_name == "OneToOneField":
                        self.update_related.append(field.name)
                        if serializer:
                            self.fields[field.name] = serializer(
                                read_only=True, label=label
                            )
                        continue
                    if field_class_name == "OneToOneRel":
                        # self.update_related.append(field.name)
                        if serializer:
                            self.fields[field.name] = serializer(
                                read_only=True, label=label
                            )
                        continue
                    if field_class_name == "ForeignKey":
                        if getattr(field, "related_editable", False):
                            self.update_related.append((field.name, "creatable"))
                        else:
                            self.update_related.append(field.name)
                        if serializer:
                            self.fields[field.name] = serializer(
                                read_only=True, label=label
                            )
                        continue
                    if field_class_name == "ManyToManyField":
                        self.update_related.append((field.name, "many"))
                        if serializer:
                            self.fields[field.name] = serializer(
                                read_only=True, label=label, many=True
                            )
                        continue
                    # if field_class_name == 'ManyToOneRel':
                    # if serializer:
                    #     self.fields[field.name] = serializer(read_only=True, many=True)
                    # continue
                    # Self.update_related.append(field.name)
                    # continue

    def to_internal_value(self, data):
        data = data.copy()

        # Clean empty RELATED fields that are not in data
        for field_name, field in self.fields.items():
            if isinstance(field, ManyRelatedField) and (
                field_name not in data or data[field_name] is None
            ):
                data[field_name] = []

        return super().to_internal_value(data)

    def create(self, validated_data, *args, **kwargs):
        # raise_errors_on_nested_writes("create", self, validated_data)

        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        try:
            instance = ModelClass._default_manager.create(**validated_data)
        except TypeError:
            tb = traceback.format_exc()
            msg = (
                "Got a `TypeError` when calling `%s.%s.create()`. "
                "This may be because you have a writable field on the "
                "serializer class that is not a valid argument to "
                "`%s.%s.create()`. You may need to make the field "
                "read-only, or override the %s.create() method to handle "
                "this correctly.\nOriginal exception was:\n %s"
                % (
                    ModelClass.__name__,
                    ModelClass._default_manager.name,
                    ModelClass.__name__,
                    ModelClass._default_manager.name,
                    self.__class__.__name__,
                    tb,
                )
            )
            raise TypeError(msg)

        # Save many-to-many relationships after the instance is created.
        # if many_to_many:
        #     for field_name, value in many_to_many.items():
        #         field = getattr(instance, field_name)
        #         field.set(value)

        instance = update_related_fields(
            instance=instance,
            request_data=self.context["normalized_raw_data"],
            update_related=self.update_related,
            model_fields=self.model_fields,
        )
        instance.save()

        return instance

    def update(self, instance, validated_data, *args, **kwargs):
        instance = update_related_fields(
            instance=instance,
            request_data=self.context["normalized_raw_data"],
            update_related=self.update_related,
            model_fields=self.model_fields,
        )

        return super().update(instance, validated_data)

    class Meta:
        fields = "__all__"


######################


for app in settings["APPS"]:
    for name, model in apps.all_models[app].items():
        model_name = model.__name__
        if isinstance(model, type):
            serializer_list_name = f"{model_name}ListSerializer"
            serializer_name = f"{model_name}Serializer"
            if not serializer_name in dir():
                meta = type("Meta", (), {"fields": "__all__", "model": model})
                generated_class = type(
                    serializer_list_name,
                    (GenericSerializer,),
                    {
                        "Meta": meta,
                    },
                )
                globals()[serializer_list_name] = generated_class

                generated_class = type(
                    serializer_name, (GenericSerializer,), {"Meta": meta}
                )
                globals()[serializer_name] = generated_class

                # Generate serializers for nested viewsets:
                # for field in model._meta.get_fields():
                #     if field.__class__.__name__ == 'ManyToOneRel':
                #         related_serializer_name = f"{model_name}Related{related_model_name}Serializer"
                #         related_model_name = field.related_model.__name__
                #         related_meta = type("Meta",(),{
                #             'fields':'__all__',
                #             'model':field.related_model
                #         })
                #         generated_class = type(serializer_name, (GenericSerializer,), {
                #             'Meta': related_meta
                #         })
                #         globals()[related_serializer_name] = generated_class
