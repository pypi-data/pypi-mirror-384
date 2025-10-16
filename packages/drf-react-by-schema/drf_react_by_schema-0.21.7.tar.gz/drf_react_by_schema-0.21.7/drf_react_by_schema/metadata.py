import inspect
from django.db import models
from django.forms.models import model_to_dict
from rest_framework import serializers
from rest_framework.metadata import BaseMetadata, SimpleMetadata
from rest_framework.fields import CurrentUserDefault
from datetime import date, datetime

from . import TypedSerializerMethodField
from .utils import get_model, get_pattern_format

SLUG_FIELD_NAME = "slug"


class Metadata(SimpleMetadata):
    """
    Enhanced metadata with:
    - Field defaults
    - Validation rules
    - Type-specific attributes
    Returns:
        dict: Enhanced DRF and React By Schema' schema
    """

    def determine_metadata(self, request, view):
        metadata = super().determine_metadata(request, view)

        if not metadata.get("actions", {}).get("POST") or not hasattr(
            view, "get_serializer"
        ):
            return metadata

        try:
            serializer = view.get_serializer()
        except (AttributeError, TypeError, ValueError):
            return metadata

        model = getattr(getattr(serializer, "Meta", None), "model", None)
        if not model:
            return metadata

        metadata.update(
            {
                "verbose_name": getattr(model._meta, "verbose_name", None),
                "verbose_name_plural": getattr(
                    model._meta, "verbose_name_plural", None
                ),
            }
        )

        try:
            serializer_fields = serializer.get_fields()
        except (AttributeError, TypeError, ValueError):
            return metadata

        # Assign "serializermethodfield" type as text and "typedserializermethodfield" as return_type
        for serializer_field_name, serializer_field in serializer_fields.items():
            if serializer_field_name not in metadata["actions"]["POST"]:
                continue

            if isinstance(serializer_field, TypedSerializerMethodField):
                metadata["actions"]["POST"][serializer_field_name][
                    "type"
                ] = serializer_field.return_type
            elif isinstance(serializer_field, serializers.SerializerMethodField):
                metadata["actions"]["POST"][serializer_field_name]["type"] = "string"

            if (
                isinstance(serializer_field, serializers.CharField)
                and serializer_field.style
            ):
                metadata["actions"]["POST"][serializer_field_name][
                    "style"
                ] = serializer_field.style

        for field in model._meta.get_fields():
            field_name = getattr(field, "name", None)

            if not field_name or field_name not in metadata.get("actions", {}).get(
                "POST", {}
            ):
                continue

            serializer_field = serializer_fields.get(field_name)

            # Print default value in OPTIONS:
            try:
                default_value = (
                    field.get_default() if getattr(field, "get_default", None) else None
                )
            except Exception:
                default_value = None

            if default_value:
                if field.related_model and serializer_field:
                    try:
                        metadata["actions"]["POST"][field_name]["model_default"] = (
                            serializer_field.__class__(
                                field.related_model.objects.get(pk=default_value)
                            ).data
                        )
                    except field.related_model.DoesNotExist:
                        metadata["actions"]["POST"][field_name][
                            "model_default_error"
                        ] = "Related object not found"
                        pass
                else:
                    metadata["actions"]["POST"][field_name][
                        "model_default"
                    ] = default_value
            elif getattr(field, "auto_now_add", False) or getattr(
                field, "auto_now", None
            ):
                metadata["actions"]["POST"][field_name]["model_default"] = (
                    date.today()
                    if isinstance(field, models.DateField)
                    else datetime.now()
                )
            elif serializer_field and serializer_field.default:
                if isinstance(serializer_field.default, (int, str)):
                    metadata["actions"]["POST"][field_name][
                        "model_default"
                    ] = serializer_field.default
                elif isinstance(serializer_field.default, CurrentUserDefault):
                    metadata["actions"]["POST"][field_name][
                        "model_default"
                    ] = "currentUser"

            # Custom regex Validators:
            validators = getattr(field, "validators", [])
            validators_regex = []
            for validator in validators:
                regex = getattr(validator, "regex", None)
                if regex:
                    validators_regex.append(
                        {
                            "regex": validator.regex.pattern,
                            "message": validator.message,
                        }
                    )
            if len(validators_regex) > 0:
                metadata["actions"]["POST"][field_name][
                    "validators_regex"
                ] = validators_regex

            # Remove the automatic required=True of reverse related objects:
            if field_name in serializer_fields and isinstance(
                serializer_fields[field_name],
                serializers.ManyRelatedField,
            ):
                metadata["actions"]["POST"][field_name]["required"] = False

            # Add ui_required to OPTIONS:
            is_ui_required = getattr(field, "ui_required", False)
            metadata["actions"]["POST"][field_name]["ui_required"] = is_ui_required

            # Add model_required to OPTIONS:
            is_required = (
                not getattr(field, "blank", False)
                and not getattr(serializer_field, "read_only", False)
                and not (
                    field_name in serializer_fields
                    and isinstance(
                        serializer_fields[field_name],
                        serializers.ManyRelatedField,
                    )
                )
            )
            metadata["actions"]["POST"][field_name]["model_required"] = is_required

            # Add pattern_format to OPTIONS:
            pattern_format = get_pattern_format(getattr(field, "pattern_format", None))
            if pattern_format:
                metadata["actions"]["POST"][field_name][
                    "pattern_format"
                ] = pattern_format

            # Add help_text to OPTIONS:
            help_text = getattr(field, "help_text", None)
            if help_text:
                metadata["actions"]["POST"][field_name]["help_text"] = help_text

            # Add related model is editable to OPTIONS:
            related_editable = getattr(field, "related_editable", None)
            if related_editable is not None:
                metadata["actions"]["POST"][field_name][
                    "related_editable"
                ] = related_editable

            # Add DecimalField decimal_places in OPTIONS:
            decimal_places = getattr(field, "decimal_places", None)
            if decimal_places is not None:
                metadata["actions"]["POST"][field_name][
                    "decimal_places"
                ] = decimal_places

            # Add DecimalField max_digits in OPTIONS:
            max_digits = getattr(field, "max_digits", None)
            if max_digits is not None:
                metadata["actions"]["POST"][field_name]["max_digits"] = max_digits

            # Add DecimalField is_currency in OPTIONS:
            is_currency = getattr(field, "is_currency", None)
            if is_currency is not None:
                metadata["actions"]["POST"][field_name]["is_currency"] = is_currency

            # Add DecimalField prefix in OPTIONS:
            prefix = getattr(field, "prefix", None)
            if prefix is not None:
                metadata["actions"]["POST"][field_name]["prefix"] = prefix

            # Add DecimalField suffix in OPTIONS:
            suffix = getattr(field, "suffix", None)
            if suffix is not None:
                metadata["actions"]["POST"][field_name]["suffix"] = suffix

            # Add DateField views in OPTIONS:
            views = getattr(field, "views", None)
            if views is not None:
                metadata["actions"]["POST"][field_name]["date_views"] = views

            if field_name in serializer_fields and (
                isinstance(
                    serializer_fields[field_name],
                    (serializers.ManyRelatedField, serializers.ListSerializer),
                )
                or metadata["actions"]["POST"][field_name]["type"] == "list"
            ):
                metadata["actions"]["POST"][field_name]["many"] = True

            # Remove the automatic required=True of reverse related objects:
            if field_name in serializer_fields and isinstance(
                serializer_fields[field_name],
                serializers.ManyRelatedField,
            ):
                metadata["actions"]["POST"][field_name]["required"] = False

            # Print multiline in OPTIONS:
            if isinstance(field, models.TextField):
                metadata["actions"]["POST"][field_name]["model_multiline"] = True

            # Force slug to be read_only:
            if field_name == SLUG_FIELD_NAME:
                metadata["actions"]["POST"][field_name].update(
                    {
                        "required": False,
                        "read_only": True,
                    }
                )

            # Add max_file_size for ImageField and FileField in OPTIONS:
            max_file_size = getattr(field, "max_file_size", None)
            if max_file_size is not None:
                metadata["actions"]["POST"][field_name]["max_file_size"] = max_file_size

            # Add allowed_mime_types for ImageField and FileField in OPTIONS:
            allowed_mime_types = getattr(field, "allowed_mime_types", None)
            if allowed_mime_types is not None:
                metadata["actions"]["POST"][field_name][
                    "allowed_mime_types"
                ] = allowed_mime_types

            # Add help_text to OPTIONS:
            conditional_visible = getattr(field, "conditional_visible", None)
            if conditional_visible:
                metadata["actions"]["POST"][field_name][
                    "conditional_visible"
                ] = conditional_visible

        return metadata
