from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.core.paginator import InvalidPage
from collections import OrderedDict
from django.db.models import Sum
from . import settings


class DRFReactBySchemaPagination(PageNumberPagination):
    page_size = (
        100
        if "PAGINATION_PER_PAGE" not in settings.get("DRF_REACT_BY_SCHEMA", {})
        else settings["DRF_REACT_BY_SCHEMA"]["PAGINATION_PER_PAGE"]
    )
    queryset = None
    # max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        self.queryset = queryset

        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        sum_rows = self.request.query_params.get("sum_rows", None)
        if sum_rows:
            fields = sum_rows.split(",")
            ret = {}
            for field in fields:
                ret[f"{field}_total"] = Sum(field)
            sum_rows = self.queryset.aggregate(**ret)
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("sum_rows", sum_rows),
                    ("results", data),
                ]
            )
        )
