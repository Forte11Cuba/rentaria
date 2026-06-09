from django.http import HttpResponsePermanentRedirect

from .utils import ShopSlugChanged


class ShopSlugAliasMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, ShopSlugChanged):
            return None
        old_segment = f'/{exception.old_slug}'
        new_segment = f'/{exception.new_slug}'
        new_path = request.path.replace(old_segment, new_segment, 1)
        qs = request.META.get('QUERY_STRING', '')
        if qs:
            new_path = f'{new_path}?{qs}'
        return HttpResponsePermanentRedirect(new_path)
