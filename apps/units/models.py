from django.db import models


class UnitModel(models.Model):
    tienda = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='modelos')
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='motos/', blank=True)
    caracteristicas = models.JSONField(default=list, blank=True)
    min_dias_alquiler = models.PositiveIntegerField(default=1)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Unit Model'
        verbose_name_plural = 'Unit Models'
        ordering = ['marca', 'modelo']

    def __str__(self):
        return f"{self.marca} {self.modelo}"

    def unidades_activas(self):
        return self.motos.filter(activa=True).count()

    def unidades_totales(self):
        return self.motos.count()

    def plan_para_dias(self, dias):
        for plan in self.planes.order_by('dias_min'):
            if dias >= plan.dias_min and (plan.dias_max is None or dias <= plan.dias_max):
                return plan
        return self.planes.order_by('dias_min').last()


class PricePlan(models.Model):
    modelo = models.ForeignKey(UnitModel, on_delete=models.CASCADE, related_name='planes')
    dias_min = models.PositiveIntegerField(default=1)
    dias_max = models.PositiveIntegerField(null=True, blank=True)
    precio_dia = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ['dias_min']
        verbose_name = 'Price Plan'
        verbose_name_plural = 'Price Plans'

    def __str__(self):
        if self.dias_max:
            return f"{self.dias_min}–{self.dias_max} días: ${self.precio_dia}/día"
        return f"{self.dias_min}+ días: ${self.precio_dia}/día"


class UnitCharge(models.Model):
    modelo = models.ForeignKey(UnitModel, on_delete=models.CASCADE, related_name='cargos')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    costo = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = 'Unit Charge'
        verbose_name_plural = 'Unit Charges'
        ordering = ['id']

    def __str__(self):
        return f"{self.nombre} (${self.costo})"


class UnitPhoto(models.Model):
    modelo = models.ForeignKey(UnitModel, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='motos/galeria/')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'Unit Photo'
        verbose_name_plural = 'Unit Photos'


class Unit(models.Model):
    chapa = models.CharField(max_length=20, primary_key=True)
    tienda = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='motos')
    modelo = models.ForeignKey(UnitModel, on_delete=models.PROTECT, related_name='motos')
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Unit'
        verbose_name_plural = 'Units'

    def __str__(self):
        return self.chapa
