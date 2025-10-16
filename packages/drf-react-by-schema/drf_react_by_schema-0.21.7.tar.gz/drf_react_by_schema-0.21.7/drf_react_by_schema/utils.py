import re
import operator
import functools
import inspect
import json
from django.db.models import Q, Count, Case, When, IntegerField
from django.apps import apps
from django.http import QueryDict
from rest_framework.utils import json


def is_tmp_id(id):
    if not id:
        return True
    return str(id)[:3] == "tmp"


def update_simple_related_objects(**kwargs):
    instance = kwargs["instance"]
    key = kwargs["key"]
    related_objects_data = kwargs["related_objects_data"]
    related_objects_data_ids = []
    for related_obj in related_objects_data:
        if not related_obj.get("id", None):
            # Create new related object with this label:
            labelKey = kwargs.pop("labelKey", "nome")
            related_object_model = getattr(instance, key).model
            new_related_object_name = related_obj.get("label", None)
            if not new_related_object_name:
                continue
            new_related_object_data = {labelKey: new_related_object_name}
            try:
                (new_related_obj, created) = related_object_model.objects.get_or_create(
                    **new_related_object_data
                )
            except:
                continue
            related_objects_data_ids.append(new_related_obj.id)
        else:
            related_objects_data_ids.append(related_obj["id"])
    getattr(instance, key).set(related_objects_data_ids)
    for related_object in getattr(instance, key).all():
        if not related_object.id in related_objects_data_ids:
            getattr(instance, key).remove(related_object)
    return instance


def update_foreignkey(**kwargs):
    instance = kwargs["instance"]
    key = kwargs["key"]
    related_object_model = kwargs["related_object_model"]
    old_related_object = getattr(instance, key)
    related_object_id = kwargs["related_object_id"]

    if related_object_id:
        try:
            related_object = related_object_model.objects.get(pk=related_object_id)
            if not old_related_object or related_object.id != old_related_object.id:
                setattr(instance, key, related_object)
            return instance
        except:
            print(
                f"update_foreignkey: Could not find ${related_object_id} in ${related_object_model}, key ${key}"
            )
            pass

    if not old_related_object is None:
        setattr(instance, key, None)

    return instance


def create_or_update_foreignkey(**kwargs):
    labelKey = kwargs.pop("labelKey", "nome")
    data = kwargs.pop("data", None)
    kwargs["related_object_id"] = data
    if type(data) is dict:
        kwargs["related_object_id"] = data.pop("id", None)
        if "label" in data:
            data[labelKey] = data.pop("label")

        if is_tmp_id(kwargs["related_object_id"]) and data.get(labelKey, None):
            related_object_model = kwargs["related_object_model"]
            (related_object, created) = related_object_model.objects.get_or_create(
                **data
            )
            kwargs["related_object_id"] = related_object.id
    return update_foreignkey(**kwargs)


def update_related_fields(instance, request_data, update_related, model_fields):
    for item in update_related:
        key = item if type(item) is str else item[0]
        action = "update" if type(item) is str or len(item) < 2 else item[1]
        if key and key in request_data:
            value = request_data[key]
            if action == "many":
                instance = update_simple_related_objects(
                    instance=instance, key=key, related_objects_data=value
                )
                continue

            for field in model_fields:
                if getattr(field, "name", None) != key:
                    continue

                if action == "creatable":
                    instance = create_or_update_foreignkey(
                        instance=instance,
                        key=key,
                        data=value,
                        related_object_model=field.related_model,
                    )
                    break

                if action == "update":
                    instance = update_foreignkey(
                        instance=instance,
                        key=key,
                        related_object_id=value,
                        related_object_model=field.related_model,
                    )
                    break

    only_add_existing = request_data.pop("onlyAddExisting", None)
    if only_add_existing:
        for field in self.model_fields:
            if getattr(field, "name", None) != only_add_existing["key"]:
                continue
            obj_to_add = field.related_model.objects.get(pk=only_add_existing["value"])
            getattr(instance, only_add_existing["key"]).add(obj_to_add)

    return instance


def get_model(app, model_name):
    if not app or not model_name:
        return None
    return apps.get_model(app_label=app, model_name=model_name)


def camel_to_snake(name, suffix=None):
    if suffix:
        name = name.removesuffix(suffix)
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def to_pascal_case(s):
    return s.replace("_", " ").title().replace(" ", "")


def get_target_field(view, field, prefix=None):
    field_name = getattr(field, "name", None)
    related_model = getattr(field, "related_model", None)
    if related_model is None:
        if field_name is not None:
            return f"{prefix}__{field_name}" if prefix else field_name
    else:
        related_model_fields = related_model._meta.get_fields()
        related_model_serializer = view.serializer_class().fields.get(field_name)
        # TODO: Check why ManyToMany fields have no "label_field" in serializer.
        # Without the label_field, It's not possible to add this model to search and filters.
        label_field = getattr(related_model_serializer, "label_field", None)
        if label_field is None or label_field == "__str__":
            if "filter_and_search_field" in related_model.__dict__:
                label_field = related_model.__dict__["filter_and_search_field"]
            else:
                for related_model_field in related_model_fields:
                    if related_model_field.name in ["slug", "nome"]:
                        label_field = related_model_field.name
                        break

        if label_field:
            for related_model_field in related_model_fields:
                related_model_field_name = getattr(related_model_field, "name", None)
                if related_model_field_name == label_field:
                    return (
                        f"{prefix}__{field_name}__{related_model_field_name}"
                        if prefix
                        else f"{field_name}__{related_model_field_name}"
                    )
    return None


def serializer_to_model_field(view, serializer_field):
    if serializer_field is None or serializer_field.source == "id":
        return None

    field_sources = serializer_field.source.split(".")
    field = None
    first_field_source = field_sources.pop(0)
    if first_field_source == "*":
        return None

    try:
        field = view.model._meta.get_field(first_field_source)
    except:
        pass  # Serializer field doesnt exist in model

    if field or len(field_sources) > 0:
        target_field = None
        if len(field_sources) == 0:
            target_field = get_target_field(view, field)
        else:
            related_model = getattr(field, "related_model", None)

            if len(field_sources) == 1:
                field = related_model._meta.get_field(field_sources[0])
                target_field = get_target_field(view, field, first_field_source)

            if len(field_sources) == 2:
                second_field = related_model._meta.get_field(field_sources[0])
                second_related_model = getattr(second_field, "related_model", None)
                third_field = second_related_model._meta.get_field(field_sources[1])
                prefix = f"{first_field_source}__{second_field.name}"
                target_field = get_target_field(view, third_field, prefix)

        return target_field

    return serializer_field.source


def serializer_to_model_fields(view, fields_raw):
    fields = []
    for field_raw in fields_raw:
        field = field_raw[1:] if field_raw.startswith("-") else field_raw
        serializer_field = view.serializer_class().fields.get(field, None)
        target_field = serializer_to_model_field(view, serializer_field)
        if target_field:
            fields.append(
                f"-{target_field}" if field_raw.startswith("-") else target_field
            )

    return fields if len(fields) > 0 else None


def apply_data_grid_filter(view, qs, column_field, operator_value, value):
    column_field_serializer = view.serializer_class().fields.get(column_field, None)

    if column_field_serializer is None:
        return qs

    target_field = serializer_to_model_field(view, column_field_serializer)

    if target_field is None:
        return qs

    if operator_value == "contains" and value:
        return qs.filter(**{f"{target_field}__icontains": value})
    if operator_value == "equals" and value:
        return qs.filter(**{f"{target_field}__iexact": value})
    if operator_value == "startsWith" and value:
        return qs.filter(**{f"{target_field}__istartswith": value})
    if operator_value == "endsWith" and value:
        return qs.filter(**{f"{target_field}__iendswith": value})
    if operator_value == "isEmpty":
        if column_field_serializer.__class__.__name__ in [
            "DateField",
            "DecimalField",
            "IntegerField",
        ]:
            return qs.filter(Q(**{f"{target_field}__isnull": True}))
        # return qs.filter(
        #     Q(**{f"{target_field}__isnull": True}) |
        #     Q(**{f"{target_field}": ''})
        # )
        return qs.filter(Q(**{f"{target_field}__isnull": True}))
    if operator_value == "isNotEmpty":
        if column_field_serializer.__class__.__name__ in [
            "DateField",
            "DecimalField",
            "IntegerField",
        ]:
            return qs.exclude(Q(**{f"{target_field}__isnull": True}))
        # return qs.exclude(
        #     Q(**{f"{target_field}__isnull": True}) |
        #     Q(**{f"{target_field}": ''})
        # )
        return qs.exclude(Q(**{f"{target_field}__isnull": True}))
    if operator_value == "isAnyOf" and value:
        values = value.split(",")
        if column_field_serializer.__class__.__name__ in [
            "DecimalField",
            "IntegerField",
        ]:
            condition = functools.reduce(
                operator.or_, [Q(**{f"{target_field}": item}) for item in values]
            )
            return qs.filter(condition)
        condition = functools.reduce(
            operator.or_, [Q(**{f"{target_field}__iexact": item}) for item in values]
        )
        return qs.filter(condition)

    # DATE filters:
    if operator_value == "is" and value:
        return qs.filter(**{f"{target_field}": value})
    if operator_value == "not" and value:
        return qs.exclude(**{f"{target_field}": value})
    if operator_value == "after" and value:
        return qs.filter(**{f"{target_field}__gt": value})
    if operator_value == "before" and value:
        return qs.filter(**{f"{target_field}__lt": value})
    if operator_value == "onOrAfter" and value:
        return qs.filter(**{f"{target_field}__gte": value})
    if operator_value == "onOrBefore" and value:
        return qs.filter(**{f"{target_field}__lte": value})
    if operator_value == "entre" and value:
        values = value.split(",")
        if len(values) == 2 and values[0] and values[1]:
            return qs.filter(
                **{f"{target_field}__gte": values[0], f"{target_field}__lte": values[1]}
            )
        elif values[0]:
            return qs.filter(**{f"{target_field}__gte": values[0]})
        elif values[1]:
            return qs.filter(**{f"{target_field}__lte": values[1]})

    # NUMBER filters:
    if operator_value == "=" and value:
        return qs.filter(**{f"{target_field}": value})
    if operator_value == "!=" and value:
        return qs.exclude(**{f"{target_field}": value})
    if operator_value == ">" and value:
        return qs.filter(**{f"{target_field}__gt": value})
    if operator_value == ">=" and value:
        return qs.filter(**{f"{target_field}__gte": value})
    if operator_value == "<" and value:
        return qs.filter(**{f"{target_field}__lt": value})
    if operator_value == "<=" and value:
        return qs.filter(**{f"{target_field}__lte": value})

    return qs


def count_required_positional_args(func):
    """
    Count the number of required positional arguments for a function or method.
    """
    signature = inspect.signature(func)
    required_args = 0

    for name, param in signature.parameters.items():
        # Check if the parameter is positional-only or positional-or-keyword
        if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
            # Check if the parameter has no default value (i.e., it's required)
            if param.default == param.empty:
                required_args += 1

    return required_args


def normalize_request_data(request):
    """Convert request.data (QueryDict or dict) to a consistent nested dict. Useful for multipart data, files upload"""
    if isinstance(request.data, QueryDict):
        data = {}
        for key, value in request.data.lists():
            if "[" in key and "]" in key:
                keys = re.findall(r"(\w+)(?:\]|\[)?", key)
                current = data
                for k in keys[:-1]:
                    current = current.setdefault(k, {})
                new_value = []
                for item in value:
                    new_value.append(json.loads(item))
                current[keys[-1]] = new_value
            else:
                data[key] = value[0] if len(value) == 1 else value
        return data
    return request.data


def get_pattern_format(pattern_format):
    if pattern_format in ["telefone", "fone", "phone", "contact", "contato"]:
        return "(##)#####-####"

    if pattern_format == "cpf":
        return "###.###.###-##"

    if pattern_format == "cnpj":
        return "##.###.###/####-##"

    if pattern_format == "cep":
        return "##.###-###"

    return pattern_format
