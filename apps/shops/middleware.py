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
        segments = request.path.split('/')
        for i, seg in enumerate(segments):
            if seg == exception.old_slug:
                segments[i] = exception.new_slug
                break
        else:
            return None
        new_path = '/'.join(segments)
        qs = request.META.get('QUERY_STRING', '')
        if qs:
            new_path = f'{new_path}?{qs}'
        return HttpResponsePermanentRedirect(new_path, preserve_request=True)
