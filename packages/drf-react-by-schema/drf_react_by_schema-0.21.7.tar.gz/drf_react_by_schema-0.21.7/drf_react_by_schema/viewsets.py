import logging
import time
import operator
import inspect
import importlib
from django.apps import apps
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.response import Response

from . import settings, serializers, utils
from .pagination import DRFReactBySchemaPagination


class LoggingMixin:
    """
    Provides full logging of requests and responses
    """

    initial_time = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("django.request")

    def initial(self, request, *args, **kwargs):
        self.initial_time = time.time()
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        if settings.get("DEBUG", True):
            try:
                time_delta_ms = (time.time() - self.initial_time) * 1000
                self.logger.debug(
                    {
                        # "request_data": request.data,
                        "request_method": request.method,
                        "request_endpoint": request.path,
                        "response_status_code": response.status_code,
                        "time_delta_request_to_response": "{0:.2f}ms".format(
                            time_delta_ms
                        ),
                    }
                )
            except Exception:
                self.logger.exception("Error logging request")
        return super().finalize_response(request, response, *args, **kwargs)


class DRFReactBySchemaBaseModelViewSet(LoggingMixin, viewsets.ModelViewSet):
    permission_classes = (
        [permissions.IsAuthenticated]
        if "PERMISSIONS" not in settings.get("DRF_REACT_BY_SCHEMA", {})
        else settings["DRF_REACT_BY_SCHEMA"]["PERMISSIONS"]
    )
    serializer_class = None
    serializer_list_class = None
    model = None
    app = None
    model_name = None
    many = True
    reverse_many = False
    parent_related_name = None
    parent_pk_field = None
    is_autocomplete = False
    queryset = None
    select_related = None
    prefetch_related = None
    annotate = None
    annotate_by_callback = None
    filter = None
    filter_by_callback = None
    filter_list_by_callback = None
    filter_by_parent_content_type = False
    exclude = None
    exclude_by_callback = None
    exclude_list_by_callback = None
    search_fields = None
    ordering_fields = None
    order_by = None
    limit = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.model:
            self.model = utils.get_model(self.app, self.model_name)
        if self.app and self.serializer_class is not None:
            threshold = 2 if self.serializer_list_class else 1
            found = 0
            try:
                app_serializers = importlib.import_module(
                    f"{self.app}.serializers"
                    if not self.is_autocomplete
                    else f"{self.app}.autocomplete_serializers"
                )
            except:
                return

            for app_serializer_name, app_serializer in inspect.getmembers(
                app_serializers, predicate=inspect.isclass
            ):
                if app_serializer_name == self.serializer_class.__name__:
                    self.serializer_class = app_serializer
                    found += 1

                if (
                    self.serializer_list_class
                    and app_serializer_name == self.serializer_list_class.__name__
                ):
                    self.serializer_list_class = app_serializer
                    found += 1

                if found == threshold:
                    break

    def get_queryset(self):
        query_params = self.request.query_params
        queryset = self.model.objects.all() if not self.queryset else self.queryset
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)

        if self.parent_related_name and self.parent_pk_field:
            key = self.parent_related_name
            value = self.kwargs[self.parent_pk_field]
            if self.many:
                value = [value]
                key = (
                    f"{self.parent_related_name}__contains"
                    if self.reverse_many
                    else f"{self.parent_related_name}__in"
                )
            kwargs = {key: value}
            if self.parent_model and self.filter_by_parent_content_type:
                content_type = ContentType.objects.get_for_model(self.parent_model)
                filter_kwargs["content_type"] = content_type.id
            queryset = queryset.filter(**kwargs)

        if self.filter:
            queryset = queryset.filter(**self.filter)

        if self.filter_by_callback:
            filter_kwargs = (
                self.filter_by_callback(queryset, self.kwargs)
                if utils.count_required_positional_args(self.filter_by_callback) == 2
                else self.filter_by_callback(queryset)
            )
            if filter_kwargs:
                if "or_kwargs" in filter_kwargs:
                    or_kwargs = filter_kwargs.pop("or_kwargs")
                    queryset = queryset.filter(
                        Q(**or_kwargs, _connector=Q.OR), **filter_kwargs
                    )
                else:
                    queryset = queryset.filter(**filter_kwargs)

        if self.exclude:
            queryset = queryset.exclude(**self.exclude)

        if self.exclude_by_callback:
            exclude_kwargs = self.exclude_by_callback(queryset)
            if exclude_kwargs:
                if "or_kwargs" in exclude_kwargs:
                    or_kwargs = exclude_kwargs.pop("or_kwargs")
                    queryset = queryset.exclude(
                        Q(**or_kwargs, _connector=Q.OR), **exclude_kwargs
                    )
                else:
                    queryset = queryset.exclude(**exclude_kwargs)

        if "columnField" in self.request.query_params and self.serializer_class:
            column_fields = self.request.GET.getlist("columnField")
            operator_values = self.request.GET.getlist("operatorValue")
            values = self.request.GET.getlist("value")

            if len(column_fields) == len(operator_values) == len(values):
                for column_field, operator_value, value in zip(
                    column_fields, operator_values, values
                ):
                    queryset = utils.apply_data_grid_filter(
                        self, queryset, column_field, operator_value, value
                    )
            else:
                raise ValueError(
                    "Mismatched filter parameters: columnField, operatorValue, and value counts must match."
                )

        if self.annotate:
            queryset = queryset.annotate(**self.annotate)

        if self.annotate_by_callback:
            annotate_kwargs = self.annotate_by_callback()
            if annotate_kwargs:
                queryset = queryset.annotate(**annotate_kwargs)

        if self.order_by:
            queryset = queryset.order_by(self.order_by)
        elif self.annotate or self.queryset:
            # orderings = ', '.join(map(str, self.model._meta.ordering))
            if self.model._meta.ordering:
                queryset = queryset.order_by(*self.model._meta.ordering)

        # is_first_batch = query_params.get('is_first_batch', None)
        # is_last_batch = query_params.get('is_last_batch', None)
        # if is_first_batch:
        #     queryset = queryset[:100]
        # elif is_last_batch:
        #     queryset = queryset[100:]
        # elif self.limit:
        #     queryset = queryset[:self.limit]

        return queryset

    def list(self, request, *args, **kwargs):
        if not self.is_autocomplete:
            # Populate select_related and prefetch_related if None:
            self.populate_select_and_prefetch_related()

            # Add search and ordering fields if None:
            self.populate_search_and_ordering_fields()

        queryset = self.filter_queryset(self.get_queryset())
        if self.filter_list_by_callback:
            filter_kwargs = (
                self.filter_list_by_callback(queryset, self.kwargs)
                if utils.count_required_positional_args(self.filter_list_by_callback)
                == 2
                else self.filter_list_by_callback(queryset)
            )
            if filter_kwargs:
                if "or_kwargs" in filter_kwargs:
                    or_kwargs = filter_kwargs.pop("or_kwargs")
                    queryset = queryset.filter(
                        Q(**or_kwargs, _connector=Q.OR), **filter_kwargs
                    )
                else:
                    queryset = queryset.filter(**filter_kwargs)

        if self.exclude_list_by_callback:
            exclude_kwargs = self.exclude_list_by_callback(queryset)
            if exclude_kwargs:
                if "or_kwargs" in exclude_kwargs:
                    or_kwargs = exclude_kwargs.pop("or_kwargs")
                    queryset = queryset.exclude(
                        Q(**or_kwargs, _connector=Q.OR), **exclude_kwargs
                    )
                else:
                    queryset = queryset.exclude(**exclude_kwargs)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_context(self):
        """Add normalized request data to context"""
        context = super().get_serializer_context()
        context["normalized_raw_data"] = utils.normalize_request_data(self.request)
        return context

    def populate_select_and_prefetch_related(self):
        should_populate_select_related = self.select_related == None
        if should_populate_select_related:
            self.select_related = []

        should_populate_prefetch_related = self.prefetch_related == None
        if should_populate_prefetch_related:
            self.prefetch_related = []

        already_populated_fields = []
        self.populate_select_and_prefetch_related_from_serializer_fields(
            self.serializer_class().fields,
            self.model,
            should_populate_select_related,
            should_populate_prefetch_related,
            [],
            [],
        )

    def populate_select_and_prefetch_related_from_serializer_fields(
        self,
        serializer_fields,
        root_model,
        should_populate_select_related,
        should_populate_prefetch_related,
        parent_prefixes,
        parent_fields,
    ):
        for serializer_field_key, serializer_field in serializer_fields.items():
            prefixes = parent_prefixes.copy()
            fields = parent_fields.copy()
            field_names = serializer_field.source.split(".")
            new_parent_prefixes = parent_prefixes.copy()
            new_parent_fields = parent_fields.copy()
            for idx, field_name in enumerate(field_names):
                field = None
                meta = (
                    root_model._meta
                    if idx == 0
                    else fields[idx - 1].related_model._meta
                )
                try:
                    field = meta.get_field(field_name)
                except:
                    continue

                related_model = getattr(field, "related_model", None)
                if related_model:
                    field_class_name = field.__class__.__name__
                    field_name_with_prefixes = (
                        field_name
                        if len(prefixes) == 0
                        else f"{'__'.join(prefixes)}__{field_name}"
                    )
                    if (
                        should_populate_select_related
                        and field_class_name in ["OneToOneField", "ForeignKey"]
                        and field_name_with_prefixes not in self.select_related
                    ):
                        self.select_related.append(field_name_with_prefixes)

                    if (
                        should_populate_prefetch_related
                        and field_class_name in ["ManyToManyField", "ManyToOneField"]
                        and field_name_with_prefixes not in self.prefetch_related
                    ):
                        self.prefetch_related.append(field_name_with_prefixes)

                    new_parent_prefixes.append(field_name)
                    new_parent_fields.append(field)

                    if "Serializer" in serializer_field.__class__.__name__:
                        new_serializer_fields = getattr(
                            serializer_field, "fields", None
                        )
                        if new_serializer_fields:
                            self.populate_select_and_prefetch_related_from_serializer_fields(
                                serializer_field.fields,
                                field.related_model,
                                should_populate_select_related,
                                should_populate_prefetch_related,
                                new_parent_prefixes.copy(),
                                new_parent_fields.copy(),
                            )

                fields.append(field)
                prefixes.append(field_name)

    def populate_search_and_ordering_fields(self):
        if self.serializer_class and (
            not self.search_fields or not self.ordering_fields
        ):
            serializer_fields = self.serializer_class().fields
            target_fields = utils.serializer_to_model_fields(
                self, list(serializer_fields.keys())
            )

            if not self.search_fields:
                self.search_fields = target_fields
            if not self.ordering_fields:
                self.ordering_fields = target_fields


class GenericRelatedModelViewSet(DRFReactBySchemaBaseModelViewSet):
    related_name = None
    parent_model = None
    pagination_class = (
        None
        if "PAGINATION_MODE_NESTED_VIEWSETS"
        not in settings.get("DRF_REACT_BY_SCHEMA", {})
        or settings["DRF_REACT_BY_SCHEMA"]["PAGINATION_MODE_NESTED_VIEWSETS"]
        != "server"
        else DRFReactBySchemaPagination
    )

    def perform_create(self, serializer, *args, **kwargs):
        parent_object = self.parent_model.objects.get(
            pk=self.kwargs[self.parent_pk_field]
        )
        related_objects = getattr(parent_object, self.related_name)

        # Is it an existing object being added?
        id_to_add = serializer.context["request"].data.pop("id_to_add", None)

        # If not:
        if not id_to_add:
            # Check if there are required fields that the serializer didn't validate because they are foreign keys with read_only=True in the serializer. If this is the case, retrieve the value stored in raw request_data and add it to validated_data:
            fields = self.model._meta.get_fields()
            for field in fields:
                is_required = not getattr(field, "blank", False)
                if is_required:
                    field_name = getattr(field, "name")
                    validated = serializer.validated_data.get(field_name, None)
                    request = serializer.context["request"].data.get(field_name, None)
                    if validated == None and request is not None:
                        # If the data is a dict, it means that it is a foreign key that must be created first:
                        if type(request) is dict and "label" in request:
                            # TODO: treat error for when it doesn't have a related_model
                            related_model = field.related_model
                            related_model_fields = (
                                field.related_model._meta.get_fields()
                            )
                            created_instance = None
                            for related_field in related_model_fields:
                                related_field_name = getattr(related_field, "name")

                                if (
                                    related_field.related_model
                                    or related_field_name == "id"
                                    or getattr(related_field, "blank", False)
                                ):
                                    continue

                                data = {related_field_name: request["label"]}
                                (created_instance, created) = (
                                    related_model.objects.get_or_create(**data)
                                )
                                break

                            if created_instance:
                                request = created_instance.id

                        serializer.validated_data[f"{field_name}_id"] = request

            try:
                instance = serializer.save()
            except:
                # There will be an error if the relation is not a direct ManyToMany
                # but through an explicit third party, for example
                # ProjetoOrganizacaoBeneficiaria, or through OneToMany (foreignKey)
                serializer.validated_data[self.parent_related_name] = parent_object
                instance = serializer.save()

            related_objects.add(instance)
        else:
            related_objects.add(id_to_add)

    def destroy(self, request, *args, **kwargs):
        parent_object = self.parent_model.objects.get(
            pk=self.kwargs[self.parent_pk_field]
        )
        related_objects = getattr(parent_object, self.related_name)

        if self.many and not self.reverse_many:
            related_objects.filter(pk=self.kwargs["pk"]).delete()
            return Response("success")

        object = self.model.objects.get(pk=self.kwargs["pk"])
        related_objects.remove(object)
        return Response("success")


class GenericAutocompleteViewSet(DRFReactBySchemaBaseModelViewSet):
    is_autocomplete = True


class GenericViewSet(DRFReactBySchemaBaseModelViewSet):
    serializer_list_class = None
    pagination_class = (
        None
        if "PAGINATION_MODE" not in settings.get("DRF_REACT_BY_SCHEMA", {})
        or settings["DRF_REACT_BY_SCHEMA"]["PAGINATION_MODE"] != "server"
        else DRFReactBySchemaPagination
    )

    def retrieve(self, request, pk=None):
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    def perform_create(self, serializer, *args, **kwargs):
        # Check if there are required fields that the serializer didn't validate because they are foreign keys with read_only=True in the serializer. If this is the case, retrieve the value stored in raw request_data and add it to validated_data:
        fields = self.model._meta.get_fields()
        for field in fields:
            is_required = not getattr(field, "blank", False)
            if is_required:
                field_name = getattr(field, "name")
                validated = serializer.validated_data.get(field_name, None)
                request = serializer.context["request"].data.get(field_name, None)
                if validated == None and request is not None:
                    # If the data is a dict, it means that it is a foreign key that must be created first:
                    if type(request) is dict and "label" in request:
                        # TODO: treat error for when it doesn't have a related_model
                        related_model = field.related_model
                        related_model_fields = field.related_model._meta.get_fields()
                        created_instance = None
                        for related_field in related_model_fields:
                            related_field_name = getattr(related_field, "name")

                            if (
                                related_field.related_model
                                or related_field_name == "id"
                                or getattr(related_field, "blank", False)
                            ):
                                continue

                            data = {related_field_name: request["label"]}
                            (created_instance, created) = (
                                related_model.objects.get_or_create(**data)
                            )
                            break

                        if created_instance:
                            request = created_instance.id

                    if not type(request) is dict:
                        serializer.validated_data[f"{field_name}_id"] = request

        instance = serializer.save()


##########################
__nested_viewsets__ = []

for app in settings["APPS"]:
    for name, model in apps.all_models[app].items():
        model_name = model.__name__
        if isinstance(model, type):
            viewset_name = f"{model_name}ViewSet"
            if not viewset_name in dir():
                generated_class = type(
                    viewset_name,
                    (GenericViewSet,),
                    {
                        "model_name": model_name,
                        "app": app,
                        "serializer_class": getattr(
                            serializers, f"{model_name}Serializer"
                        ),
                        "serializer_list_class": getattr(
                            serializers, f"{model_name}ListSerializer"
                        ),
                    },
                )
                globals()[viewset_name] = generated_class
                # Generate nested viewsets:
                for field in model._meta.get_fields():
                    if field.__class__.__name__ == "ManyToOneRel":
                        related_model_name = field.related_model.__name__
                        if getattr(
                            serializers, f"{related_model_name}Serializer", None
                        ):
                            related_name = f"{model_name}Related{related_model_name}"
                            related_viewset_name = f"{related_name}ViewSet"
                            parent_related_name = field.remote_field.name
                            # TODO: Think of a better way to deal with multiple references to same foreignKey model in the same model
                            if related_viewset_name in globals():
                                related_viewset_name = f"{related_name}{utils.to_pascal_case(parent_related_name)}ViewSet"
                            target_field_name = (
                                "pk"
                                if field.target_field.name == "id"
                                else field.target_field.name
                            )
                            generated_nested_class = type(
                                related_viewset_name,
                                (GenericRelatedModelViewSet,),
                                {
                                    "model": field.related_model,
                                    "app": app,
                                    "serializer_class": getattr(
                                        serializers, f"{related_model_name}Serializer"
                                    ),
                                    "related_name": field.name,
                                    "many": True,
                                    "parent_model": model,
                                    "parent_pk_field": f"{parent_related_name}_{target_field_name}",
                                    "parent_related_name": parent_related_name,
                                },
                            )
                            globals()[related_viewset_name] = generated_nested_class
                            __nested_viewsets__.append(
                                (utils.camel_to_snake(model_name), related_viewset_name)
                            )


class EndpointsViewSet(viewsets.ViewSet):
    def list(self, request):
        endpoints = []
        for app in settings["APPS"]:
            for name, model in apps.all_models[app].items():
                endpoint = {
                    "model_name": utils.camel_to_snake(model.__name__),
                    "verbose_name": model._meta.verbose_name,
                    "verbose_name_plural": model._meta.verbose_name_plural,
                }
                endpoints.append(endpoint)
        endpoints.sort(key=operator.itemgetter("verbose_name_plural"))
        return Response(endpoints)
