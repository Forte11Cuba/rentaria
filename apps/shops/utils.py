from django.http import Http404

from .models import Shop, ShopSlugAlias


class ShopSlugChanged(Exception):
    def __init__(self, old_slug, new_slug):
        self.old_slug = old_slug
        self.new_slug = new_slug
        super().__init__(f'{old_slug} → {new_slug}')


def get_shop_or_redirect(slug, **filters):
    try:
        return Shop.objects.get(slug=slug, **filters)
    except Shop.DoesNotExist:
        pass
    alias = ShopSlugAlias.objects.select_related('shop').filter(old_slug=slug).first()
    if alias and Shop.objects.filter(pk=alias.shop_id, **filters).exists():
        raise ShopSlugChanged(slug, alias.shop.slug)
    raise Http404('Shop not found')
