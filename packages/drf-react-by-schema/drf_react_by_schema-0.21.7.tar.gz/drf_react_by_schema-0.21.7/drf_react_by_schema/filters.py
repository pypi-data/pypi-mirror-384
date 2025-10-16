from rest_framework.filters import OrderingFilter, SearchFilter
from . import utils


class DRFReactBySchemaOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        """
        Ordering is set by a comma delimited ?ordering=... query parameter.

        The `ordering` query parameter can be overridden by setting
        the `ordering_param` value on the OrderingFilter or by
        specifying an `ORDERING_PARAM` value in the API settings.
        """
        params = request.query_params.get(self.ordering_param)
        if params:
            fields_raw = [param.strip() for param in params.split(",")]
            fields = utils.serializer_to_model_fields(view, fields_raw)
            if fields is not None:
                ordering = self.remove_invalid_fields(queryset, fields, view, request)
                if ordering:
                    return ordering

        # No ordering was included, or all the ordering fields were invalid
        return self.get_default_ordering(view)
