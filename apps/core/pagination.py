from rest_framework.pagination import CursorPagination as BaseCursorPagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class CursorPagination(BaseCursorPagination):
    """
    Custom cursor-based pagination for better performance
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('count', self.page.paginator.count if hasattr(self.page, 'paginator') else None),
            ('results', data)
        ]))
class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.page_size),
            ('results', data)
        ]))

class LargePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

class SmallPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50