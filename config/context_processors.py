from django.conf import settings


def branding(request):
    return {
        'BRAND_NAME': settings.BRAND_NAME,
        'BASE_DOMAIN': settings.BASE_DOMAIN,
        'APP_URL': settings.APP_URL,
    }
