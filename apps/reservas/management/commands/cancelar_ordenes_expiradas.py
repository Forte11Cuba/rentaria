from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.reservas.models import Orden


class Command(BaseCommand):
    help = 'Cancela órdenes Bitcoin pendientes con más de 35 minutos sin pago'

    def handle(self, *args, **options):
        limite = timezone.now() - timedelta(minutes=35)
        qs = Orden.objects.filter(
            estado='pendiente',
            metodo_pago='bitcoin_btcpay',
            created_at__lt=limite,
        )
        count = qs.update(estado='cancelada')
        self.stdout.write(
            self.style.SUCCESS(f'Canceladas {count} orden(es) Bitcoin expirada(s).')
        )
