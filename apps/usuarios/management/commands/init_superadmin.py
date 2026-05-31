import os
from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Crea el superadmin inicial si no existe'

    def handle(self, *args, **options):
        email = os.environ.get('SUPERADMIN_EMAIL')
        password = os.environ.get('SUPERADMIN_PASSWORD')
        if not email or not password:
            self.stdout.write(self.style.WARNING('SUPERADMIN_EMAIL o SUPERADMIN_PASSWORD no definidos'))
            return
        if Usuario.objects.filter(rol='superadmin').exists():
            self.stdout.write('Superadmin ya existe, nada que hacer.')
            return
        user = Usuario.objects.create_superuser(
            username=email.split('@')[0],
            email=email,
            password=password,
            rol='superadmin',
            estado='activo',
        )
        self.stdout.write(self.style.SUCCESS(f'Superadmin creado: {user.email}'))
